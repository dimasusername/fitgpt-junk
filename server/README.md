# AI Chat Application Backend

FastAPI backend for the AI chat application with RAG capabilities.

## Setup

### Quick Setup (Recommended)
```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create a `.env` file from the example
- Set up the project for development

### Manual Setup
1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and configuration
   ```

### Required Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key

## Running the Server

### Development (Recommended)
```bash
./start.sh
```

### Manual Development
```bash
source .venv/bin/activate  # Activate virtual environment
python run.py
```

### Production
```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Testing

The server includes a comprehensive test suite with organized test categories:

### Quick Testing
```bash
# Run fast tests (unit + API)
./run_tests.sh fast

# Run all tests
./run_tests.sh

# Run with coverage report
./run_tests.sh coverage
```

### Test Categories
- **Unit Tests** (`tests/unit/`) - Fast, isolated component tests
- **API Tests** (`tests/api/`) - HTTP endpoint testing with TestClient
- **Integration Tests** (`tests/integration/`) - Database and service integration

### Test Commands
```bash
./run_tests.sh unit         # Unit tests only
./run_tests.sh api          # API endpoint tests  
./run_tests.sh integration  # Integration tests
./run_tests.sh db           # Database-specific tests
```

See `tests/README.md` for detailed testing documentation.

## API Endpoints

### Health Checks
- `GET /api/health` - Comprehensive health check with dependency status
- `GET /api/health/ready` - Readiness check for deployment
- `GET /api/health/live` - Liveness check for deployment

## Project Structure

```
server/
├── main.py                 # FastAPI application entry point
├── run.py                  # Development server runner
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration example
└── app/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py       # Application settings
    │   ├── database.py     # Supabase client setup
    │   └── exceptions.py   # Custom exceptions
    └── api/
        ├── __init__.py
        ├── routes.py       # Main API router
        └── endpoints/
            ├── __init__.py
            └── health.py   # Health check endpoints
```

## Configuration

The application uses Pydantic settings for configuration management. All settings can be configured via environment variables or a `.env` file.

Key configuration options:
- CORS origins for frontend integration
- File upload limits and allowed types
- AI model configuration
- Database connection settings

## Error Handling

The application includes comprehensive error handling:
- Global exception handlers for unhandled errors
- Custom application exceptions with proper HTTP status codes
- Structured error responses
- Request logging and error tracking

## Health Monitoring

Multiple health check endpoints are provided:
- `/health` - Detailed health status including database connectivity
- `/health/ready` - Simple readiness check for load balancers
- `/health/live` - Basic liveness check for container orchestration

## Testing

The project includes a comprehensive test suite organized by test type:

### Quick Testing
```bash
# Run all tests
./run_tests.sh

# Run fast tests only (unit + API)
./run_tests.sh fast

# Run specific test types
./run_tests.sh unit         # Unit tests only
./run_tests.sh api          # API endpoint tests
./run_tests.sh integration  # Integration tests
./run_tests.sh db           # Database tests
```

### Test Structure
```
tests/
├── unit/           # Fast unit tests, no external dependencies
├── api/            # HTTP endpoint tests using TestClient
├── integration/    # Tests requiring external services
└── fixtures/       # Test utilities and mock objects
```

### Test Categories
- **Unit Tests**: Test individual functions in isolation (very fast)
- **API Tests**: Test HTTP endpoints via FastAPI TestClient
- **Integration Tests**: Test database connectivity and service integration
- **Legacy Tests**: Original standalone test scripts

For detailed testing documentation, see [tests/README.md](tests/README.md).

### Running Tests with pytest
```bash
source .venv/bin/activate

# All tests
pytest tests/

# Specific categories
pytest -m "unit"        # Unit tests only
pytest -m "api"         # API tests only
pytest -m "integration" # Integration tests only
```