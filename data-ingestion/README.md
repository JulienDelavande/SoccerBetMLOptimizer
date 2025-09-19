# Data Ingestion Service

## Overview

Microservice for ingesting football data into a PostgreSQL database with support for both synchronous and asynchronous (background) task execution.

## Project Structure

```
data-ingestion/
├── main.py                    # FastAPI application entry point
├── app/
│   ├── __init__.py
│   ├── _config.py            # Configuration and logging setup
│   ├── models.py             # Pydantic models for requests/responses
│   ├── background_tasks.py   # Background task functions
│   ├── utils.py              # Utility functions for formatting and messages
│   ├── insert_data/          # Data insertion modules
│   └── ...
├── test_background_tasks.py  # Test script for API endpoints
└── README.md
```

## Background Tasks Feature

All data ingestion endpoints now support an optional `run_in_background` parameter that allows you to choose between:

- **Synchronous execution** (default): The API waits for the task to complete and returns detailed results
- **Background execution**: The API immediately returns and the task runs in the background

### Code Organization

The codebase is organized into separate modules for better maintainability:

- **`app/background_tasks.py`**: Contains all background task functions with proper logging
- **`app/utils.py`**: Utility functions for data formatting and message creation
- **`main.py`**: Clean FastAPI route definitions with minimal business logic

### Available Endpoints

#### 1. FBref Data Ingestion
```
POST /sources/fbref
```

**Request Body:**
```json
{
  "get_current_season_only": true,
  "use_cache": false,
  "cutoff_days": 7,
  "run_in_background": false
}
```

**Synchronous Response:**
```json
{
  "status": "success",
  "inserted_rows": 150,
  "first_row": "...",
  "last_row": "...",
  "message": "Successfully inserted 150 rows"
}
```

**Background Response:**
```json
{
  "status": "accepted",
  "message": "FBref data ingestion started in background. Check logs for progress."
}
```

#### 2. SOFIFA Team Stats Ingestion
```
POST /sources/sofifa/team_stats
```

**Request Body:**
```json
{
  "use_cache": false,
  "scrap_all": false,
  "run_in_background": false
}
```

#### 3. Odds Data Ingestion
```
POST /sources/the_odds_api/odds
```

**Request Body:**
```json
{
  "run_in_background": false
}
```

### Monitoring Background Tasks

When tasks are run in background:
1. The API immediately returns with `status: "accepted"`
2. Progress can be monitored through the service logs
3. Tasks are logged with INFO level for success and ERROR level for failures

### Usage Examples

#### Synchronous (default behavior)
```bash
curl -X POST "http://localhost:8100/sources/fbref" \
  -H "Content-Type: application/json" \
  -d '{
    "get_current_season_only": true,
    "use_cache": true,
    "cutoff_days": 7,
    "run_in_background": false
  }'
```

#### Background execution
```bash
curl -X POST "http://localhost:8100/sources/fbref" \
  -H "Content-Type: application/json" \
  -d '{
    "get_current_season_only": true,
    "use_cache": true,
    "cutoff_days": 7,
    "run_in_background": true
  }'
```

### Testing

Use the provided test script to test both synchronous and background execution:

```bash
python test_background_tasks.py
```

Make sure the service is running on port 8100 before running the tests.

## Running the Service

```bash
DB_PORT=5432 uv run uvicorn main:app --port 8100
```