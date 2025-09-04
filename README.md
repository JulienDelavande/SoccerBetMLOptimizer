# 🏆 OptiBet - Soccer Betting ML Optimizer

> **Intelligent soccer betting optimization using machine learning and real-time data analysis**

[![CI/CD Pipeline](https://github.com/JulienDelavande/SoccerBetMLOptimizer/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/JulienDelavande/SoccerBetMLOptimizer/actions/workflows/ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-green.svg)](https://kubernetes.io/)

## 🎯 Overview

OptiBet is a comprehensive machine learning platform that optimizes soccer betting strategies using:

- **Real-time data ingestion** from multiple sources (FBRef, SofaIFA, The Odds API)
- **Advanced ML models** for match outcome prediction
- **Portfolio optimization** using Kelly Criterion and modern portfolio theory
- **Interactive web interface** for strategy visualization and execution
- **Microservices architecture** for scalability and maintainability

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Data Ingestion │    │    Database     │
│                 │───▶│                  │───▶│   PostgreSQL    │
│ FBRef, SofaIFA  │    │    FastAPI       │    │                 │
│ The Odds API    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
┌─────────────────┐    ┌──────────────────┐              │
│   Frontend UI   │    │   App Backend    │              │
│                 │◀──▶│                  │◀─────────────┘
│   Streamlit     │    │    FastAPI       │
│                 │    │                  │
└─────────────────┘    └──────────────────┘
                                 │
                       ┌──────────────────┐
                       │   ML Pipelines   │
                       │                  │
                       │    FastAPI       │
                       │                  │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- Docker & Docker Compose (optional)
- Make

### 🔧 Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/JulienDelavande/SoccerBetMLOptimizer.git
   cd SoccerBetMLOptimizer
   ```

2. **Setup environment**
   ```bash
   # Quick setup with our development script
   ./dev.sh setup
   
   # Or manual setup
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **Configure secrets**
   ```bash
   cp secrets_template.env secrets.env
   # Edit secrets.env with your API keys and database credentials
   ```

4. **Setup database**
   ```bash
   # Create PostgreSQL database
   createdb optimsportbets-db
   
   # Apply migrations
   cd db
   python apply_migrations.py
   ```

5. **Start development environment**
   ```bash
   ./dev.sh start
   ```

6. **Access the application**
   - Frontend: http://localhost:8204
   - Backend API: http://localhost:8203/docs
   - Data Ingestion API: http://localhost:8200/docs

### 🐳 Docker Development

```bash
# Build and start all services
docker-compose up --build

# Or use make commands
make build
make up
```

## 📁 Project Structure

```
SoccerBetMLOptimizer/
├── 🎨 app-frontend/          # Streamlit web interface
├── ⚙️  app-backend/          # Main FastAPI backend
├── 📊 data-ingestion/        # Data collection microservice
├── 🤖 pipelines/             # ML inference pipelines
├── 📚 optibet_lib/           # Shared Python library
├── 🗄️  db/                   # Database schema & migrations
├── ☸️  k8s/                  # Kubernetes deployments
├── 📓 notebooks/             # Jupyter notebooks for analysis
├── 📖 doc/                   # Documentation
├── 🔧 .github/               # CI/CD workflows
├── 🐳 compose.yml            # Docker Compose configuration
└── 📋 requirements*.txt      # Python dependencies
```

## 🛠️ Development Workflow

### Code Quality & Testing

```bash
# Run all code quality checks
./dev.sh check

# Individual commands
./dev.sh format    # Format code with Black & isort
./dev.sh lint      # Run flake8, mypy, bandit
./dev.sh test      # Run pytest suite
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks (included in setup)
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 🎮 Usage Examples

### Computing Optimal Betting Strategy

```python
import requests

# Get predictions for upcoming matches
response = requests.get(
    "http://localhost:8203/compute/predictions",
    params={
        "datetime_first_match": "2024-01-15 00:00:00",
        "n_matches": 10,
        "bookmakers": "betclic,unibet_eu",
        "bankroll": 1.0,
        "method": "SLSQP",
        "utility_fn": "Kelly"
    }
)

predictions = response.json()
```

### Data Ingestion

```python
# Ingest latest match results
response = requests.get(
    "http://localhost:8200/fbref",
    params={"get_current_season_only": True}
)

# Ingest latest odds
response = requests.get("http://localhost:8200/the_odds_api/odds")
```

## 🚀 Deployment

### Kubernetes (Production)

1. **Setup infrastructure**
   ```bash
   # Azure (example)
   az aks create --resource-group OptimSportBets --name optimsportbets
   az aks get-credentials --resource-group OptimSportBets --name optimsportbets
   ```

2. **Deploy application**
   ```bash
   kubectl create namespace optimsportbets
   kubectl apply -f k8s/helm-deploy/secrets/
   helm install optimsportbets k8s/helm-deploy/optimsportbets/
   ```

3. **Build and push images**
   ```bash
   make build
   make tag
   make push
   ```

### Docker Compose (Staging)

```bash
export $(grep -v '^#' .env)
export $(grep -v '^#' compose.env)
docker-compose -f compose.yml up -d
```

## 📊 API Documentation

Each service provides interactive API documentation:

- **App Backend**: http://localhost:8203/docs
- **Data Ingestion**: http://localhost:8200/docs
- **ML Pipelines**: http://localhost:8201/docs

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_NAME=optimsportbets-db

# API Keys
THE_ODDS_API_KEY=your_api_key

# Services
APP_BACKEND_PORT=8203
APP_FRONTEND_PORT=8204
DATA_INGESTION_PORT=8200
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and run tests: `./dev.sh check`
4. Commit with conventional commits: `git commit -m "feat: add amazing feature"`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide (enforced by Black)
- Write tests for new features
- Update documentation
- Use type hints
- Keep commits atomic and well-described

## 📈 Performance & Monitoring

### Health Checks

All services provide health check endpoints:

```bash
curl http://localhost:8203/health
curl http://localhost:8200/health
```

### Metrics

Monitor application performance:
- Response times
- Database query performance
- ML model inference time
- Betting strategy performance

## 🔒 Security

- Secrets management via environment variables
- CORS configuration
- Input validation and sanitization
- Security scanning with Bandit
- Dependency vulnerability scanning

## 📚 Documentation

- [Architecture Overview](doc/architecture.md)
- [API Reference](doc/api-reference.md)
- [Deployment Guide](doc/deployment.md)
- [Development Setup](doc/development.md)

## 🐛 Troubleshooting

### Common Issues

1. **Database connection errors**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # Verify connection
   psql -h localhost -U postgres -d optimsportbets-db
   ```

2. **Port conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8203
   
   # Change ports in .env file
   ```

3. **API key issues**
   ```bash
   # Verify your API key is set
   echo $THE_ODDS_API_KEY
   ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Master's thesis work by Julien Delavande (SUPAERO)
- Data sources: FBRef, SofaIFA, The Odds API
- Built with FastAPI, Streamlit, PostgreSQL, and Kubernetes

## 📞 Support

- 📧 Email: julien.delavande@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/JulienDelavande/SoccerBetMLOptimizer/issues)
- 📖 Wiki: [Project Wiki](https://github.com/JulienDelavande/SoccerBetMLOptimizer/wiki)

---

**⚠️ Disclaimer**: This software is for educational and research purposes. Please gamble responsibly and in accordance with local laws and regulations.









