"""Rapport personnel hors Git ; exécuter avec Python et python-docx (runtime documentaire)."""
import json
from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

P = Path('reports/preuves')
C = json.loads((P/'comparaison.json').read_text(encoding='utf-8'))
M, A = C['manuel'], C['automl']
machine = json.loads((P/'machine.txt').read_text(encoding='utf-8'))
comparaison = Path('reports/tp5_comparaison.md').read_text(encoding='utf-8')
decision = comparaison.split('## Decision',1)[1].split('\n\n',1)[1].strip()
def valeurs(d, cle):
    return ' et '.join(f"{v[cle]:.1f}" for v in d['latences'])
famille = A['registre']['params']['famille']
dependance = A['registre']['dependance_verifiee']
questions = [
('Question 1 Le choix de production', f"""Nous proposons fraude-manuel pour ce prototype : son F1 de {M['f1']:.4f} dépasse celui du modèle AutoML {famille}, {A['f1']:.4f}. Sur le même test, il manque vingt fraudes contre vingt-trois et produit quinze fausses alertes contre dix-neuf. Aucun objectif maximal de latence métier n'a été fourni ; nous donnons donc priorité à cette qualité, sans ignorer le coût de service. Les p95 manuels sont {valeurs(M,'p95_ms')} ms, contre {valeurs(A,'p95_ms')} ms pour AutoML. Les fichiers pèsent respectivement {M['taille_Mo']:.4f} et {A['taille_Mo']:.4f} Mo : AutoML convient mieux à une contrainte de mémoire ou de réponse rapide. La forêt fournit des importances globales et une recette fixe de réentraînement. Le gagnant FLAML impose ici {dependance} en production et son budget temporel peut sélectionner une autre famille malgré la graine. Nous conserverions les versions, leurs dépendances et un retour arrière par alias. Ce choix reste à confirmer par des tests de charge, la maintenabilité et une validation métier du coût des erreurs ; les importances seules ne justifient pas chaque transaction."""),
('Question 2 Le coût du point de terminaison cloud', """La page officielle de tarification Vertex AI a été consultée le 5 novembre 2026. Elle redirige vers la tarification Gemini platform et renvoie, pour l'inférence AutoML tabulaire, aux machines des modèles personnalisés. Nous retenons une seule réplique n1-standard-2 dans Iowa, us-central1, sans GPU, au tarif à la demande de 0.1095 USD par heure affiché dans la section Prediction and explanation. La documentation de configuration liste ce type avec deux vCPU et 7.5 Go de mémoire. Pour trente jours d'activité continue, le calcul est 0.1095 × 24 × 30 = 78.84 USD. Avec la convention de 730 heures, le résultat devient 79.935 USD, soit 79.94 USD arrondis. Le déploiement reste facturé en l'absence de requêtes. L'estimation exclut entraînement, stockage, trafic, taxes et remises contractuelles ; elle ne prédit pas la capacité de traitement. Nous n'avons créé aucun compte, modèle, bucket ni point de terminaison cloud : ce montant est un calcul documentaire, aucune dépense n'a été mesurée."""),
('Question 3 La latence locale et la latence cloud', f"""Nos appels locaux passent par 127.0.0.1 et incluent le client Python, la sérialisation JSON, le serveur HTTP et l'inférence. Les médianes AutoML sont {valeurs(A,'mediane_ms')} ms et ses p95 {valeurs(A,'p95_ms')} ms. La référence manuelle présente des médianes de {valeurs(M,'mediane_ms')} ms et des p95 de {valeurs(M,'p95_ms')} ms. Chaque série comprend dix appels d'échauffement puis deux cents appels chronométrés. Le premier appel affiché est également exclu des mesures. Nous n'avons effectué aucune mesure cloud et ne pouvons donc calculer ni surcoût réseau réel ni rapport de vitesse cloud/local. Un service distant ajoute généralement un aller-retour Internet, la négociation TLS lorsque la connexion est nouvelle, l'authentification et le passage par un répartiteur de charge. La sérialisation peut aussi être plus complexe. Des files d'attente, une machine partagée ou un démarrage à froid éventuel augmentent particulièrement la queue de distribution. À l'inverse, une machine distante plus puissante peut réduire le calcul. Nos résultats caractérisent une requête séquentielle à chaud et ne permettent pas d'estimer un débit concurrent."""),
('Question 4 Le moteur AutoML change de version', f"""La graine 42 ne garantit pas à elle seule une reconstruction identique. Dans notre expérience, FLAML dispose d'un budget de quatre-vingt-dix secondes : la vitesse du poste et l'ordonnancement influencent les essais terminés. Une nouvelle version peut changer les familles candidates, les paramètres par défaut, la recherche, le prétraitement ou le comportement numérique. Chez un fournisseur, une mise à jour du moteur peut donc modifier les prédictions et les métriques après réentraînement sans modification de notre propre code. Ce risque concerne une régression silencieuse, une rupture de compatibilité et une dépendance au calendrier du fournisseur ; un artefact déjà figé n'est pas nécessairement réentraîné automatiquement. Nous conserverions notre jeu de référence, le F1 mesuré de {A['f1']:.4f}, les matrices de confusion, les dépendances et l'artefact exact. Des tests de régression compareraient qualité, schéma et latence avant promotion. Le registre avec alias production permet un retour vers une version validée. Enfin, un déploiement progressif, la surveillance des distributions et des erreurs, et le gel des versions lorsque possible limiteraient l'exposition."""),
('Question 5 Garantir la réversibilité', f"""La réversibilité commence par la conservation des données, du schéma et du code de préparation, indépendamment du fournisseur. Notre script donnees.py permet de régénérer le jeu synthétique et son empreinte est conservée ; fraude-manuel fournit une référence de remplacement avec un F1 de {M['f1']:.4f}. Nous archiverions également le découpage, les métriques, les matrices de confusion, les versions des bibliothèques et la procédure de service. La documentation officielle consultée le 5 novembre 2026 autorise l'export des modèles AutoML tabulaires de classification et de régression, avec un format tf-saved-model et un serveur Docker documenté. Ce n'est pas une promesse universelle : la prévision n'est pas exportable par cette procédure, le CPU doit supporter x86 et AVX, et Explainable AI n'accompagne pas l'export. Il faut donc vérifier le format ouvert disponible et tester réellement le fonctionnement hors plateforme avant de s'engager. Un registre indépendant, des contrats d'entrée stables et des essais réguliers de restauration rendent cette sortie vérifiable. Nous avons seulement lu la documentation, aucun export cloud n'a été exécuté."""),
('Question 6 skops et cloudpickle', f"""Le gagnant AutoML appartient à la famille {famille}. Les estimateurs LightGBM ou XGBoost utilisés par FLAML, ainsi que certains pipelines, ne sont pas automatiquement pris en charge ou approuvés par skops. Il faut examiner les types reconnus et la liste de confiance plutôt que supposer qu'un modèle scikit-learn équivaut à tout objet exposant predict. Cloudpickle sérialise des objets Python plus généraux et facilite ici l'enregistrement du modèle extrait. Notre preuve MLmodel indique le format effectivement utilisé et les deux flavors de service ; requirements.txt vérifie la dépendance {dependance}. La référence RandomForest conserve le paramètre skops_trusted_types du listing pédagogique. Le risque du format pickle est l'exécution de code arbitraire lors du chargement d'un fichier malveillant. Dans ce TP, les modèles proviennent de nos scripts, restent dans un registre local et sont servis sur la boucle locale ; aucune source externe n'est chargée. Cela rend le risque acceptable dans ce périmètre, sans faire du pickle un format sûr. En production, il faudrait un registre contrôlé, des droits limités, des signatures ou empreintes vérifiées et un environnement isolé."""),
]
for titre,texte in questions:
    nombre = len(texte.split())
    assert 120 <= nombre <= 200, (titre,nombre)

