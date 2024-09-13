from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import os

# Data Ingestion
## API
DATA_INGESTION_PROTOCOL = os.getenv("DATA_INGESTION_SERVICE_PROTOCOL")
DATA_INGESTION_HOST = os.getenv("DATA_INGESTION_SERVICE_NAME")
DATA_INGESTION_PORT = os.getenv("DATA_INGESTION_SERVICE_NPORT")
DATA_INGESTION_ENDPOINT_FBREF = os.getenv("DATA_INGESTION_FBREF_ENDPOINT")
DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS = os.getenv("DATA_INGESTION_THE_ODDS_API_ODDS_ENDPOINT")
DATA_INGESTION_ENDPOINT_SOFIFA_TEAMS_STATS = os.getenv("DATA_INGESTION_SOFIFA_TEAM_STATS_ENDPOINT")
SOCCERDATA_DIR = os.getenv("SOCCERDATA_DIR")
# Pipelines
## API
PIPELINES_PROTOCOL = os.getenv("PIPELINES_SERVICE_PROTOCOL")
PIPELINES_HOST = os.getenv("PIPELINES_SERVICE_NAME")
PIPELINES_PORT = os.getenv("PIPELINES_SERVICE_NPORT")
PIPELINES_ENDPOINT_INFERENCE = os.getenv("PIPELINES_ENDPOINT_INFERENCE")
PIPELINES_ENDPOINT_OPTIMIZATION = os.getenv("PIPELINES_ENDPOINT_OPTIMIZATION")


# Configuration du DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ingest_predict_optimize',
    default_args=default_args,
    description='',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    catchup=False,
)

ingest_fbref_data = BashOperator(
    task_id='ingest_fbref_data',
    bash_command=f'curl -X GET "{DATA_INGESTION_PROTOCOL}://{DATA_INGESTION_HOST}:{DATA_INGESTION_PORT}/{DATA_INGESTION_ENDPOINT_FBREF}" -H "accept: application/json"',
    dag=dag,
)

ingest_sofifa_team_stats_data = BashOperator(
    task_id='ingest_sofifa_team_stats_data',
    bash_command=f'curl -X GET "{DATA_INGESTION_PROTOCOL}://{DATA_INGESTION_HOST}:{DATA_INGESTION_PORT}/{DATA_INGESTION_ENDPOINT_SOFIFA_TEAMS_STATS}" -H "accept: application/json"',
    dag=dag,
)

ingest_the_odds_api_odds_data = BashOperator(
    task_id='ingest_the_odds_api_odds_data',
    bash_command=f'curl -X GET "{DATA_INGESTION_PROTOCOL}://{DATA_INGESTION_HOST}:{DATA_INGESTION_PORT}/{DATA_INGESTION_ENDPOINT_THE_ODDS_API_ODDS}" -H "accept: application/json"',
    dag=dag,
)

infer_match_results = BashOperator(
    task_id='infer_match_results',
    bash_command=f'curl -X GET "{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_INFERENCE}" -H "accept: application/json"',
    dag=dag,
)

optimize_bankroll_to_invest = BashOperator(
    task_id='optimize_bankroll_to_invest',
    bash_command=f'curl -X GET "{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_INFERENCE}" -H "accept: application/json"',
    dag=dag,
)

[ingest_fbref_data, ingest_sofifa_team_stats_data, ingest_the_odds_api_odds_data] >> infer_match_results >> optimize_bankroll_to_invest
