# Deployment Guide

This guide covers all deployment options for OptiBet, from local development to production Kubernetes clusters.

## Prerequisites

### Software Requirements

- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Python** (3.10+)
- **PostgreSQL** (12+)
- **Git**
- **Make**

### For Kubernetes Deployment

- **kubectl** (compatible with your cluster version)
- **Helm** (v3.0+)
- **Azure CLI** (if using Azure)

### For CI/CD

- **GitHub account** with Actions enabled
- **Container registry** (Docker Hub, Azure ACR, etc.)

## Local Development Deployment

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/JulienDelavande/SoccerBetMLOptimizer.git
   cd SoccerBetMLOptimizer
   ./dev.sh setup
   ```

2. **Configure secrets**:
   ```bash
   cp secrets_template.env secrets.env
   # Edit secrets.env with your API keys
   ```

3. **Start services**:
   ```bash
   ./dev.sh start
   ```

### Manual Setup

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **Setup database**:
   ```bash
   # Install PostgreSQL if not already installed
   createdb optimsportbets-db
   cd db
   python apply_migrations.py
   ```

4. **Start services individually**:
   ```bash
   # Terminal 1 - Data Ingestion
   cd data-ingestion
   uvicorn main:app --port 8200 --reload
   
   # Terminal 2 - ML Pipelines
   cd pipelines
   uvicorn main:app --port 8201 --reload
   
   # Terminal 3 - App Backend
   cd app-backend
   uvicorn main:app --port 8203 --reload
   
   # Terminal 4 - App Frontend
   cd app-frontend
   streamlit run main.py --server.port 8204
   ```

### Makefile Commands

```bash
# Setup development environment
make dev-setup

# Start all services
make dev-start

# Stop all services
make dev-stop

# Run tests
make dev-test

# Format code
make dev-format

# Run linting
make dev-lint

# Run all checks
make dev-check
```

## Docker Development Deployment

### Using Docker Compose

1. **Build and start**:
   ```bash
   docker-compose -f compose.yml -f compose.override.yml up --build
   ```

2. **Individual service build**:
   ```bash
   # Build specific service
   docker-compose build app-backend
   
   # Start specific service
   docker-compose up app-backend
   ```

3. **View logs**:
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f app-backend
   ```

4. **Stop services**:
   ```bash
   docker-compose down
   
   # Remove volumes too
   docker-compose down -v
   ```

### Production Docker Compose

```bash
# Production deployment (no override)
export $(grep -v '^#' .env)
export $(grep -v '^#' compose.env)
docker-compose -f compose.yml up -d
```

## Kubernetes Deployment

### Azure Kubernetes Service (AKS)

#### 1. Setup Azure Resources

```bash
# Login to Azure
az login

# Create resource group
az group create --name OptimSportBets --location westeurope

# Create container registry
az acr create --resource-group OptimSportBets --name optimsportbets --sku Basic

# Create AKS cluster
az aks create \
  --resource-group OptimSportBets \
  --name optimsportbets \
  --node-count 3 \
  --generate-ssh-keys \
  --attach-acr optimsportbets

# Get credentials
az aks get-credentials --resource-group OptimSportBets --name optimsportbets
```

#### 2. Build and Push Images

```bash
# Build images for Linux/AMD64
make build-mac  # or make build

# Tag images for registry
make tag

# Push to registry
make push
```

#### 3. Configure Secrets

Create secret files in `k8s/helm-deploy/secrets/`:

**api-keys-secrets.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys-secrets
  namespace: optimsportbets
data:
  theOddsApiKey: <base64-encoded-api-key>
```

**db-credentials-secrets.yaml**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials-secrets
  namespace: optimsportbets
data:
  admin-password: <base64-encoded-password>
  user-password: <base64-encoded-password>
```

**cr-secrets.yaml** (if using private registry):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cr-secret
  namespace: optimsportbets
  type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

#### 4. Deploy Application

```bash
# Create namespace
kubectl create namespace optimsportbets
kubectl config set-context --current --namespace=optimsportbets

# Deploy secrets
kubectl apply -f ./k8s/helm-deploy/secrets/

# Deploy with Helm
helm install optimsportbets ./k8s/helm-deploy/optimsportbets/ \
  -f ./k8s/helm-deploy/optimsportbets/values.yaml \
  --namespace optimsportbets

# Deploy cron jobs
kubectl apply -R -f ./k8s/helm-deploy/cron-jobs
```

### Generic Kubernetes Cluster

For non-Azure Kubernetes clusters:

1. **Configure registry**:
   ```bash
   # Update values.yaml with your registry
   containerRegistry:
     registry: your-registry.com
   ```

2. **Deploy**:
   ```bash
   # Use the make target
   make deploy
   ```

### Helm Configuration

Key configuration options in `values.yaml`:

```yaml
# Container registry settings
containerRegistry:
  registry: optimsportbets.azurecr.io
  enabled: true

# Service configurations
appBackend:
  image: optim-sportbet-app-backend
  tag: "1.57"
  replicas: 2

appFrontend:
  image: optim-sportbet-app-frontend
  tag: "1.57"
  replicas: 1

dataIngestion:
  image: optim-sportbet-data-ingestion
  tag: "1.57"
  replicas: 1

pipelines:
  image: optim-sportbet-pipelines
  tag: "1.57"
  replicas: 1

# Database settings
postgresql:
  enabled: true
  persistence:
    size: 20Gi
```