captures = [
"[CAPTURE 1 À INSÉRER : le run automl-90s dans l'expérience tp5-automl-deploiement, paramètres famille et cfg_…, métrique f1, et le fichier MLmodel montrant serialization_format et les flavors python_function et sklearn. Vérifier fraude-automl version 1 pour la première campagne.]",
"[CAPTURE 2 À INSÉRER : les terminaux PowerShell 3 et 4 avec les services models:/fraude-automl@production et models:/fraude-manuel@production démarrés, messages d'écoute des ports 8100 et 8101 et commandes visibles.]",
"[CAPTURE 3 À INSÉRER : les sorties de src/client.py pour 8100 et 8101 avec réponses HTTP 200, médianes et p95, et la réponse HTTP 400 à la requête invalide citant anciennete, freq_24h et nuit manquantes.]"
]
sources = [
"Tarif consulté le 05/11/2026 : https://cloud.google.com/vertex-ai/pricing ; page servie https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing#prediction-and-explanation",
"Machines consultées le 05/11/2026 : https://cloud.google.com/vertex-ai/docs/predictions/configure-compute",
"Export consulté le 05/11/2026 : https://cloud.google.com/vertex-ai/docs/export/export-model-tabular",
]
introduction = f"""Ce TP compare deux modèles de détection de fraude jusqu'au service HTTP avec MLflow. Le plan A FLAML a été utilisé. Les mesures sont produites sur Windows par Codex dans un environnement à permissions restreintes, sans calcul cloud. Elles doivent être confirmées sur le poste avant le rendu. Nous retenons le modèle manuel pour sa qualité supérieure, sous réserve des validations métier et de charge. Les trois captures restent à réaliser par l'étudiant.

Identité : [NOM] [PRÉNOM] — [FILIÈRE] — [GROUPE]
Date de la campagne : 5 novembre 2026.
Machine : {machine['OS']}, {machine['CPU']}, {machine['RAM_octets']/1024**3:.2f} Go RAM, Python {machine['Python']}.
Versions : {', '.join(k+' '+v for k,v in machine['versions'].items())}.
Données : 5000 transactions, 568 fraudes, graine 7 ; séparation 75/25 avec random_state=42, sans stratification, conformément au listing. Le jeu de test comprend 1250 transactions.
"""
md = '# TP05 AutoML et déploiement de modèles\n\n' + introduction + '\n\n' + comparaison
for titre,texte in questions: md += '\n\n## '+titre+'\n\n'+texte
md += '\n\n## Sources documentaires\n\n'+'\n\n'.join(sources)
md += '\n\n## Captures réelles à insérer\n\n[À FAIRE PAR L’ÉTUDIANT]\n\n'+'\n\n'.join(captures)
md += '\n\n## Hypothèses et limites\n\nLe budget temporel FLAML est non déterministe entre machines. Aucune ressource du bloc G ni mesure cloud. Aucun correctif des listings pédagogiques n’a été nécessaire avec les bibliothèques installées. La taille est mesurée en unités binaires selon la convention PowerShell. Le nom du dépôt fourni diffère du nom mlops-tp5-automl exigé ; il a été conservé. Aucune capture ni durée humaine n’est inventée. Les erreurs HTTP sont validées pour les deux ports. Les modèles et données restent exclus de Git.\n'
Path('rendu/compte_rendu.md').write_text(md,encoding='utf-8')

