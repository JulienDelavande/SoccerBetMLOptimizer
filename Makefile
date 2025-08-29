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


stop:
	@cat .pid | xargs kill -9 || true
	@rm -f .pid

build-mac:
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-data-ingestion:$(TAG) ./data-ingestion
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-pipelines:$(TAG) ./pipelines
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-app-backend:$(TAG) ./app-backend
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-app-frontend:$(TAG) ./app-frontend

build-mac-pipelines:
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-pipelines:$(TAG) ./pipelines

build:
	docker compose build

up:
	docker compose up

tag:
	docker tag $(IMAGE_PREFIX)-data-ingestion:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(TAG)
	docker tag $(IMAGE_PREFIX)-pipelines:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(TAG)
	docker tag $(IMAGE_PREFIX)-app-backend:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(TAG)
	docker tag $(IMAGE_PREFIX)-app-frontend:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(TAG)

push:
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(TAG)

deploy:
	kubectl create namespace $(NAMESPACE) || true
	helm upgrade --install optimsportbets ./k8s/helm-deploy-contabo/optimsportbets --namespace $(NAMESPACE) --set containerRegistry.registry=$(CONTAINER_REGISTRY) --set services.dataIngestion.tag=$(TAG) \
		--set services.pipelines.tag=$(TAG) --set services.appBackend.tag=$(TAG) --set services.appFrontend.tag=$(TAG)
	kubectl apply -n $(NAMESPACE) -f ./k8s/helm-deploy-contabo/cron-jobs

test:
	export $(grep -v '^#' compose.env)
	printenv DATA_INGESTION_HOST
