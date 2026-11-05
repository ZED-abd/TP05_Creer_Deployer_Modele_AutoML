# TP05 AutoML et déploiement avec MLflow

Travaux pratiques EMSI, 5IASD : comparer un gagnant AutoML et une forêt aléatoire de référence, les enregistrer dans MLflow, les promouvoir par alias et les appeler en HTTP local.

Tous les calculs sont locaux. Le bloc G n'est pas exécuté. Les captures réelles et le temps humain sont à compléter par l'étudiant ; aucun résultat ni capture n'est simulé.

## Organisation

- `donnees.py` : données synthétiques, graine 7 (le fichier du TP04 est absent).
- `src/` : cinq listings reconstruits à partir du PDF, plan A FLAML et annexe A disponibles.
- `scripts/run_tp05.ps1` : reproduction complète ; `stop_services.ps1` : arrêt des processus du TP et vérification des ports ; `services.ps1` : démarrage et contrôles de santé ; `preuves.py` : validations, inspection, explicabilité, comparaison et anonymisation.
- `reports/tp5_comparaison.md` : tableau des mesures et décision ; `reports/flaml_tp5.log` : journal réel de recherche ; `reports/preuves/` : sorties et informations de machine.
- `data/`, `models/`, `mlflow.db`, `mlartifacts/` : résultats locaux, exclus de Git.
- `rendu/` : rapport Word et Markdown, checklist du PDF, e-mail préparé et guide manuel, exclus de Git.

## Reproduction PowerShell

Python 3.13 est conseillé. Le lanceur `py -0` n'a détecté aucun interpréteur durant cette exécution ; `python` désigne pourtant Python 3.13.3 et a permis de créer le venv. Aucune installation globale n'a été effectuée.

Depuis la racine du dépôt, dans PowerShell :

```powershell
./scripts/run_tp05.ps1
# Si Python n'est pas dans PATH :
./scripts/run_tp05.ps1 -PythonExe 'CHEMIN_VERS_PYTHON/python.exe'
# Si les dépendances sont déjà installées :
./scripts/run_tp05.ps1 -SansInstallation
```

Le script utilise `.venv`, installe les quatre dépendances de l'énoncé, régénère les données et contrôle 5000 transactions, 568 fraudes et 5001 lignes. Il lance MLflow et les deux services via `Start-Process -PassThru -WindowStyle Hidden`, avec journaux séparés, et attend `/health` puis `/ping`. Il exécute les quatre séries de latence successivement. Le bloc `finally` arrête les processus enregistrés et leurs enfants, contrôle les ports 5000, 8100 et 8101 et anonymise les chemins des preuves.

Le premier lancement a utilisé un registre neuf : versions 1. Les relances conservent la base et créent de nouvelles versions ; l'alias production est déplacé vers la dernière. Aucune base existante n'est supprimée automatiquement. Ne pas lancer deux campagnes simultanément. Un port déjà occupé fait échouer le démarrage pour éviter d'interrompre un autre programme.

En cas d'interruption manuelle :

```powershell
./scripts/stop_services.ps1
```

Les PID et dates de création sont conservés dans `rendu/processus.json` pendant l'exécution. Seuls ces processus et leurs descendants sont arrêtés. Les journaux sont de vraies sorties texte ; ils ne remplacent pas les captures demandées.

## Quatre terminaux pour les captures

Dans chaque terminal, se placer à la racine du projet et activer le venv :

```powershell
. ./.venv/Scripts/Activate.ps1
```

Terminal 1, serveur de suivi :

```powershell
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts
```

Terminal 2, travail et clients (après disponibilité des services) :

```powershell
python src/client.py 8100
python src/client.py 8101
python src/client.py 8100
python src/client.py 8101
$mauvais = @{ dataframe_records = @(@{ montant = 8500 }) } | ConvertTo-Json -Depth 5
try {
    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8100/invocations -ContentType 'application/json' -Body $mauvais
} catch { $_.ErrorDetails.Message }
```

Terminal 3, AutoML :

```powershell
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
mlflow models serve -m 'models:/fraude-automl@production' -p 8100 --env-manager local
```

Terminal 4, référence manuelle :

```powershell
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
mlflow models serve -m 'models:/fraude-manuel@production' -p 8101 --env-manager local
```

Arrêter ces trois processus de premier plan par Ctrl+C après les captures. Le script d'arrêt automatique concerne uniquement les services qu'il a lui-même lancés.

## Fidélité et compatibilité

Le PDF local a été extrait avec `pypdf`, option `extraction_mode='layout'`, dans `rendu/enonce_extrait.txt` (11 pages). Les listings ont été reconstruits puis compilés avec `python -m py_compile`. Le découpage sans stratification, les graines, les familles, les paramètres et les métriques du PDF sont conservés. Le plan A est utilisé ; l'annexe A est fournie en secours et n'est pas exécutée si FLAML est installé.

Les correctifs éventuellement nécessaires et les versions effectivement utilisées sont précisés avec les résultats de la campagne ci-dessous. Les scripts supplémentaires de contrôle sont distincts des listings pédagogiques.

Si FLAML est réellement impossible à installer après essai avec Python 3.13 : retirer `flaml[automl]` de `requirements.txt`, conserver `mlflow`, `scikit-learn`, `pandas` et relancer. Le script choisira `automl_deploy_sklearn.py` (20 configurations, 3 plis). Signaler le plan B dans le rapport et adapter le nom de run demandé pour la capture. Ne pas présenter un résultat du plan B comme une recherche FLAML de 90 s.

