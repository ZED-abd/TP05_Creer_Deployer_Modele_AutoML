# Validation du script complet sous Windows

Date : 5 novembre 2026.

Commande réellement exécutée : `./rendu/verification_reproduction/scripts/run_tp05.ps1 -SansInstallation`.

Le script a été copié sans modification fonctionnelle dans un sous-dossier ignoré par Git, avec les sources et le générateur de données. Une jonction locale `.venv` réutilise le venv du projet ; la base SQLite, les artefacts et les preuves de ce test sont séparés de la campagne de référence. Aucune donnée personnelle ni aucun modèle n'est publié.

Résultat : code de sortie 0. Données validées (5000 transactions, 568 fraudes), deux modèles en version 1 du registre isolé, inspections des paquets réussies, alias production, santé des deux services, quatre séries de latence successives, requêtes invalides rejetées sur les deux ports, matrices et tailles calculées. Les journaux confirment 422 réponses HTTP 200 par service et une réponse HTTP 400 par service. Le fichier d'état des processus a été supprimé après arrêt réussi. Les ports 5000, 8100 et 8101 ont réussi le test final de liaison TCP exclusive.

Le test a retenu XGBClassifier avec un F1 de test de 0.8560606060606061 ; la référence manuelle retrouve 0.8669201520912547. La campagne principale documentée dans reports/tp5_comparaison.md reste LightGBM à 0.8409090909090909 et la même forêt manuelle. Ces mesures ne sont pas mélangées. La recherche FLAML à budget temps peut donc varier même entre deux lancements sur le même poste ; une graine ne fixe pas le nombre d'essais achevés.

L'installation avait été validée auparavant dans le venv racine avec les commandes de pip du script. Ce test utilise `-SansInstallation` et n'installe aucune bibliothèque supplémentaire.

Correction d'orchestration validée : les dates ISO chargées par ConvertFrom-Json peuvent devenir des DateTime sous PowerShell 7. Le script d'arrêt compare les ticks UTC plutôt qu'une chaîne à un DateTime. Il arrête les superviseurs avant leurs descendants et ne supprime le fichier d'état qu'après libération des ports. Les listings du PDF n'ont nécessité aucun correctif de bibliothèque avec les versions installées.
