# Contrôles finaux du 5 novembre 2026

- Les cinq listings extraits du PDF, donnees.py et les scripts Python supplémentaires passent `python -m py_compile`.
- Les trois scripts d'orchestration PowerShell et l'orchestrateur principal passent l'analyse syntaxique native de PowerShell. Les helpers et le script complet sont exécutés réellement sous Windows, ce dernier dans un registre isolé avec `-SansInstallation`.
- Les données contiennent 5000 transactions, 568 fraudes et 5001 lignes avec l'en-tête. L'empreinte SHA-256 est dans validation_donnees.json.
- Le run automl-90s, la famille lgbm, les paramètres cfg_…, le F1 exporté identique et la version 1 sont contrôlés par l'API MLflow. Le paquet contient cloudpickle et lightgbm. La référence manuelle est en version 1 au format skops.
- Deux séries réelles de 200 mesures, précédées chacune de 10 échauffements, ont été faites par service, successivement et sans autre travail lancé en parallèle. Les journaux comptent 422 réponses HTTP 200 par port, affichages et échauffements inclus ; une réponse HTTP 400 par port valide les entrées manquantes.
- Les importances, nombres d'arbres, profondeurs, tailles et matrices de confusion sont calculés sur les objets effectivement exportés.
- Le rapport Word personnel comporte 7 pages et six réponses de 167, 156, 170, 168, 167 et 175 mots. Le rendu canonique render_docx.py a signalé LibreOffice absent. Le document a donc été exporté par Microsoft Word installé en mode invisible, puis rasterisé avec pypdfium2 du runtime documentaire ; les sept pages ont été inspectées. Le trait du style Title a été supprimé, puis le rendu a été vérifié de nouveau. Les pages 2 à 7 sont identiques après cette correction.
- Aucune capture du TP n'est produite : les trois emplacements et leur contenu attendu restent explicitement à réaliser par l'étudiant. Les images de contrôle Word ne sont pas des captures des services.
- Aucun correctif d'API des bibliothèques n'a été nécessaire dans les listings. La correction d'arrêt liée aux dates ISO de PowerShell est documentée dans validation_reproduction.md.
- Les journaux sont anonymisés et normalisés en UTF-8. Le contrôle des fichiers sources et preuves ne trouve aucun chemin de profil personnel ou secret apparent. Le contrôle Git des espaces est réussi.
- L'API GitHub confirme le dépôt public, sous le nom TP05_Creer_Deployer_Modele_AutoML ; le nom exigé mlops-tp5-automl reste à valider avant rendu. Aucun dépôt créé ni renommé.
- Le bloc G, les commandes cloud, la création de compte et l'envoi d'e-mail ne sont pas exécutés.
- Après les deux campagnes, les ports 5000, 8100 et 8101 sont libres, avec test de liaison TCP exclusive réussi. Aucun fichier d'état de processus ne reste après le test complet.
