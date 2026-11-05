# Tarification officielle consultée le 5 novembre 2026

URL demandée : https://cloud.google.com/vertex-ai/pricing
URL finale servie : https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing
Accès : Firecrawl, lecture seule. Aucun compte ni ressource créé.

La section AutoML Tabular data renvoie au tarif des modèles personnalisés pour l’inférence. La section Prediction and explanation, N1 Series, affiche Iowa (us-central1) et un tarif à la demande n1-standard-2 de 0.1095 USD par heure. Une machine restant déployée est facturée même sans prédiction.

Hypothèse de calcul théorique : une réplique n1-standard-2, us-central1, 24 h/jour, 30 jours, sans GPU ni réduction contractuelle. 0.1095 × 24 × 30 = 78.84 USD. Variante 730 h : 79.935 USD, soit 79.94 USD arrondis. Entraînement, stockage, trafic, taxes et autres services exclus. Aucune facture cloud mesurée.

Compatibilité : la documentation officielle https://cloud.google.com/vertex-ai/docs/predictions/configure-compute (consultée le même jour, redirigée vers https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/predictions/configure-compute) couvre les modèles personnalisés et AutoML tabulaires et liste n1-standard-2 avec 2 vCPU et 7.5 Go de mémoire. Il s'agit d'une hypothèse d'une seule réplique, sans garantie de débit ni mesure sur cette machine.

La page consultée utilise désormais le titre Gemini platform pricing ; le nom Vertex AI est conservé pour correspondre au TP. Le tarif d’entraînement ne doit pas être confondu avec le tarif d’inférence.