## Sources et limites

Les prix et possibilités d'export sont documentés dans `reports/preuves/tarification_vertex_ai.md` et `reversibilite_vertex_ai.md`, avec les URL officielles et la date du 5 novembre 2026. Coût théorique pour une seule n1-standard-2, us-central1 : 0.1095 USD/h × 720 h = 78.84 USD, hors coûts complémentaires ; aucune facture ni latence cloud mesurée.

La recherche à budget temporel dépend du poste même avec une graine fixée. Les latences sont celles d'appels séquentiels à chaud en loopback, sans test de charge. Le F1 est une mesure sur ce jeu synthétique, pas une validation métier de fraude réelle. Les importances globales ne constituent pas une explication individuelle.

Le nom du dépôt fourni est conservé : `TP05_Creer_Deployer_Modele_AutoML`. Le PDF exige `mlops-tp5-automl` et un dépôt public ; cette conformité est à vérifier par l'étudiant. Aucun dépôt n'a été créé ou renommé.

## Résultats de la campagne

Campagne principale du 5 novembre 2026, plan A, Windows 11 (build 26300), Intel i7-1265U, 12 processeurs logiques, 15.69 Go de RAM utilisable. Exécution Codex à permissions restreintes sur ce poste ; aucune machine cloud. Confirmer les latences sur le poste avant le rendu. Python 3.13.3, FLAML 2.7.0, MLflow 3.18.0, scikit-learn 1.9.1, LightGBM 4.7.0, XGBoost 2.1.4, pandas 3.1.1, NumPy 2.5.4, skops 0.16.0. Toutes les versions sont dans `reports/preuves/machine.txt` et `versions_figees.txt`.

| Mesure | Manuel | AutoML |
|---|---|---|
| Famille | RandomForestClassifier | LightGBM |
| F1 test | 0.8669 | 0.8409 |
| Entraînement ou recherche | 2.4 s | 90.3 s |
| Médianes des deux séries | 45.8 / 46.1 ms | 9.7 / 10.1 ms |
| p95 des deux séries | 54.1 / 51.8 ms | 31.6 / 30.1 ms |
| Taille du fichier joblib | 13.3735 Mo | 0.0622 Mo |
| Arbres et profondeurs observées | 500, de 11 à 16 | 104, de 2 à 3 |
| Confusion TN, FP, FN, TP | 1101, 15, 20, 114 | 1097, 19, 23, 111 |
| Version et format du registre | 1, skops | 1, cloudpickle |

Le F1 manuel et sa taille correspondent aux indications du PDF. L'égalité F1 FLAML/export est vérifiée à 0.8409 ; les deux alias production pointaient vers la version 1. Tous les 422 appels valides par service ont répondu HTTP 200 ; chaque requête invalide a répondu HTTP 400 en citant les trois colonnes manquantes. Les ports ont été libérés et vérifiés par liaison TCP exclusive.

Nous retenons le manuel pour la qualité de détection, en l'absence d'objectif métier de latence fourni. AutoML constitue une alternative beaucoup plus compacte et plus rapide. Le tableau complet, les importances et la décision en cinq lignes sont dans `reports/tp5_comparaison.md`. Les importances de forêt (baisse normalisée d'impureté) et de LightGBM (nombre de divisions) ont des échelles différentes.

Aucun correctif de compatibilité des bibliothèques n'a été nécessaire dans les cinq listings du PDF. `name=`, `skops_trusted_types` et `serialization_format` fonctionnent avec MLflow 3.18.0. Le plan B a été compilé mais n'a pas été exécuté. Le contrôle d'arrêt PowerShell compare les dates de création en ticks UTC pour tenir compte de la conversion automatique des dates ISO par `ConvertFrom-Json` sous PowerShell 7.

Le script complet a été testé avec `-SansInstallation` dans `rendu/verification_reproduction/`, sur un registre isolé et le même venv local. Il s'est terminé avec le code 0 et les trois ports libres. Ce second lancement a choisi XGBoost, F1 0.8561, alors que la référence manuelle reste à 0.8669. Cette variation réelle illustre le caractère non strictement déterministe du budget temps. Les preuves de la campagne principale ne sont pas remplacées par celles de ce test ; voir `reports/preuves/validation_reproduction.md`.

Les fichiers de preuve sont anonymisés (`[PROJET]`, `[PROFIL]`) et leurs fins de ligne normalisées ; métriques et messages de service sont conservés. Pour figer à nouveau l'environnement existant, utiliser le fichier `reports/preuves/versions_figees.txt` avec pip dans un venv Python 3.13, plutôt que réinstaller ultérieurement les dernières versions sans contrôle.

Le rapport personnel Word et les six réponses sont dans `rendu/` (ignoré par Git). Chaque réponse comporte de 156 à 175 mots. `scripts/generer_rapport.py` utilise `python-docx`, disponible dans le runtime documentaire employé pour ce travail ; cette bibliothèque n'est pas nécessaire à l'exécution MLOps. Le rendu Word a été contrôlé visuellement après export par Microsoft Word installé, car LibreOffice n'est pas disponible. Les PNG de contrôle ne sont pas des captures du TP et ne sont pas des livrables à insérer.

Le dépôt est public d'après les métadonnées GitHub consultées le 5 novembre 2026. Son nom reste différent du nom exigé par le PDF ; voir le guide personnel `rendu/A_FAIRE_MANUELLEMENT.md`.
