# Contributing to OptiBet

We love your input! We want to make contributing to OptiBet as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Pull Request Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Getting Started

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL
- Git

### Setup Development Environment

1. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/SoccerBetMLOptimizer.git
   cd SoccerBetMLOptimizer
   ```

2. **Quick setup**:
   ```bash
   ./dev.sh setup
   ```

3. **Configure secrets**:
   ```bash
   cp secrets_template.env secrets.env
   # Edit secrets.env with your API keys
   ```

4. **Start development environment**:
   ```bash
   ./dev.sh start
   ```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**:
   - Write your code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   ./dev.sh check  # Run all checks
   ./dev.sh test   # Run tests only
   ./dev.sh lint   # Run linting only
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `style:` for formatting changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Create a Pull Request** on GitHub

## Code Style

We use automated code formatting and linting:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security analysis

All of these are enforced by pre-commit hooks and CI/CD.

### Code Style Guidelines

- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names
- Follow PEP 8 style guide (enforced by Black)

### Example Code

```python
from typing import Optional, List
from pydantic import BaseModel


class Match(BaseModel):
    """Represents a soccer match."""
    
    home_team: str
    away_team: str
    date: str
    odds_home: Optional[float] = None


def calculate_probability(odds: float) -> float:
    """Calculate implied probability from decimal odds.
    
    Args:
        odds: Decimal odds value
        
    Returns:
        Implied probability as a float between 0 and 1
        
    Raises:
        ValueError: If odds are not positive
    """
    if odds <= 0:
        raise ValueError("Odds must be positive")
    
    return 1.0 / odds
```

## Testing

### Writing Tests

- Write unit tests for all new functions
- Write integration tests for API endpoints
- Use descriptive test names
- Mock external dependencies
- Aim for 80%+ code coverage

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient


def test_calculate_probability_valid_odds():
    """Test probability calculation with valid odds."""
    result = calculate_probability(2.0)
    assert result == 0.5


def test_calculate_probability_invalid_odds():
    """Test probability calculation with invalid odds."""
    with pytest.raises(ValueError, match="Odds must be positive"):
        calculate_probability(-1.0)


class TestPredictionAPI:
    """Test suite for prediction API endpoints."""
    
    def test_compute_predictions_success(self, client: TestClient):
        """Test successful prediction computation."""
        response = client.get("/compute/predictions", params={"n_matches": 5})
        assert response.status_code == 200
        assert "df_optim_results" in response.json()
```

### Running Tests

```bash
# Run all tests
./dev.sh test

# Run specific test file
cd app-backend
pytest tests/test_main.py -v

# Run tests with coverage
cd app-backend
pytest tests/ --cov=. --cov-report=html
```

## Documentation

### API Documentation

- All API endpoints are automatically documented with OpenAPI/Swagger
- Add detailed descriptions and examples to endpoint decorators
- Use Pydantic models for request/response validation

### Code Documentation

- Write clear docstrings for all public functions
- Include type hints
- Add inline comments for complex logic
- Update README.md for major changes

### Architecture Documentation

Update architecture documentation in `docs/` for:
- New services or major components
- Database schema changes
- API changes
- Deployment changes

## Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/JulienDelavande/SoccerBetMLOptimizer/issues).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

We use GitHub issues to track feature requests. Request a feature by [opening a new issue](https://github.com/JulienDelavande/SoccerBetMLOptimizer/issues) with the "enhancement" label.

**Great Feature Requests** include:

- Clear description of the feature
- Motivation for why this feature would be useful
- Examples of how it would be used
- Consideration of alternatives

## Architecture Guidelines

### Microservices Design

- Keep services focused and independent
- Use well-defined APIs between services
- Minimize shared state
- Handle failures gracefully

### Database Design

- Use proper indexing for performance
- Follow normalization principles
- Document schema changes in migrations
- Consider data privacy and security

### ML/Data Science

- Version your models and datasets
- Document feature engineering decisions
- Include model evaluation metrics
- Consider model bias and fairness

## Security Guidelines

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Follow principle of least privilege
- Keep dependencies updated

## Performance Guidelines

- Profile before optimizing
- Use appropriate caching strategies
- Monitor database query performance
- Consider memory usage and scalability

## Release Process

1. All features merged to `main` branch
2. Version bump according to semantic versioning
3. Create release notes
4. Tag release in Git
5. Deploy to staging for testing
6. Deploy to production

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to reach out:

- Create an issue for technical questions
- Email: julien.delavande@example.com
- Join our discussions in GitHub Discussions

## Recognition

Contributors will be recognized in our README and release notes. Thank you for making OptiBet better! 🎉