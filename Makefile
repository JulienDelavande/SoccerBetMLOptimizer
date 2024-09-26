VENV = venv

# export $(grep -v '^#' .env)
# export $(grep -v '^#' secrets.env)

# export $(grep -v '^#' proddb.env)
# export $(grep -v '^#' secrets_proddb.env)

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

ifneq (,$(wildcard ./secrets.env))
    include secrets.env
    export
endif

# Comment this line if you don't want to use compose.env
ifneq (,$(wildcard ./compose.env))
    include compose.env
    export
endif
##############################################


start-data-ingestion:
	@source $(VENV)/Scripts/activate && \
	cd data-ingestion && \
	uvicorn main:app --port $(DATA_INGESTION_PORT) --reload >> logs/stdout.log 2>> logs/stderr.log & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-pipelines:
	@source $(VENV)/Scripts/activate && \
	cd pipelines && \
	uvicorn main:app --port $(PIPELINES_PORT) --reload >> logs/stdout.log 2>> logs/stderr.log & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-mlflow:
	@source $(VENV)/Scripts/activate && \
	cd mlflow && \
	mlflow server --host 0.0.0.0 \
              --port $(MLFLOW_PORT) >> logs/stdout.log 2>> logs/stderr.log & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-frontend:
	@source $(VENV)/Scripts/activate && \
	printenv DB_PASSWORD | cat -v && \
	cd app-frontend && \
	streamlit run main.py --server.port $(APP_FRONTEND_PORT) & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-backend:
	@source $(VENV)/Scripts/activate && \
	cd app-backend && \
	uvicorn main:app --port $(APP_BACKEND_PORT) --reload >> logs/stdout.log 2>> logs/stderr.log & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start: start-data-ingestion start-pipelines start-mlflow start-frontend start-backend

# Docker

CONTAINER_REGISTRY = optimsportbets.azurecr.io
#CONTAINER_REGISTRY = juliendelavande
IMAGE_PREFIX = optim-sportbet
DATA_INGESTION_TAG = 1.4
PIPELINES_TAG = 1.4
#MLFLOW_TAG = 1.3
APP_BACKEND_TAG = 1.3
APP_FRONTEND_TAG = 1.4

stop:
	@cat .pid | xargs kill -9 || true
	@rm -f .pid

build:
	docker compose build

up:
	docker compose up

tag:
	docker tag $(IMAGE_PREFIX)-data-ingestion:latest $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(DATA_INGESTION_TAG)
	docker tag $(IMAGE_PREFIX)-pipelines:latest	     $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(PIPELINES_TAG) 
	docker tag $(IMAGE_PREFIX)-app-backend:latest	 $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(APP_BACKEND_TAG)
	docker tag $(IMAGE_PREFIX)-app-frontend:latest   $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(APP_FRONTEND_TAG)

tag-mlflow:
	docker tag $(IMAGE_PREFIX)-mlflow:latest		 $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-mlflow:$(MLFLOW_TAG)

push:
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(DATA_INGESTION_TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(PIPELINES_TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(APP_BACKEND_TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(APP_FRONTEND_TAG)

push-mlflow:
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-mlflow:$(MLFLOW_TAG)

test:
	export $(grep -v '^#' compose.env)
	printenv DATA_INGESTION_HOST