## Production Deployment Best Practices

### Environment Configuration

#### Production Environment Variables

```bash
# .env.production
TAG=v1.0.0
CONTAINER_REGISTRY=your-registry.com
IMAGE_PREFIX=optibet

# Database
DB_HOST=postgresql-global
DB_PORT=5432
DB_NAME=optimsportbets-db

# Security
CORS_ORIGINS=https://your-domain.com
```

#### Secrets Management

1. **Kubernetes Secrets**:
   ```bash
   kubectl create secret generic api-keys \
     --from-literal=odds-api-key=your-key \
     --namespace optimsportbets
   ```

2. **Azure Key Vault** (recommended):
   ```bash
   # Install CSI driver
   helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
   helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver --namespace kube-system
   ```

### Database Deployment

#### Managed Database (Recommended)

```bash
# Azure Database for PostgreSQL
az postgres server create \
  --resource-group OptimSportBets \
  --name optimsportbets-db \
  --admin-user postgres \
  --admin-password <secure-password> \
  --sku-name GP_Gen5_2
```

#### Self-hosted Database

```yaml
# postgresql-production.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  serviceName: postgresql
  replicas: 1
  template:
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: optimsportbets-db
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 50Gi
```

### Monitoring and Logging

#### Health Checks

```yaml
# Health check configuration
livenessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5
```

#### Logging

```yaml
# Logging configuration
logging:
  level: INFO
  format: json
  destination: stdout
```

### Scaling Configuration

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## CI/CD Pipeline

### GitHub Actions

The repository includes a comprehensive CI/CD pipeline in `.github/workflows/ci-cd.yml`:

#### Pipeline Stages

1. **Code Quality**: Linting, formatting, type checking
2. **Testing**: Unit and integration tests
3. **Security**: Security scanning with Bandit
4. **Build**: Docker image building
5. **Deploy**: Automated deployment to staging/production

#### Environment Setup

```bash
# GitHub Secrets required
CONTAINER_REGISTRY_URL
CONTAINER_REGISTRY_USERNAME
CONTAINER_REGISTRY_PASSWORD
KUBE_CONFIG  # Base64 encoded kubeconfig
THE_ODDS_API_KEY
DB_PASSWORD
```

#### Manual Deployment

```bash
# Trigger deployment
git tag v1.0.1
git push origin v1.0.1

# Or manual workflow dispatch
gh workflow run ci-cd.yml -f environment=production
```

## Verification and Testing

### Service Health Checks

```bash
# Check all services
kubectl get pods -n optimsportbets

# Check service endpoints
kubectl get svc -n optimsportbets

# Test health endpoints
curl http://your-domain/api/backend/health
curl http://your-domain/api/ingestion/health
curl http://your-domain/api/pipelines/health
```

### Database Connection

```bash
# Port forward to database
kubectl port-forward svc/postgresql-global 5432:5432 -n optimsportbets

# Connect to database
psql -h localhost -U postgres -d optimsportbets-db
```

### Load Testing

```bash
# Install tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://your-domain
```

## Troubleshooting

### Common Issues

#### Pod Startup Issues

```bash
# Check pod logs
kubectl logs -f deployment/app-backend -n optimsportbets

# Check events
kubectl get events -n optimsportbets --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n optimsportbets
```

#### Database Connection Issues

```bash
# Check database pod
kubectl logs -f deployment/postgresql -n optimsportbets

# Test connection
kubectl exec -it deployment/app-backend -n optimsportbets -- \
  python -c "import psycopg2; print('DB connection OK')"
```

#### Image Pull Issues

```bash
# Check registry credentials
kubectl get secret cr-secret -n optimsportbets -o yaml

# Test image pull
docker pull optimsportbets.azurecr.io/optim-sportbet-app-backend:latest
```

### Performance Tuning

#### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Optimize common queries
CREATE INDEX idx_match_date ON fbref_results(date_match);
CREATE INDEX idx_odds_bookmaker ON soccer_odds(bookmaker_key);
```

#### Application Optimization

```python
# Enable connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0
)
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
kubectl create job backup-$(date +%Y%m%d) \
  --from=cronjob/postgres-backup \
  -n optimsportbets
```

### Disaster Recovery

```bash
# Restore from backup
kubectl apply -f k8s/disaster-recovery/restore-job.yaml
```

## Security Considerations

### Network Security

```yaml
# Network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-backend-netpol
spec:
  podSelector:
    matchLabels:
      app: app-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: app-frontend
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
```

### Secret Rotation

```bash
# Update API key
kubectl patch secret api-keys-secrets \
  -p='{"data":{"theOddsApiKey":"<new-base64-key>"}}' \
  -n optimsportbets

# Restart deployments to pick up new secrets
kubectl rollout restart deployment/data-ingestion -n optimsportbets
```

This deployment guide covers all major scenarios from development to production. Choose the deployment method that best fits your infrastructure and requirements.