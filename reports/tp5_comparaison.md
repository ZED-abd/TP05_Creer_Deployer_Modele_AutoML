# Modele manuel ou modele AutoML ? (TP05)

| Critere | Manuel (rf 500/16) | AutoML (FLAML 90 s) |
|---|---|---|
| Famille de modele | foret aleatoire | lgbm |
| F1 sur le jeu de test | 0.8669 | 0.8409 |
| Temps de recherche machine | 2.4 s (entraînement) | 90.3 s |
| Temps humain (estimation) | [À REMPLIR PAR L’ÉTUDIANT] | [À REMPLIR PAR L’ÉTUDIANT] |
| Latence mediane (ms) | 45.8 / 46.1 | 9.7 / 10.1 |
| Latence p95 (ms) | 54.1 / 51.8 | 31.6 / 30.1 |
| Taille du fichier (Mo) | 13.3735 | 0.0622 |
| Explicabilite | montant=0.4789; anciennete=0.2370; freq_24h=0.1915; nuit=0.0926 | montant=116.0000; anciennete=87.0000; freq_24h=78.0000; nuit=31.0000 |

Mesures 1 / 2, sans moyenne des p95. Mo = 1 048 576 octets (convention PowerShell 1MB). Temps humain : suggestion de saisie 30 à 90 minutes pour le réglage manuel et 10 à 30 minutes pour AutoML ; estimations indicatives, aucune durée personnelle mesurée.

manuel : matrice de confusion [lignes réelles 0/1, colonnes prédites 0/1] [[1101, 15], [20, 114]], 500 arbres, profondeur paramétrée 16, profondeurs observées {'min': 11, 'max': 16}.

automl : matrice de confusion [lignes réelles 0/1, colonnes prédites 0/1] [[1097, 19], [23, 111]], 104 arbres, profondeur paramétrée -1, profondeurs observées {'min': 2, 'max': 3}.

Configuration gagnante : {"cfg_n_estimators": "104", "cfg_num_leaves": "4", "cfg_min_child_samples": "43", "cfg_learning_rate": "0.6558491573833527", "cfg_log_max_bin": "5", "cfg_colsample_bytree": "0.9051169955870563", "cfg_reg_alpha": "0.0009765625", "cfg_reg_lambda": "6.492993307502377"}

Les importances ne sont pas sur la même échelle : forêt = baisse normalisée d’impureté ; LightGBM = nombre de divisions (importance_type=split). Elles sont descriptives, sans comparaison directe de leurs amplitudes. La profondeur LightGBM -1 signifie absence de borne explicite ; les 4 feuilles bornent ici les arbres observés à 2–3 niveaux.

## Decision (5 lignes) : quel modele mettre en production, et pourquoi ?

Nous retenons le modèle manuel pour ce prototype de fraude, en donnant priorité à la qualité ; aucun objectif maximal de latence métier n’a été fourni.
Le manuel atteint F1 0.8669 contre 0.8409 ; ses faux négatifs sont 20 contre 23 pour AutoML, sur le même test.
Le compromis de service reste explicite : p95 manuel 54.1 / 51.8 ms contre 31.6 / 30.1 ms pour AutoML, sans mesure de charge concurrente.
Le fichier manuel pèse 13.3735 Mo contre 0.0622 Mo ; ses 500 arbres de profondeur maximale 16 restent inspectables, tout comme les 104 arbres du gagnant AutoML.
La recette manuelle fixe les réglages scikit-learn ; le budget FLAML peut changer le gagnant et impose ici lightgbm en production ; conserver les deux versions et réévaluer le choix si le besoin privilégie la latence ou la mémoire.
