# API Reference

## Overview

OptiBet provides a comprehensive REST API for soccer betting optimization using machine learning. The API is divided into several microservices, each handling specific aspects of the betting optimization pipeline.

## Services

### 1. App Backend (`/api/backend`)

The main API service for computing predictions and retrieving results.

**Base URL**: `http://localhost:8203`

#### Endpoints

##### Health Check
- **GET** `/health`
- **Description**: Health check endpoint for monitoring
- **Response**: Service status and version information

##### Compute Predictions
- **GET** `/compute/predictions`
- **Description**: Compute optimized betting predictions using ML models
- **Parameters**:
  - `datetime_first_match` (optional): Starting datetime (YYYY-MM-DD HH:MM:SS)
  - `n_matches` (optional): Number of matches to analyze (1-100)
  - `bookmakers` (optional): Comma-separated bookmaker list
  - `bankroll` (optional): Bankroll amount (0.01-1000000)
  - `method` (optional): Optimization method (SLSQP, COBYLA, trust-constr)
  - `utility_fn` (optional): Utility function (Kelly)
  - `same_day` (optional): Only same-day matches (boolean)

##### Fetch Last Predictions
- **GET** `/fetch/last_predictions`
- **Description**: Get latest betting recommendations
- **Parameters**:
  - `optim_label`: Optimization strategy label
  - `datetime_optim_last`: Last optimization datetime filter

##### Fetch Past Performances
- **GET** `/fetch/past_performances`
- **Description**: Retrieve historical betting performance
- **Parameters**:
  - `optim_label`: Strategy label to filter
  - `datetime_first_match`: Performance period start
  - `datetime_last_match`: Performance period end

##### Fetch Performance Gains
- **GET** `/fetch/past_performances_gains`
- **Description**: Get cumulative gains over time
- **Parameters**:
  - `optim_label`: Strategy label
  - `datetime_first_match`: Start date for gains
  - `datetime_last_match`: End date for gains
  - `divisor`: Risk adjustment divisor (1-10)

### 2. Data Ingestion (`/api/ingestion`)

Microservice for data collection from external sources.

**Base URL**: `http://localhost:8200`

#### Endpoints

##### Health Check
- **GET** `/health`
- **Description**: Service health status

##### FBRef Data Ingestion
- **GET** `/fbref`
- **Description**: Ingest match results from FBRef
- **Parameters**:
  - `get_current_season_only`: Current season only (boolean)
  - `use_cache`: Use cached data (boolean)
  - `cutoff_days`: Data cutoff in days (integer)

##### SofaIFA Team Stats
- **GET** `/sofifa/team_stats`
- **Description**: Ingest team statistics from SofaIFA
- **Parameters**:
  - `use_cache`: Use cached data (boolean)
  - `scrap_all`: Scrape all data (boolean)

##### Odds API Data
- **GET** `/the_odds_api/odds`
- **Description**: Ingest odds from The Odds API
- **Authentication**: Requires `THE_ODDS_API_KEY` environment variable

### 3. ML Pipelines (`/api/pipelines`)

Machine learning inference and optimization pipelines.

**Base URL**: `http://localhost:8201`

#### Endpoints

##### Health Check
- **GET** `/health`
- **Description**: Service health status

##### ML Inference
- **GET** `/infer/RSF_PR_LR`
- **Description**: Run RSF_PR_LR model inference
- **Parameters**:
  - `date_stop`: Stop date for inference (YYYY-MM-DD HH:MM:SS)

##### Portfolio Optimization
- **GET** `/optim`
- **Description**: Optimize betting portfolio
- **Parameters**:
  - `datetime_first_match`: First match datetime
  - `model`: ML model to use (default: RSF_PR_LR)
  - `n_matches`: Number of matches
  - `same_day`: Same day optimization (boolean)
  - `bookmakers`: Bookmaker list
  - `bankroll`: Bankroll amount
  - `method`: Optimization method
  - `utility_fn`: Utility function
  - `optim_label`: Optimization label

## Authentication

Currently, the API doesn't require authentication for most endpoints. However, some data sources require API keys:

- **The Odds API**: Set `THE_ODDS_API_KEY` environment variable
- **Database Access**: Configure database credentials in environment

## Rate Limits

- Standard endpoints: 100 requests/minute
- Compute-intensive endpoints: 10 requests/minute
- Data ingestion endpoints: 20 requests/minute

## Error Handling

All endpoints return standardized error responses:

```json
{
  "status": "error",
  "error": "Error message",
  "details": "Detailed error information"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error
- `503`: Service Unavailable

## Examples

### Compute Predictions Example

```bash
curl -X GET "http://localhost:8203/compute/predictions" \
  -G \
  -d "datetime_first_match=2024-01-15 00:00:00" \
  -d "n_matches=5" \
  -d "bookmakers=betclic,unibet_eu" \
  -d "bankroll=100" \
  -d "method=SLSQP"
```

### Fetch Latest Predictions Example

```bash
curl -X GET "http://localhost:8203/fetch/last_predictions" \
  -G \
  -d "optim_label=auto_regular"
```

### Data Ingestion Example

```bash
curl -X GET "http://localhost:8200/fbref" \
  -G \
  -d "get_current_season_only=true" \
  -d "use_cache=false"
```

## SDKs and Libraries

### Python SDK

```python
import requests

class OptiBetClient:
    def __init__(self, base_url="http://localhost:8203"):
        self.base_url = base_url
    
    def compute_predictions(self, **kwargs):
        response = requests.get(f"{self.base_url}/compute/predictions", params=kwargs)
        return response.json()
    
    def fetch_last_predictions(self, optim_label="manual"):
        response = requests.get(f"{self.base_url}/fetch/last_predictions", 
                               params={"optim_label": optim_label})
        return response.json()

# Usage
client = OptiBetClient()
predictions = client.compute_predictions(n_matches=10, bankroll=100)
```

## Interactive Documentation

Each service provides interactive API documentation:

- **App Backend**: http://localhost:8203/docs
- **Data Ingestion**: http://localhost:8200/docs
- **ML Pipelines**: http://localhost:8201/docs

These Swagger/OpenAPI interfaces allow you to test endpoints directly in your browser.