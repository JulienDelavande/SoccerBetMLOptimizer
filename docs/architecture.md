# OptiBet Architecture Overview

## System Architecture

OptiBet follows a microservices architecture designed for scalability, maintainability, and separation of concerns. The system is composed of several specialized services that work together to provide comprehensive soccer betting optimization.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                Internet                                     │
└─────────────────────┬───────────────────────┬───────────────────────────────┘
                      │                       │
                      ▼                       ▼
            ┌─────────────────┐    ┌─────────────────────┐
            │   External APIs │    │     Web Users       │
            │                 │    │                     │
            │  • FBRef        │    │  • Betting Platform │
            │  • SofaIFA      │    │  • Analytics        │
            │  • The Odds API │    │  • Mobile App       │
            └─────────────────┘    └─────────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Load Balancer / API Gateway                     │
└─────────────────────┬───────────────────────┬───────────────────────────────┘
                      │                       │
         ┌────────────┴────────────┐         │
         ▼                         ▼         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Ingestion │    │   App Backend   │    │ ML Pipelines    │
│                 │    │                 │    │                 │
│  • FBRef scraper│◄──►│  • Predictions  │◄──►│ • Model Training│
│  • Odds collector│    │  • Optimization │    │ • Inference     │
│  • Team stats   │    │  • API Gateway  │    │ • Portfolio Opt │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PostgreSQL Database                           │
│                                                                             │
│  • Match Results    • Team Statistics    • Betting Odds    • Models        │
│  • Predictions      • Optimization Results    • Performance Metrics        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
                         ┌─────────────────┐
                         │  App Frontend   │
                         │                 │
                         │  • Streamlit UI │
                         │  • Dashboards   │
                         │  • Analytics    │
                         └─────────────────┘
```

## Core Components

### 1. Data Ingestion Service

**Purpose**: Collect and normalize data from external sources

**Technologies**: 
- FastAPI
- BeautifulSoup (web scraping)
- Requests (API calls)
- SQLAlchemy (database ORM)

**Responsibilities**:
- Scrape match results from FBRef
- Collect team statistics from SofaIFA
- Fetch real-time odds from The Odds API
- Data validation and cleaning
- Database insertion and updates

**Key Features**:
- Caching mechanisms for efficiency
- Error handling and retry logic
- Rate limiting compliance
- Data deduplication

### 2. ML Pipelines Service

**Purpose**: Machine learning model training, inference, and portfolio optimization

**Technologies**:
- FastAPI
- Scikit-learn
- XGBoost
- NumPy/Pandas
- SciPy (optimization)

**Responsibilities**:
- Train predictive models (RSF_PR_LR, etc.)
- Generate match outcome predictions
- Portfolio optimization using Kelly Criterion
- Model performance evaluation
- Feature engineering

**Key Features**:
- Multiple ML algorithms support
- Real-time inference
- Optimization strategies
- Model versioning and tracking

### 3. App Backend Service

**Purpose**: Main API gateway and business logic orchestration

**Technologies**:
- FastAPI
- Pydantic (data validation)
- SQLAlchemy
- Rich (logging)

**Responsibilities**:
- API endpoint orchestration
- Business logic implementation
- Data aggregation and transformation
- Authentication and authorization
- Response formatting

**Key Features**:
- Comprehensive API documentation
- Input validation
- Error handling
- Health monitoring

### 4. App Frontend Service

**Purpose**: User interface and data visualization

**Technologies**:
- Streamlit
- Pandas
- Plotly/Matplotlib (visualizations)

**Responsibilities**:
- Interactive web interface
- Data visualization and dashboards
- User input handling
- Results presentation

**Key Features**:
- Real-time updates
- Interactive charts
- Strategy configuration
- Performance analytics

### 5. Shared Library (optibet_lib)

**Purpose**: Common utilities and models shared across services

**Technologies**:
- Python
- Pydantic
- SQLAlchemy

**Responsibilities**:
- Database models and schemas
- Common utilities and helpers
- Shared business logic
- Configuration management

## Data Flow

### 1. Data Collection Flow

```
External APIs → Data Ingestion → Database → ML Pipelines
     ↓              ↓               ↓            ↓
  Raw Data → Validated Data → Stored Data → Features
