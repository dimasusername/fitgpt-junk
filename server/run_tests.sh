#!/bin/bash
# Test runner script for the FastAPI server

set -e  # Exit on any error

echo "🧪 Running FastAPI Server Tests"
echo "================================"

# Activate virtual environment
source .venv/bin/activate

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the server directory"
    exit 1
fi

# Function to run unit tests only
run_unit_tests() {
    echo "⚡ Running unit tests (fast)..."
    pytest tests/unit/ -v -m "unit"
    echo ""
}

# Function to run integration tests
run_integration_tests() {
    echo "🔗 Running integration tests..."
    pytest tests/integration/ -v -m "integration"
    echo ""
}

# Function to run API tests
run_api_tests() {
    echo "🌐 Running API tests..."
    pytest tests/api/ -v -m "api"
    echo ""
}

# Function to run all organized tests
run_all_tests() {
    echo "🎯 Running all organized tests..."
    pytest tests/ -v
    echo ""
}

# Function to run tests with coverage
run_with_coverage() {
    echo "� Running tests with coverage..."
    pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
    echo ""
    echo "� Coverage report generated in htmlcov/index.html"
}

# Function to run specific test types
run_by_marker() {
    local marker="$1"
    echo "🏷️  Running tests marked as '$marker'..."
    pytest tests/ -v -m "$marker"
    echo ""
}

# Parse command line arguments
case "${1:-all}" in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "api")
        run_api_tests
        ;;
    "db")
        run_by_marker "db"
        ;;
    "fast")
        run_unit_tests
        run_api_tests
        ;;
    "coverage")
        run_with_coverage
        ;;
    "all")
        run_all_tests
        ;;
    *)
        echo "Usage: $0 [unit|integration|api|db|fast|coverage|all]"
        echo ""
        echo "  unit        - Run unit tests only (fast)"
        echo "  integration - Run integration tests (may be slow)"
        echo "  api         - Run API endpoint tests"
        echo "  db          - Run database-related tests"
        echo "  fast        - Run unit + API tests (quick feedback)"
        echo "  coverage    - Run all tests with coverage report"
        echo "  all         - Run all tests (default)"
        exit 1
        ;;
esac

echo "✅ Test run completed!"
