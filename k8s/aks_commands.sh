# Login to Azure
az login 

# Create Azure Container Registry
az acr create \ 
    --resource-group Optim-SportBets \
    --name optimsportbets \
    --sku Basic 

# Create Azure Kubernetes Service (problem with vm scale set due to policy, use AvailabilitySet)
az aks create \
    --resource-group Optim-SportBets \
    --name optimsportbets \
    --node-count 1 \
    --vm-set-type AvailabilitySet \
    --generate-ssh-keys \
    --location eastus

# Scale AKS to 2 nodes
az aks scale \
    --resource-group Optim-SportBets \
    --name optimsportbets \
    --node-count 2 \
    --nodepool-name nodepool1


# Get credentials for kubectl (local)
az aks get-credentials \
    --name optimsportbets \
    --resource-group Optim-SportBets



# Attach ACR to AKS - Ne fonctionne pas car pas contributeur sur la subscription
az aks update \
    --resource-group Optim-SportBets \
    --name optimsportbets \
    --attach-acr optimsportbets

# alternative - regénérer les credentials et créer un secret kube
az acr login --name optimsportbets
az acr update --name optimsportbets --admin-enabled true
az acr credential show --name optimsportbets -o table

# Connect tag push image to ACR
az acr login --name optimsportbets
docker tag optim-sportbet-pipelines:latest optimsportbets.azurecr.io/optim-sportbet-pipelines:1.0
docker push optimsportbets.azurecr.io/optim-sportbet-pipelines:1.0
az acr repository list --name optimsportbets --output table

# Create aks deployment
kubectl apply -f k8s/deployment.yaml
kubectl apply -R -f k8s/manifests/
kubectl get pods
kubectl logs <pod-name>
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- /bin/bash

# Install Airflow
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow -f airflow-values.yaml 

# se connecter à airflow  webserver cluster ip
kubectl port-forward svc/airflow-webserver 8102:8080 --namespace default

ssh-keygen -t rsa -b 4096 -C "airflow-kube@headmind.com" -f airflow_kube_ssh_key

az ad sp create-for-rbac --name OptimSB-ContributorApp --role Contributor --scopes /subscriptions/dc0686fc-bdbf-4f78-9f07-ec7bd5755e35/resourceGroups/Optim-SportBets --query "{clientId:appId, clientSecret:password, tenantId:tenant}"
az ad sp create-for-rbac --name ACR-OptimSB-ContributorApp --scopes $(az acr show --name optimsportbets --query id --output tsv) --role acrpull --query "{clientId:appId, clientSecret:password, tenantId:tenant}"
az ad sp create-for-rbac --name OptimSB-service-principal --role Contributor --scopes /subscriptions/dc0686fc-bdbf-4f78-9f07-ec7bd5755e35/resourceGroups/Optim-SportBets