# Tests Documentation

This directory contains a well-organized test suite for the FastAPI server following Python/FastAPI best practices.

## 📁 Test Structure

```
tests/
├── __init__.py              # Test configuration and path setup
├── conftest.py              # Pytest fixtures and shared test utilities
├── api/                     # API endpoint tests (HTTP-level testing)
│   └── test_health_endpoints.py
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_config.py
│   └── test_health.py
├── integration/             # Integration tests (may require external services)
│   └── test_database.py
└── fixtures/                # Test utilities and mock objects
    └── mock_database.py
```

## 🏷️ Test Categories (Markers)

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests, may require database/services  
- `@pytest.mark.api` - API endpoint tests using TestClient
- `@pytest.mark.db` - Database-related tests
- `@pytest.mark.slow` - Tests that take longer to run

## 🚀 Running Tests

### Quick Commands

```bash
# Run all tests
./run_tests.sh

# Run only fast tests (unit + API)
./run_tests.sh fast

# Run specific test types
./run_tests.sh unit         # Unit tests only
./run_tests.sh api          # API tests only
./run_tests.sh integration  # Integration tests only
./run_tests.sh db           # Database tests only

# Run with coverage report
./run_tests.sh coverage
```

### Using pytest directly

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all organized tests
pytest tests/

# Run specific directories
pytest tests/unit/          # Unit tests
pytest tests/api/           # API tests
pytest tests/integration/   # Integration tests

# Run by markers
pytest -m "unit"            # All unit tests
pytest -m "api"             # All API tests
pytest -m "unit or api"     # Unit OR API tests
pytest -m "db"              # Database tests

# Run specific test files
pytest tests/unit/test_config.py -v
pytest tests/api/test_health_endpoints.py::test_liveness_endpoint -v
```

## 📋 Test Types Explained

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- No external dependencies (database, network, files)
- Very fast execution (< 1 second total)
- Mock external dependencies when needed

### Integration Tests (`tests/integration/`)
- Test how components work together
- May require external services (database, APIs)
- Slower execution but more realistic
- Test actual data flows and integrations

### API Tests (`tests/api/`)
- Test HTTP endpoints using FastAPI's TestClient
- Test request/response cycles
- Validate API contracts and HTTP status codes
- Test authentication, authorization, error handling

## 🛠️ Writing New Tests

### Adding Unit Tests
```python
# tests/unit/test_new_feature.py
import pytest

@pytest.mark.unit
def test_some_function():
    from app.some_module import some_function
    result = some_function("input")
    assert result == "expected_output"
```

### Adding API Tests
```python
# tests/api/test_new_endpoints.py
import pytest

@pytest.mark.api
def test_new_endpoint(client):
    response = client.post("/api/new-endpoint", json={"data": "test"})
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

### Adding Integration Tests
```python
# tests/integration/test_new_integration.py
import pytest

@pytest.mark.integration
@pytest.mark.db
def test_database_integration():
    # Test that requires actual database
    pass
```

## 🎯 Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Markers**: Always mark tests with appropriate categories
3. **Fixtures**: Use pytest fixtures for shared setup code
4. **Isolation**: Each test should be independent and not rely on other tests
5. **Speed**: Keep unit tests fast, use integration tests for complex scenarios
6. **Coverage**: Aim for high test coverage but focus on critical paths

## 📊 Test Coverage

To generate test coverage reports:

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## 🔧 Configuration

Test configuration is in:
- `pyproject.toml` - Pytest settings and markers
- `conftest.py` - Shared fixtures and test setup
- `tests/__init__.py` - Path configuration

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the server directory and virtual environment is activated
2. **Database Tests Failing**: Check if `.env` file has correct database credentials
3. **Slow Tests**: Use `./run_tests.sh fast` for quick feedback during development

### Debug Mode
```bash
# Run tests with more verbose output
pytest tests/ -v --tb=long

# Run with pdb debugger
pytest tests/ --pdb

# Run only failed tests
pytest tests/ --lf
```
