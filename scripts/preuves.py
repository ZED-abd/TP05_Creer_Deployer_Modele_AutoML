"""Contrôles complémentaires, sans modifier les listings pédagogiques."""
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

PREUVES = Path('reports/preuves')
PREUVES.mkdir(parents=True, exist_ok=True)

def ecrire(nom, valeur):
    texte = valeur if isinstance(valeur, str) else json.dumps(valeur, indent=2, ensure_ascii=False, default=str)
    (PREUVES / nom).write_text(texte + '\n', encoding='utf-8')
    return texte

def machine():
    versions = {}
    for package in ('flaml','mlflow','scikit-learn','lightgbm','xgboost','numpy','pandas','skops','cloudpickle','requests'):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = 'non installé'
    ps = "[PSCustomObject]@{CPU=(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name);RAM_octets=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory} | ConvertTo-Json -Compress"
    materiel = json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',ps], text=True))
    contenu = {'date':'2026-11-05', 'OS':platform.platform(), 'Python':platform.python_version(),
               'processeurs_logiques':os.cpu_count(), **materiel, 'versions':versions,
               'contexte':'Windows du poste, exécution par Codex dans un environnement à permissions restreintes ; aucun calcul cloud. Relancer sur le poste avant rendu pour confirmer les latences.'}
    print(ecrire('machine.txt', contenu))
    ecrire('versions_figees.txt', subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
    import pandas as pd
    df = pd.read_csv('data/transactions.csv')
    assert len(df) == 5000 and int(df.fraude.sum()) == 568
    assert len(Path('data/transactions.csv').read_text().splitlines()) == 5001
    ecrire('validation_donnees.json', {'transactions':len(df),'fraudes':int(df.fraude.sum()),
           'lignes_avec_entete':5001,'sha256':hashlib.sha256(Path('data/transactions.csv').read_bytes()).hexdigest()})

def inspecter(nom):
    import mlflow
    import yaml
    mlflow.set_tracking_uri('http://127.0.0.1:5000')
    client = mlflow.MlflowClient()
    v = max(client.search_model_versions(f"name='{nom}'"), key=lambda v:int(v.version))
    run = client.get_run(v.run_id)
    resultat = {'nom':nom,'version':v.version,'run_id':v.run_id,'run_name':run.info.run_name,
                'params':run.data.params,'metrics':run.data.metrics}
    for fichier in ('MLmodel','requirements.txt'):
        chemin = mlflow.artifacts.download_artifacts(artifact_uri=f'models:/{nom}/{v.version}',dst_path='rendu/inspection')
        contenu = (Path(chemin)/fichier).read_text(encoding='utf-8')
        ecrire(f'{nom}_{fichier}',contenu)
        if fichier == 'MLmodel':
            flavors = yaml.safe_load(contenu)['flavors']
            assert 'sklearn' in flavors and 'python_function' in flavors
            resultat['flavors'] = flavors
        else:
            famille = run.data.params.get('famille','')
            attendu = {'lgbm':'lightgbm','xgboost':'xgboost','rf':'scikit-learn','extra_tree':'scikit-learn'}.get(famille,'scikit-learn')
            assert attendu in contenu, f'Dépendance absente : {attendu}'
            resultat['dependance_verifiee'] = attendu
    print(ecrire(f'{nom}_registre.json',resultat))
    if nom == 'fraude-automl' and run.data.params.get('outil') == 'flaml':
        log = lire('automl.txt')
        scores = re.findall(r'F1 \([^\n]+?:\s*([0-9.]+)',log)
        assert len(scores) == 2 and scores[0] == scores[1], scores

def lire(nom):
    raw = (PREUVES/nom).read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace')

def invalide():
    import requests
    resultat = {}
    for port in (8100,8101):
        r = requests.post(f'http://127.0.0.1:{port}/invocations',json={'dataframe_records':[{'montant':8500}]},timeout=10)
        resultat[port] = {'statut':r.status_code,'reponse':r.json()}
        assert r.status_code == 400
        assert all(nom in r.text for nom in ('anciennete','freq_24h','nuit'))
    print(ecrire('requetes_invalides.json',resultat))

def comparer():
    import joblib
    import pandas as pd
    from sklearn.metrics import confusion_matrix, f1_score
    from sklearn.model_selection import train_test_split
    df = pd.read_csv('data/transactions.csv')
    _, Xte, _, yte = train_test_split(df.drop(columns='fraude'),df.fraude,test_size=0.25,random_state=42)
    resultat = {}
    for nom in ('manuel','automl'):
        fichier = Path(f'models/model_{nom}.pkl')
        modele = joblib.load(fichier)
        clf = modele.named_steps['clf'] if hasattr(modele,'named_steps') else modele
        registre = json.loads(lire(f'fraude-{nom}_registre.json'))
        importance = getattr(clf,'feature_importances_',None)
        detail = {'classe':type(clf).__name__, 'f1':f1_score(yte,modele.predict(Xte)),
                  'matrice_confusion':confusion_matrix(yte,modele.predict(Xte)).tolist(),
                  'taille_octets':fichier.stat().st_size,'taille_Mo':fichier.stat().st_size/1024**2,
                  'parametres_modele':clf.get_params(), 'registre':registre,
                  'importances':sorted(zip(Xte.columns,importance.tolist()),key=lambda p:-p[1]) if importance is not None else 'non disponible',
                  'nombre_arbres':getattr(clf,'n_estimators_',getattr(clf,'n_estimators',None)),
                  'profondeur_parametree':clf.get_params().get('max_depth')}
        if hasattr(clf,'estimators_') and type(clf).__name__ in ('RandomForestClassifier','ExtraTreesClassifier'):
            detail['profondeurs_reelles'] = {'min':min(t.tree_.max_depth for t in clf.estimators_), 'max':max(t.tree_.max_depth for t in clf.estimators_)}
        if hasattr(clf,'booster_'):
            arbres = clf.booster_.dump_model()['tree_info']
            def profondeur(node):
                return 0 if 'leaf_index' in node else 1+max(profondeur(node['left_child']),profondeur(node['right_child']))
            profondeurs = [profondeur(t['tree_structure']) for t in arbres]
            detail['profondeurs_reelles'] = {'min':min(profondeurs),'max':max(profondeurs)}
        detail['latences'] = []
        for p in sorted(PREUVES.glob('client_*.txt')):
            texte = lire(p.name)
            port = '8100' if nom == 'automl' else '8101'
            m = re.search(rf'port {port} \| mediane : ([0-9.]+) ms \| p95 : ([0-9.]+)',texte)
            if m:
                assert "reponse : 200" in texte
                detail['latences'].append({'mediane_ms':float(m[1]),'p95_ms':float(m[2]),'preuve':p.name})
        assert len(detail['latences']) == 2
        resultat[nom] = detail
    print(ecrire('comparaison.json',resultat))
    manuel,auto = resultat['manuel'],resultat['automl']
    def lat(d,k): return ' / '.join(str(l[k]) for l in d['latences'])
    def imp(d): return '; '.join(f'{n}={v:.4f}' for n,v in d['importances']) if isinstance(d['importances'],list) else d['importances']
    lignes = [
      ('Famille de modele','foret aleatoire',auto['registre']['params']['famille']),
      ('F1 sur le jeu de test',f"{manuel['f1']:.4f}",f"{auto['f1']:.4f}"),
      ('Temps de recherche machine',str(manuel['registre']['metrics']['duree_entrainement_s'])+' s (entraînement)',str(auto['registre']['metrics']['duree_recherche_s'])+' s'),
      ('Temps humain (estimation)','[À REMPLIR PAR L’ÉTUDIANT]','[À REMPLIR PAR L’ÉTUDIANT]'),
      ('Latence mediane (ms)',lat(manuel,'mediane_ms'),lat(auto,'mediane_ms')),
      ('Latence p95 (ms)',lat(manuel,'p95_ms'),lat(auto,'p95_ms')),
      ('Taille du fichier (Mo)',f"{manuel['taille_Mo']:.4f}",f"{auto['taille_Mo']:.4f}"),
      ('Explicabilite',imp(manuel),imp(auto))]
    texte = '# Modele manuel ou modele AutoML ? (TP05)\n\n| Critere | Manuel (rf 500/16) | AutoML (FLAML 90 s) |\n|---|---|---|\n'
    texte += '\n'.join('| '+' | '.join(l)+' |' for l in lignes)
    texte += '\n\nMesures 1 / 2, sans moyenne des p95. Mo = 1 048 576 octets (convention PowerShell 1MB). '
    texte += 'Temps humain : suggestion de saisie 30 à 90 minutes pour le réglage manuel et 10 à 30 minutes pour AutoML ; estimations indicatives, aucune durée personnelle mesurée.\n'
    for nom,d in resultat.items():
        texte += f"\n{nom} : matrice de confusion [lignes réelles 0/1, colonnes prédites 0/1] {d['matrice_confusion']}, {d['nombre_arbres']} arbres, profondeur paramétrée {d['profondeur_parametree']}, profondeurs observées {d.get('profondeurs_reelles','non disponible')}.\n"
    texte += '\nConfiguration gagnante : ' + json.dumps({k:v for k,v in auto['registre']['params'].items() if k.startswith('cfg_')},ensure_ascii=False) + '\n'
    texte += '\nLes importances ne sont pas sur la même échelle : forêt = baisse normalisée d’impureté ; LightGBM = nombre de divisions (importance_type=split). Elles sont descriptives, sans comparaison directe de leurs amplitudes. La profondeur LightGBM -1 signifie absence de borne explicite ; les 4 feuilles bornent ici les arbres observés à 2–3 niveaux.\n'
    choix = 'manuel' if manuel['f1'] >= auto['f1'] else 'AutoML'
    texte += '\n## Decision (5 lignes) : quel modele mettre en production, et pourquoi ?\n\n'
    texte += f"Nous retenons le modèle {choix} pour ce prototype de fraude, en donnant priorité à la qualité ; aucun objectif maximal de latence métier n’a été fourni.\n"
    texte += f"Le manuel atteint F1 {manuel['f1']:.4f} contre {auto['f1']:.4f} ; ses faux négatifs sont {manuel['matrice_confusion'][1][0]} contre {auto['matrice_confusion'][1][0]} pour AutoML, sur le même test.\n"
    texte += f"Le compromis de service reste explicite : p95 manuel {lat(manuel,'p95_ms')} ms contre {lat(auto,'p95_ms')} ms pour AutoML, sans mesure de charge concurrente.\n"
    texte += f"Le fichier manuel pèse {manuel['taille_Mo']:.4f} Mo contre {auto['taille_Mo']:.4f} Mo ; ses 500 arbres de profondeur maximale 16 restent inspectables, tout comme les {auto['nombre_arbres']} arbres du gagnant AutoML.\n"
    texte += f"La recette manuelle fixe les réglages scikit-learn ; le budget FLAML peut changer le gagnant et impose ici {auto['registre']['dependance_verifiee']} en production ; conserver les deux versions et réévaluer le choix si le besoin privilégie la latence ou la mémoire.\n"
    for port in (8100,8101):
        journal = lire(f'service_{port}.stdout.log')
        succes = len(re.findall(r'POST /invocations HTTP/1.1\" 200 OK',journal))
        erreurs = len(re.findall(r'POST /invocations HTTP/1.1\" 400 Bad Request',journal))
        assert succes == 422, (port,succes)
        assert erreurs == 1, (port,erreurs)
        ecrire(f'validation_http_{port}.json',{'port':port,'appels_valides_HTTP_200':succes,'appels_invalides_HTTP_400':erreurs,'detail':'2 × (1 affichage + 10 échauffements + 200 mesures)'})
    Path('reports/tp5_comparaison.md').write_text(texte,encoding='utf-8')

def anonymiser():
    racine = str(Path.cwd())
    utilisateur = str(Path.home())
    for p in Path('reports').rglob('*'):
        if not p.is_file(): continue
        texte = lire(str(p.relative_to(PREUVES))) if p.is_relative_to(PREUVES) else p.read_text(encoding='utf-8-sig')
        for chemin,label in ((racine,'[PROJET]'),(utilisateur,'[PROFIL]')):
            for forme in (chemin,chemin.replace('\\','/'),chemin.replace('\\','\\\\')):
                texte = re.sub(re.escape(forme),lambda _:label,texte,flags=re.IGNORECASE)
        texte = re.sub(r'(?i)([a-z]:[\\/]+Users[\\/]+)[^\\/\s\"\']+',r'\1[UTILISATEUR]',texte)
        # Stabiliser les fins de ligne Windows lors de plusieurs anonymisations.
        texte = texte.replace('\r','').replace('\x00','')
        p.write_text(texte.rstrip()+'\n',encoding='utf-8',newline='\n')

if __name__ == '__main__':
    action = sys.argv[1]
    if action == 'machine': machine()
    elif action == 'inspecter': inspecter(sys.argv[2])
    elif action == 'invalide': invalide()
    elif action == 'comparer': comparer()
    elif action == 'anonymiser': anonymiser()
    else: raise ValueError(action)
