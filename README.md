# Optim-sportbet

## Description

This project aims to deliver day to day prediction on what to bet on sport games.

## Installation

There is 3 ways to install the project:

1. Local installation
2. Docker installation
3. Kubernetes installation

### Local installation

To install the project locally, you need to have the following dependencies installed on your machine:

- Python 3.10
- make

First replace the `secrets_template.env` file with your own secrets and rename it to `secrets.env`.

```bash	
echo secrets_template.env > secrets.env
```

Then you can install the project by running the following command:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

```bash
make start
```

To stop the project, you can run the following command:

```bash
make stop
```

### Docker installation

To install the project with Docker, you need to have the following dependencies installed on your machine:

- Docker
- Docker Compose

First replace the `secrets_template.env` file with your own secrets and rename it to `secrets.env`.

```bash
echo secrets_template.env > secrets.env
```

Then you can install the project by running the following command:

```bash
docker compose --env-file .env --env-file compose.env -f compose.yml up
```

If you want airflow to be installed, you can run the following command:

```bash
docker compose --env-file .env --env-file compose.env -f compose.yml -f airflow.yml up
```

To stop the project, you can run the following command:

```bash
docker compose down
```

### Kubernetes installation

To install the project with Kubernetes, you need to have access to a Kubernetes cluster.
You need to have the following dependencies installed on your machine:

- kubectl
- helm
- Docker
- Docker Compose
- make

#### Creation of all needed services using Azure

You need to have the following dependencies installed on your machine:

- Azure CLI

```bash
az login
```

A resource group, named `Optim-sportBets`, has been created on Azure, with all the services needed for the project. You can either use the existing resource group and the ressources if still available, or create your own.

Within the ressource group, you will find the following services:
- Azure Kubernetes Service (AKS) [existing name: `optimsportbets`]
- Azure Container Registry (ACR) [existing name: `optimsportbets`]
- Azure Database for PostgreSQL server [existing name: `soccerodds-psql-db`]

As well as remote repositories on Azure DevOps for the project's code [existing name: `optim-sportbet`].

Create a resource group on Azure if you need by running the following command:

```bash
az group create --name <resource-group> --location <location>
```

##### Create an AKS cluster

To create an AKS cluster on Azure, you can run the following command:


```bash
az aks create --resource-group <resource-group> --name <cluster-name> --node-count 2 --generate-ssh-keys
```

Then you can get the credentials of the cluster by running the following command:

```bash
az aks get-credentials --resource-group <resource-group> --name <cluster-name>
```

##### Create a ACR registry on Azure

To create an ACR registry on Azure, you can run the following command:

```bash
az acr create --resource-group <resource-group> --name <registry-name> --sku Basic
```

Then you can get the credentials of the registry by running the following command:

```bash
az acr login --name <registry-name>
```

##### Create a PostgreSQL server on Azure

To create a PostgreSQL server on Azure, you can run the following command:

```bash
az postgres server create --resource-group <resource-group> --name <server-name> --location <location> --admin-user <admin-user> --admin-password <admin-password> --sku-name B_Gen5_1 --version 12 --ssl-enforcement Enabled
```

Then you can create a database by running the following command:

```bash
az postgres db create --resource-group <resource-group> --server-name <server-name> --name <database-name>
```

Then you need to apply the migrations (set the structure of the db) by running the following command:

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
cd db
python apply_migrations.py
```

### Configure the secrets

Modify the secrets files in k8s/secrets/ with your own secrets.

#### k8s/secrets_template/acr_secret.yaml

Modify the `.dockerconfigjson` fields with the credentials of a user that has access to the ACR registry.
For example the admin of the ACR registry. You can get the credentials by running the following command:

```bash
az acr credential show --name <registry-name>
```

Then you can encode the credentials by running the following command:

```bash
cat .dockerconfigjson | base64  
```
Put the results in the acr_secret.yaml file.

#### k8s/secrets_template/airflow-azure-devops-secrets.yaml

Modify the `GIT_SYNC_USERNAME` and `GIT_SYNC_PASSWORD` fields with the credentials of a user that has access to the repository.
You can a azure service principal to access the repository in the repo configuration.
For example the service principal named `gitalcicd` from the Azure subscription has full access to the repository. Don't forget to encode the credentials.

```bash
echo -n <username> | base64
```

```bash
echo -n <password> | base64
```

Put the results in the airflow-azure-devops-secrets file. The `GITSYNC_USERNAME` and `GITSYNC_PASSWORD` should be the same as the `GIT_SYNC_USERNAME` and `GIT_SYNC_PASSWORD`.

#### k8s/secrets_template/secrets.yaml

Modify the `DB_PASSWORD` field with the password of the database. Don't forget to encode the password.

```bash
echo -n <password> | base64
```

Modify the `THE_ODDS_API_KEY` field with the API key accessof the Odds API website (you can create an account here https://the-odds-api.com/ the free tier is sufficiant). Don't forget to encode the API key.

```bash
echo -n <api> | base64
```

Put the results in the secrets.yaml file.

### Configure the environment variables

If you chose to create your own ressources, you need to modify things in the following files:
- k8s/config-map/config-map.yaml
- k8s/deployments/*

#### You created your own database

Modify the `DB_HOST`, `DB_NAME`, `DB_USER` fields with the information of your database in the config-map.yaml file.

#### You created your own ACR registry

Modify the name of the image in the deployments files.

### Build, tag and push the Docker images

To build, tag and push the Docker images to the ACR registry, you can run the following command:

```bash
make build
```

```bash
make tag
```

```bash
make push
```

If you created your own container registry, you need to modify the `CONTAINER_REGISTRY` field in Makefile with the name of your ACR registry before running the commands.

### Deploy the project

To deploy the project on Kubernetes, you can run the following command:

```bash
kubectl apply -f k8s/
```

Then to deploy Airflow pods using helm, you can run the following command:

```bash
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow -f k8s/airflow-values.yaml
```

### Access the services

#### App-frontend

To access the frontend, you can run the following command:

```bash
kubectl port-forward svc/frontend 8204:80
```

Then you can access the frontend by going to http://localhost:8204.

#### Airflow

To access the Airflow UI, you can run the following command:

```bash
kubectl port-forward svc/airflow-webserver 8205:8080
```

Then you can access the Airflow UI by going to http://localhost:8205.

#### Mlflow

To access the Mlflow UI, you can run the following command:

```bash
kubectl port-forward svc/mlflow-service 8202:80
```

Then you can access the Mlflow UI by going to http://localhost:8202.


#### Backends

To access the fast api doc of the backends, you can run the following command:

```bash
kubectl port-forward svc/app-backend-service 8203:80
```
    
```bash
kubectl port-forward svc/data-ingestion-service 8200:80
```

```bash
kubectl port-forward svc/pipelines-service 8201:80
```

Then you can access the fast api doc by going to http://localhost:8203/docs, http://localhost:8200/docs and http://localhost:8201/docs.

#### Postgres

To access the PostgreSQL database, you can run the following command:

```bash
psql --host=<server-name>.postgres.database.azure.com --port=5432 --username=<admin-user>@<server-name> --dbname=<database-name> --sslmode=require
```

Then you can access the database by running SQL queries.









