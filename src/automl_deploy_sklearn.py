# Plan B du TP05 : recherche automatique avec scikit-learn seul (sans FLAML)
import time
from pathlib import Path
import joblib
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.pipeline import Pipeline
from sklearn.ensemble import (RandomForestClassifier, ExtraTreesClassifier,
                              HistGradientBoostingClassifier)
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import f1_score

df = pd.read_csv('data/transactions.csv')
X, y = df.drop(columns='fraude'), df['fraude']
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
espace = [
    {'clf': [RandomForestClassifier(random_state=42)],
     'clf__n_estimators': [100, 200, 400], 'clf__max_depth': [6, 10, 16, None]},
    {'clf': [ExtraTreesClassifier(random_state=42)],
     'clf__n_estimators': [100, 200, 400], 'clf__max_depth': [6, 10, 16, None]},
    {'clf': [HistGradientBoostingClassifier(random_state=42)],
     'clf__learning_rate': [0.03, 0.1, 0.3],
     'clf__max_leaf_nodes': [15, 31, 63]},
]
recherche = RandomizedSearchCV(Pipeline([('clf', RandomForestClassifier())]),
                               espace, n_iter=20, cv=3, scoring='f1',
                               random_state=42, n_jobs=-1)
t0 = time.time()
recherche.fit(Xtr, ytr)
duree = round(time.time() - t0, 1)
modele = recherche.best_estimator_
famille = type(modele.named_steps['clf']).__name__
f1 = round(f1_score(yte, modele.predict(Xte)), 4)
print('famille retenue :', famille, '| F1 test :', f1, '|', duree, 's')
Path('models').mkdir(exist_ok=True)
joblib.dump(modele, 'models/model_automl.pkl')
mlflow.set_tracking_uri('http://127.0.0.1:5000')
mlflow.set_experiment('tp5-automl-deploiement')
with mlflow.start_run(run_name='sklearn-recherche-20'):
    mlflow.log_params({'outil': 'sklearn-maison', 'famille': famille})
    mlflow.log_metrics({'f1': f1, 'duree_recherche_s': duree})
    info = mlflow.sklearn.log_model(
        modele, name='model', input_example=Xte.head(3),
        registered_model_name='fraude-automl',
        serialization_format='cloudpickle')
print('enregistre : fraude-automl, version', info.registered_model_version)