```

### 2. Prediction Flow

```
Historical Data → Feature Engineering → ML Model → Predictions
       ↓               ↓                    ↓          ↓
   Database → Preprocessing → Inference → Database
```

### 3. Optimization Flow

```
Predictions + Odds → Portfolio Optimization → Betting Strategy
      ↓                      ↓                      ↓
   Database → Kelly Criterion → Recommended Bets
```

### 4. User Interaction Flow

```
User Request → App Backend → ML Pipelines → Database
     ↓             ↓             ↓            ↓
  Frontend ← API Response ← Results ← Data Retrieval
```

## Deployment Architecture

### Local Development

```
Docker Compose
├── app-backend (Port 8203)
├── app-frontend (Port 8204)
├── data-ingestion (Port 8200)
├── pipelines (Port 8201)
├── postgres (Port 5432)
└── redis (Port 6379) [optional]
```

### Production (Kubernetes)

```
Kubernetes Cluster
├── Namespace: optimsportbets
├── Services:
│   ├── app-backend-svc
│   ├── app-frontend-svc
│   ├── data-ingestion-svc
│   ├── pipelines-svc
│   └── postgresql-svc
├── Deployments:
│   ├── app-backend-deployment
│   ├── app-frontend-deployment
│   ├── data-ingestion-deployment
│   ├── pipelines-deployment
│   └── postgresql-deployment
├── ConfigMaps & Secrets
├── Ingress Controllers
└── Monitoring & Logging
```

## Database Schema

### Core Tables

1. **fbref_results**: Match results and statistics
2. **soccer_odds**: Betting odds from various bookmakers
3. **sofifa_teams_stats**: Team performance statistics
4. **models_results**: ML model predictions
5. **optim_results**: Portfolio optimization results
6. **logs**: Application and system logs

### Relationships

```
Teams ←→ Matches ←→ Odds
  ↓        ↓        ↓
Stats → Predictions → Optimization Results
```

## Security Architecture

### Authentication & Authorization

- API key-based authentication for external services
- Role-based access control (planned)
- Environment-based secrets management

### Data Security

- Database connection encryption
- API communication over HTTPS (production)
- Input validation and sanitization
- Security scanning with Bandit

### Infrastructure Security

- Non-root Docker containers
- Network policies in Kubernetes
- Secret management with Kubernetes secrets
- Regular security updates via Dependabot

## Monitoring & Observability

### Health Checks

- Service-level health endpoints
- Database connectivity checks
- External API availability monitoring

### Logging

- Structured logging with JSON format
- Centralized log aggregation
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging

### Metrics (Planned)

- Application performance metrics
- Business metrics (prediction accuracy, profit/loss)
- Infrastructure metrics (CPU, memory, disk)
- Custom dashboards with Grafana

## Scalability Considerations

### Horizontal Scaling

- Stateless microservices design
- Load balancing between service instances
- Database connection pooling
- Caching strategies

### Performance Optimization

- Database query optimization
- ML model inference caching
- API response caching
- Asynchronous processing for heavy operations

### Resource Management

- Resource limits and requests in Kubernetes
- Auto-scaling based on CPU/memory usage
- Database connection limits
- Rate limiting for external APIs

## Technology Stack Summary

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Streamlit, HTML/CSS, JavaScript |
| **Backend APIs** | FastAPI, Python 3.10+ |
| **ML/Analytics** | Scikit-learn, XGBoost, Pandas, NumPy |
| **Database** | PostgreSQL, SQLAlchemy |
| **Caching** | Redis (optional) |
| **Containerization** | Docker, Docker Compose |
| **Orchestration** | Kubernetes, Helm |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Built-in health checks, structured logging |
| **Security** | Bandit, Dependabot, environment secrets |

## Future Enhancements

### Planned Features

1. **Real-time streaming**: WebSocket support for live updates
2. **Advanced ML**: Deep learning models, ensemble methods
3. **Mobile app**: React Native mobile application
4. **Trading integration**: Direct betting platform integration
5. **Advanced analytics**: Machine learning explainability

### Infrastructure Improvements

1. **Service mesh**: Istio for advanced traffic management
2. **Observability**: Prometheus + Grafana monitoring
3. **Message queues**: Redis/RabbitMQ for async processing
4. **API versioning**: Support for multiple API versions
5. **Multi-region deployment**: Global availability