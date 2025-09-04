# OptiBet Lib

Shared library for the OptiBet Soccer Betting ML Optimizer platform.

## Installation

```bash
pip install -e .
```

## Features

This library provides common utilities and models shared across all OptiBet services:

- Database connection and ORM models
- Shared data models and validation
- Common utilities and helper functions
- ML model interfaces and abstractions
- Configuration management

## Usage

```python
from optibet_lib import models, utils, database

# Use shared models
match = models.Match(...)

# Use database utilities
db = database.get_connection()

# Use utility functions
result = utils.calculate_odds(...)
```

## Development

To set up for development:

```bash
pip install -e ".[dev]"
pre-commit install
```