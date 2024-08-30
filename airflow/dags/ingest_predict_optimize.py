from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

DATA_INGESTION_SERVICE_NAME = "data-ingestion"
DATA_INGESTION_SERVICE_NPORT = "8000"
DATA_INGESTION_FBREF_ENDPOINT = "fbref"
DATA_INGESTION_SOFIFA_TEAM_STATS_ENDPOINT = "sofifa/team_stats"
DATA_INGESTION_THE_ODDS_API_ODDS_ENDPOINT = "the_odds_api/odds"

PIPELINES_SERVICE_NAME = "pipelines"
PIPELINES_SERVICE_NPORT = "8001"
PIPELINES_SERVICE_INFERENCE_ENDPOINT = "infer/RSF_PR_LR"
PIPELINES_SERVICE_OPTIMIZATION_ENDPOINT = "optim"

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
    bash_command=f'curl -X GET "http://{DATA_INGESTION_SERVICE_NAME}:{DATA_INGESTION_SERVICE_NPORT}/{DATA_INGESTION_FBREF_ENDPOINT}" -H "accept: application/json"',
    dag=dag,
)

ingest_sofifa_team_stats_data = BashOperator(
    task_id='ingest_sofifa_team_stats_data',
    bash_command=f'curl -X GET "http://{DATA_INGESTION_SERVICE_NAME}:{DATA_INGESTION_SERVICE_NPORT}/{DATA_INGESTION_SOFIFA_TEAM_STATS_ENDPOINT}" -H "accept: application/json"',
    dag=dag,
)

ingest_the_odds_api_odds_data = BashOperator(
    task_id='ingest_the_odds_api_odds_data',
    bash_command=f'curl -X GET "http://{DATA_INGESTION_SERVICE_NAME}:{DATA_INGESTION_SERVICE_NPORT}/{DATA_INGESTION_THE_ODDS_API_ODDS_ENDPOINT}" -H "accept: application/json"',
    dag=dag,
)

infer_match_results = BashOperator(
    task_id='infer_match_results',
    bash_command=f'curl -X GET "http://{PIPELINES_SERVICE_NAME}:{PIPELINES_SERVICE_NPORT}/{PIPELINES_SERVICE_INFERENCE_ENDPOINT}" -H "accept: application/json"',
    dag=dag,
)

optimize_bankroll_to_invest = BashOperator(
    task_id='optimize_bankroll_to_invest',
    bash_command=f'curl -X GET "http://{PIPELINES_SERVICE_NAME}:{PIPELINES_SERVICE_NPORT}/{PIPELINES_SERVICE_OPTIMIZATION_ENDPOINT}" -H "accept: application/json"',
    dag=dag,
)

[ingest_fbref_data, ingest_sofifa_team_stats_data, ingest_the_odds_api_odds_data] >> infer_match_results >> optimize_bankroll_to_invest
