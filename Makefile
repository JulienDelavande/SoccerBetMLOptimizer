ifneq (,$(wildcard ./.env))
    include .env
    export
endif

ifneq (,$(wildcard ./.env.secrets))
    include .env.secrets
    export
endif

# Comment this line if you don't want to use compose.env
ifneq (,$(wildcard ./compose.env))
    include compose.env
    export
endif
###############################################

# Variables
DUMP_FILE = ./db/data_only_dump.sql
VIEWS_DIR = ./db/views
PG_PORT_FORWARD = 5433
PG_SERVICE = postgresql-global
PG_NAMESPACE = $(NAMESPACE)



### DEV RULES ###
dump-prod-db:
	@kubectl port-forward svc/$(PG_SERVICE) $(PG_PORT_FORWARD):5432 -n $(PG_NAMESPACE) & \
		echo "$$!" > .portforward_pid && \
		sleep 5 && \
		PGPASSWORD=$$DB_PASSWORD pg_dump \
			--data-only \
			--inserts \
			--rows-per-insert=1000 \
			--no-owner \
			--no-privileges \
			--format=plain \
			--file=$(DUMP_FILE) \
			-h localhost \
			-U $(DB_USER) \
			-p $(PG_PORT_FORWARD) \
			$(DB_NAME) && \
		kill -9 $$(cat .portforward_pid) && rm .portforward_pid

dev-up:
	docker-compose up -d
	until docker exec dev-postgres pg_isready -U $(DB_USER) > /dev/null 2>&1; do sleep 1; done
	cd db && uv run alembic upgrade head
	psql postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME) < $(DUMP_FILE)
	cat $(VIEWS_DIR)/*.sql | psql -h $(DB_HOST) -U $(DB_USER) -p $(DB_PORT) -d $(DB_NAME)

apply-views:
	cat $(VIEWS_DIR)/*.sql | psql -h $(DB_HOST) -U $(DB_USER) -p $(DB_PORT) -d $(DB_NAME)

dev-down:
	docker-compose down -v



### DEPLOYMENT RULES ###
build:
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-data-ingestion:$(TAG) -f ./data-ingestion/Dockerfile .
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-pipelines:$(TAG) -f ./pipelines/Dockerfile .
	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-app-backend:$(TAG) -f ./app-backend/Dockerfile .
#	docker buildx build --platform linux/amd64 --load -t $(IMAGE_PREFIX)-app-frontend:$(TAG) -f ./app-frontend/Dockerfile .

tag:
	docker tag $(IMAGE_PREFIX)-data-ingestion:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(TAG)
	docker tag $(IMAGE_PREFIX)-pipelines:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(TAG)
	docker tag $(IMAGE_PREFIX)-app-backend:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(TAG)
#   docker tag $(IMAGE_PREFIX)-app-frontend:$(TAG) $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(TAG)

push:
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-data-ingestion:$(TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-pipelines:$(TAG)
	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-backend:$(TAG)
#	docker push $(CONTAINER_REGISTRY)/$(IMAGE_PREFIX)-app-frontend:$(TAG)

deploy:
	kubectl create namespace $(NAMESPACE) || true
	helm upgrade --install optimsportbets ./k8s/optimsportbets --namespace $(NAMESPACE) --set containerRegistry.registry=$(CONTAINER_REGISTRY) --set services.dataIngestion.tag=$(TAG) \
		--set services.pipelines.tag=$(TAG) --set services.appBackend.tag=$(TAG) --set services.appFrontend.tag=$(TAG)
	kubectl apply -n $(NAMESPACE) -f ./k8s/cron-jobs

to-prod:
	$(MAKE) increment-tag
	$(MAKE) build
	$(MAKE) tag
	$(MAKE) push
	$(MAKE) deploy

deploy-all:
	$(MAKE) deploy
	$(MAKE) update-db
	$(MAKE) deploy-logos

update-db:
	kubectl port-forward svc/$(PG_SERVICE) $(PG_PORT_FORWARD):5432 -n $(PG_NAMESPACE) & \
		echo $$! > .portforward_pid && \
		sleep 5 && \
		cd db && DB_PORT=$(PG_PORT_FORWARD) uv run alembic upgrade head && \
		DB_PORT=$(PG_PORT_FORWARD) uv run scripts/load_team_aliases.py && \
		cat views/*.sql | PGPASSWORD=$(DB_PASSWORD) psql -h localhost -U kube -p $(PG_PORT_FORWARD) -d $(DB_NAME) && \
		cd .. && kill -9 $$(cat .portforward_pid) && rm .portforward_pid

deploy-logos:
	@echo "Waiting for CDN pod to be ready..."
	@kubectl wait --for=condition=ready pod -l app=cdn -n $(NAMESPACE) --timeout=120s
	@CDN_POD=$$(kubectl get pods -l app=cdn -n $(NAMESPACE) -o jsonpath='{.items[0].metadata.name}') && \
		echo "Copying logos to CDN pod: $$CDN_POD" && \
		kubectl cp ./assets/logos $$CDN_POD:/usr/share/nginx/html/ -n $(NAMESPACE)
	@echo "Logos deployed successfully!"

increment-tag:
	@current_tag=$$(grep "^TAG=" .env | cut -d'=' -f2); \
	IFS='.' read -ra VERSION_PARTS <<< "$$current_tag"; \
	patch_version=$${VERSION_PARTS[2]}; \
	new_patch_version=$$((patch_version + 1)); \
	new_tag="$${VERSION_PARTS[0]}.$${VERSION_PARTS[1]}.$$new_patch_version"; \
	sed -i '' "s/^TAG=.*/TAG=$$new_tag/" .env; \
	echo "Tag incremented from $$current_tag to $$new_tag"


