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
export $(grep -v '^#' .env)
export $(grep -v '^#' compose.env)
docker compose --env-file .env --env-file compose.env -f compose.yml up
```

If you want airflow to be installed, you can run the following command:

```bash
export $(grep -v '^#' .env)
export $(grep -v '^#' compose.env)
docker compose -f compose.yml -f airflow.yml up
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

As well as remote repositories on Azure DevOps for the project's code [existing name: `optim-sportbet`].

Create a resource group on Azure if you need by running the following command:

```bash
az group create --name <resource-group> --location <location>
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

##### Create an AKS cluster

To create an AKS cluster on Azure, you can run the following command:


```bash
az aks create --resource-group <resource-group> --name <cluster-name> --node-count 2 --generate-ssh-keys
```

Then you can get the credentials of the cluster by running the following command:

```bash
az aks get-credentials --resource-group <resource-group> --name <cluster-name>
```

### Configure the secrets

Get the three folowing secrets files and put then in k8s/helm-deploy/secrets:
- api-keys-secrets.yaml : The odds api key to scrapp odds from the-odds-api.com
```yaml	
apiVersion: v1
kind: Secret
metadata:
  name: api-keys-secrets
  namespace: optimsportbets
data:
  theOddsApiKey: <base64-encoded-theOddsApiKey> # Get the api key from https://the-odds-api.com/ and encode it in base64
```
- cr-secrets.yaml : The credentials of the CR registry if the container registry is private - if public, you can remove this file and put containerRegistry.enabled to false in values.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
    name: cr-secret
    namespace: optimsportbets
    type: kubernetes.io/dockerconfigjson
data:
    .dockerconfigjson: <base64-encoded-.dockerconfigjson> # Get the credentials of the ACR registry by running the command az acr login --name <registry-name> and encode it in base64, the dockerconfigjson is the output of the command az acr login --name <registry-name> encoded in base64
```
- db-credentials-secrets.yaml
```yaml
apiVersion: v1
kind: Secret
metadata:
    name: db-credentials-secrets
    namespace: optimsportbets
data:
    admin-password: <base64-encoded-admin-password> # the admin password of the postgres database encoded in base64 - you can choose the password you want
    user-password: <base64-encoded-user-password> # the user password of the postgres database encoded in base64 - you can choose the password you want
```

Make sure the secrets are correctly configured with the right credentials.

#### You created your own ACR registry

If you created your own ACR registry, you need to modify the `values.yaml` file in `k8s/helm-deploy/optimsportbets` with the name of your ACR registry:
```yaml
containerRegistry:
    registry: <your-acr-registry>.azurecr.io
```

If the name and tag of the images new, you also need to modify the `values.yaml` file in `k8s/helm-deploy/optimsportbets` with the name and tag of the images:
```yaml
appFrontend: # Do the same for the other services
    image: <name-of-your-image-on-your-container-registry>
    tag: <tag-of-your-image-on-your-container-registry>
```
### Build, tag and push the Docker images

To build, tag and push the Docker images to the ACR registry, you can run the following command:

```bash
docker compose build
```

```bash
make tag
```

```bash
make push
```

If you created your own container registry, you need to modify the `CONTAINER_REGISTRY` field in Makefile with the name of your ACR registry before running the commands.

### Deploy the project

To deploy the project on Kubernetes, you can run the following commands from the root of the project:

```bash
# Create the namespace and switch to it
kubectl create namespace optimsportbets
kubectl config set-context --current --namespace=optimsportbets

# Deploy the secrets the helm chart of the project and the cron jobs
kubectl apply -f ./k8s/helm-deploy/secrets/
helm install optimsportbets ./k8s/helm-deploy/optimsportbets/ -f ./k8s/helm-deploy/optimsportbets/values.yaml --namespace optimsportbets
kubectl apply -R -f ./k8s/helm-deploy/cron-jobs
```


### Access the services

To list the pods, services, secret and cronjobs you can run the following command:

```bash
kubectl get pods -n optimsportbets
kubectl get svc -n optimsportbets
kubectl get secret -n optimsportbets
kubectl get cronjobs -n optimsportbets
```

You can port-forward the services to access them locally:

```bash
kubectl port-forward svc/<name-of-the-service> <local-port>:<kube-port> -n optimsportbets
# Example to have the frontend on localhost:8080 `http://localhost:8080`.
kubectl port-forward svc/app-frontend-svc 8080:8104 -n optimsportbets
```









