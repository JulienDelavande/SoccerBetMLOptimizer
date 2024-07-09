SHELL := git-bash.exe

devenv:
	ls /
	source venv/Scripts/activate
	
start_data_ingestion:
	uvicorn data-ingestion-service.main:app --reload

start_pipelines:
	uvicorn pipelines-service.main:app --reload