doc = Document()
sec = doc.sections[0]
sec.page_width,sec.page_height = Inches(8.5),Inches(11)
sec.top_margin = sec.bottom_margin = Inches(.65)
sec.left_margin = sec.right_margin = Inches(.7)
normal = doc.styles['Normal']
normal.font.name='Calibri'; normal.font.size=Pt(11)
normal.paragraph_format.space_after=Pt(7)
normal.paragraph_format.line_spacing=1.08
for nom,taille in [('Title',24),('Heading 1',16),('Heading 2',12)]:
    doc.styles[nom].font.name='Calibri'
    doc.styles[nom].font.size=Pt(taille)
    doc.styles[nom].font.color.rgb=RGBColor.from_string('000000' if nom=='Title' else '17365D')
# Le modèle Word de python-docx peut inclure un trait sous le titre : le supprimer.
for border in list(doc.styles['Title'].element.xpath('./w:pPr/w:pBdr')):
    border.getparent().remove(border)
doc.core_properties.author='[NOM] [PRÉNOM]'
doc.core_properties.title='TP05 AutoML et déploiement de modèles'
doc.core_properties.subject='Comparaison de deux modèles de détection de fraude'
sec.header.paragraphs[0].text='EMSI | 5IASD | Déploiement d’IA | TP05'
sec.header.paragraphs[0].style='Caption'
footer=sec.footer.paragraphs[0]
footer.text='[NOM] [PRÉNOM]  |  [FILIÈRE]  |  [GROUPE]                         '
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)
doc.add_heading('TP05 AutoML et déploiement de modèles',0)
doc.add_paragraph('Compte rendu de travaux pratiques',style='Subtitle')
for p in introduction.strip().split('\n'):
    if p.strip(): doc.add_paragraph(p.strip())
doc.add_heading('Protocole et preuves',1)
doc.add_paragraph("La recherche dispose de 90 secondes. Les deux modèles suivent le même découpage et le même registre. L'export AutoML est vérifié par égalité des F1. Les latences sont mesurées successivement dans l'ordre 8100, 8101, 8100, 8101, avec dix échauffements puis deux cents appels. Les preuves texte, signatures, configurations, matrices de confusion et versions figurent dans reports/preuves/.")
doc.add_paragraph('Dépôt : https://github.com/ZED-abd/TP05_Creer_Deployer_Modele_AutoML')
doc.add_paragraph('Nom exigé dans le PDF : mlops-tp5-automl. Cet écart doit être vérifié avant le rendu.')
doc.add_page_break()
doc.add_heading('Comparaison et décision',1)
rows = [line for line in comparaison.splitlines() if line.startswith('|') and not line.startswith('|---')]
table=doc.add_table(rows=0,cols=3)
table.style='Table Grid'
table.autofit=False
for rownum,line in enumerate(rows):
    cells=table.add_row().cells
    for i,v in enumerate(line.strip('|').split('|')):
        cells[i].text=v.strip()
        cells[i].width=Inches([2.1,2.45,2.45][i])
        for p in cells[i].paragraphs:
            p.paragraph_format.space_after=Pt(5)
            p.paragraph_format.space_before=Pt(5)
            for r in p.runs:r.font.size=Pt(10)
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'17365D' if rownum==0 else ('EDF2F7' if rownum%2 else 'FFFFFF'))
        cells[i]._tc.get_or_add_tcPr().append(shade)
        if rownum==0:
            for r in cells[i].paragraphs[0].runs:r.bold=True;r.font.color.rgb=RGBColor(255,255,255)
    if rownum==0:
        repeat=OxmlElement('w:tblHeader');table.rows[-1]._tr.get_or_add_trPr().append(repeat)
