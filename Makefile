VENV = venv

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

ifneq (,$(wildcard ./secrets.env))
    include secrets.env
    export
endif

test:
	@echo $$ | awk '{print Hello $$1 pid}' >> .pid

start-data-ingestion:
	@source $(VENV)/Scripts/activate && \
	cd data-service && \
	uvicorn main:app --port $(DATA_INGESTION_SERVICE_NPORT) --reload & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-pipelines:
	@source $(VENV)/Scripts/activate && \
	cd pipelines && \
	uvicorn main:app --port $(PIPELINES_SERVICE_NPORT) --reload & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-mlflow:
	@source $(VENV)/Scripts/activate && \
	cd mlflow && \
	mlflow server --host 0.0.0.0 \
              --port $(MLFLOW_WEBSERVER_CONTAINER_PORT) & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-frontend:
	@source $(VENV)/Scripts/activate && \
	cd app-frontend && \
	streamlit run main.py --server.port $(PIPELINES_SERVICE_NPORT) & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start-backend:
	@source $(VENV)/Scripts/activate && \
	cd app-backend && \
	uvicorn main:app --port $(APP_BACKEND_PORT) --reload & \
	PID=$$! && \
	echo $$((PID + 1)) >> .pid

start: start-data-ingestion start-pipelines start-mlflow start-frontend start-backend

# Docker

CONTAINER_REGISTRY = optimsportbets.azurecr.io
IMAGE_PREFIX = optim-sportbet
DATA_INGESTION_TAG = 1.1
PIPELINES_TAG = 1.1
MLFLOW_TAG = 1.2
APP_BACKEND_TAG = 1.1
APP_FRONTEND_TAG = 1.1

stop:
	@cat .pid | xargs kill -9
	@rm .pid

build:
	@docker compose --env-file .env --env-file compose.env -f compose.yml build

up:
	@docker compose --env-file .env --env-file compose.env -f compose.yml up

tag:
	@docker tag $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(DATA_INGESTION_TAG) $(IMAGE_PREFIX)-data-ingestion:latest
	@docker tag $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(PIPELINES_TAG) $(IMAGE_PREFIX)-pipelines:latest
	@docker tag $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-mlflow:$(MLFLOW_TAG) $(IMAGE_PREFIX)-mlflow:latest
	@docker tag $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(APP_BACKEND_TAG) $(IMAGE_PREFIX)-app-backend:latest
	@docker tag $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(APP_FRONTEND_TAG) $(IMAGE_PREFIX)-app-frontend:latest

push:
	@docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(DATA_INGESTION_TAG)
	@docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(PIPELINES_TAG)
	@docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-mlflow:$(MLFLOW_TAG)
	@docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(APP_BACKEND_TAG)
	@docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(APP_FRONTEND_TAG)

