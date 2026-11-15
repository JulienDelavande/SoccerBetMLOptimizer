import os

# app._config refuses to import without these; tests never open a connection with them
# (services take the engine lazily and tests patch it or the service functions).
for _k, _v in {
    "DB_TYPE": "postgresql", "DB_PILOT": "psycopg2", "DB_USER": "test", "DB_PASSWORD": "test",
    "DB_HOST": "localhost", "DB_PORT": "5432", "DB_NAME": "test",
    "DB_TN_FBREF_RESULTS": "fbref_results", "DB_TN_MODELS_RESULTS": "models_results",
    "DB_TN_OPTIM_RESULTS": "optim_results",
    "PIPELINES_PROTOCOL": "http", "PIPELINES_HOST": "localhost", "PIPELINES_PORT": "8101",
    "PIPELINES_ENDPOINT_INFERENCE": "infer", "PIPELINES_ENDPOINT_OPTIMIZATION": "optimize",
    "DATA_INGESTION_PROTOCOL": "http", "DATA_INGESTION_HOST": "localhost", "DATA_INGESTION_PORT": "8100",
    "DATA_INGESTION_ENDPOINT_FBREF": "fbref", "DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS": "odds",
}.items():
    os.environ.setdefault(_k, _v)