doc.add_paragraph('Latences : mesures 1 / 2 ; p95 calculé séparément pour chaque série. Mo = 1 048 576 octets.',style='Caption')
doc.add_heading('Décision de production',2)
for ligne in decision.splitlines():
    if ligne.strip():doc.add_paragraph(ligne.strip())
doc.add_paragraph('Temps humain : [À REMPLIR PAR L’ÉTUDIANT]. Suggestions indicatives : 30 à 90 min pour le réglage manuel ; 10 à 30 min pour la préparation AutoML. Ces fourchettes ne sont pas des durées mesurées.',style='Caption')
doc.add_page_break()
doc.add_heading('Analyse des modèles',1)
for nom,d in C.items():
    doc.add_heading('Modèle '+('manuel' if nom=='manuel' else 'AutoML'),2)
    doc.add_paragraph(f"Classe {d['classe']} ; nombre d'arbres {d['nombre_arbres']} ; profondeur paramétrée {d['profondeur_parametree']} ; profondeurs observées {d.get('profondeurs_reelles','non disponibles')}.")
    doc.add_paragraph(f"Matrice de confusion {d['matrice_confusion']} ; lignes = classes réelles 0, 1 ; colonnes = classes prédites 0, 1.")
    doc.add_paragraph('Importances globales : '+('; '.join(f'{k} {v:.4f}' for k,v in d['importances']) if isinstance(d['importances'],list) else d['importances']))
doc.add_heading('Hyperparamètres gagnants',2)
doc.add_paragraph('; '.join(k.removeprefix('cfg_')+' = '+v for k,v in A['registre']['params'].items() if k.startswith('cfg_')))
doc.add_heading('Écarts et limites',2)
doc.add_paragraph(f"F1 manuel attendu 0.8669 ; mesuré {M['f1']:.4f}. Taille indicative attendue 13 à 14 Mo ; mesurée {M['taille_Mo']:.4f} Mo. Les versions de bibliothèque et la représentation sérialisée peuvent modifier les tailles. Les valeurs réelles sont conservées ; aucune cible n'a été forcée. Les deux modèles ont été enregistrés en version {M['registre']['version']} et {A['registre']['version']} pour la première campagne.")
doc.add_paragraph("Le test isolé du script complet a retenu XGBoost avec un F1 de 0.8561, contre LightGBM et 0.8409 dans la campagne présentée ici. Le budget FLAML rend donc la famille variable même lors de deux exécutions sur ce poste. Les résultats de ces campagnes restent séparés. Les importances sont normalisées par baisse d'impureté pour la forêt et comptées en divisions pour LightGBM ; leurs amplitudes ne sont pas comparables. Les services sont locaux ; aucun test de charge ni mesure cloud. Le bloc G n'a pas été exécuté.")
for i in range(0,6,2):
    doc.add_page_break()
    for titre,texte in questions[i:i+2]:
        doc.add_heading(titre,1)
        doc.add_paragraph(texte)
doc.add_page_break()
doc.add_heading('Captures à réaliser par l’étudiant',1)
doc.add_paragraph('[À FAIRE PAR L’ÉTUDIANT] Aucune capture n’a été générée automatiquement.')
for i,texte in enumerate(captures,1):
    doc.add_heading('Capture '+str(i),2)
    doc.add_paragraph(texte)
    doc.add_paragraph('Insérer ici la capture réelle après vérification des valeurs.')
doc.add_heading('Sources et finalisation',1)
for source in sources:
    p=doc.add_paragraph(source)
    for run in p.runs:run.font.size=Pt(9)
doc.add_paragraph("Avant envoi : compléter identité et temps humain, insérer les captures, vérifier le nom et la visibilité du dépôt, relire les six réponses. Le guide A_FAIRE_MANUELLEMENT.md détaille les étapes. Envoi sous 48 heures après la séance à h.naciri@emsi.ma, objet Nom Prénom_Filière_Groupe. Aucun e-mail n'a été envoyé par l'agent.")
sortie=Path('rendu/Nom_Prénom_Filière_Groupe.docx')
doc.save(sortie)
print(sortie)
print('Mots des réponses :', [len(t.split()) for _,t in questions])
