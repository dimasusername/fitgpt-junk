# VS Code Development Configuration

This document describes the VS Code tasks, debugging configurations, and development tools set up for the FitGPT project.

## Quick Start

### Running the Application
- **Start Full Stack**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Dev: Start Full Stack"
- **Start Server Only**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Server: Start Development"
- **Start Frontend Only**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Frontend: Start Development"

### Testing
- **Run All Tests**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Server: Run All Tests"
- **Run Fast Tests**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Server: Run Fast Tests"
- **Run Tests with Coverage**: `Ctrl+Shift+P` → "Tasks: Run Task" → "Server: Run Tests with Coverage"

### Debugging
- **Debug Full Stack**: `F5` → Select "Debug Full Stack"
- **Debug Server Only**: `F5` → Select "Debug FastAPI Server"
- **Debug Frontend Only**: `F5` → Select "Debug Next.js Development"

## Available Tasks

### Server (Python/FastAPI) Tasks

#### Development
- `Server: Start Development` - Start FastAPI server in development mode
- `Server: Start Production` - Start server in production mode with uvicorn
- `Server: Setup Virtual Environment` - Create and setup Python virtual environment
- `Server: Install Dependencies` - Install Python packages from requirements.txt
- `Server: Upgrade Dependencies` - Upgrade all Python packages

#### Testing
- `Server: Run All Tests` - Run complete test suite
- `Server: Run Unit Tests` - Run unit tests only (fast)
- `Server: Run Integration Tests` - Run integration tests
- `Server: Run API Tests` - Run API endpoint tests
- `Server: Run Tests with Coverage` - Run tests with coverage report
- `Server: Run Fast Tests` - Run unit + API tests (quick feedback)

#### Code Quality
- `Server: Lint with Flake8` - Run flake8 linting
- `Server: Format with Black` - Format code with Black
- `Server: Sort Imports with isort` - Sort and organize imports
- `Server: Type Check with mypy` - Run static type checking

### Frontend (Next.js) Tasks

#### Development
- `Frontend: Start Development` - Start Next.js development server
- `Frontend: Build Production` - Build production bundle
- `Frontend: Start Production` - Start production server
- `Frontend: Install Dependencies` - Install npm packages
- `Frontend: Update Dependencies` - Update npm packages

#### Code Quality
- `Frontend: Lint` - Run ESLint
- `Frontend: Type Check` - Run TypeScript type checking
- `Frontend: Bundle Analyzer` - Analyze bundle size

### Health Checks
- `Health: Check Server` - Test if server is responding
- `Health: Check Frontend` - Test if frontend is responding  
- `Health: Check Both Services` - Test both server and frontend

### Workflow Tasks
- `Dev: Start Full Stack` - Start both server and frontend
- `Dev: Build All` - Build all production assets
- `Dev: Setup Project` - Setup complete development environment
- `Dev: Lint All` - Run linting on all code
- `Dev: Type Check All` - Run type checking on all code

### Cleanup Tasks
- `Cleanup: Clear All Caches` - Clear Python and Node.js caches
- `Cleanup: Reset Node Modules` - Remove and reinstall node_modules
- `Cleanup: Reset Python Environment` - Remove and recreate virtual environment

## Debugging Configurations

### Python/FastAPI Debugging
- `Debug FastAPI Server` - Debug server in development mode
- `Debug FastAPI Server (Production Mode)` - Debug server with uvicorn
- `Debug Current Python File` - Debug currently open Python file
- `Debug Python Tests` - Debug test suite
- `Debug Current Test File` - Debug currently open test file
- `Debug Unit Tests Only` - Debug unit tests specifically
- `Debug API Tests Only` - Debug API tests specifically

### Node.js/Next.js Debugging
- `Debug Next.js Development` - Debug Next.js in development mode
- `Debug Next.js Production Build` - Debug production build
- `Debug in Chrome` - Debug in Chrome browser
- `Attach to Chrome` - Attach to running Chrome instance

### Compound Configurations
- `Debug Full Stack` - Debug both server and frontend simultaneously
- `Debug Full Stack with Browser` - Debug server, frontend, and browser

## Code Snippets

### Python Snippets
- `route` - FastAPI route template
- `depend` - FastAPI dependency template
- `model` - Pydantic model template
- `test` - Pytest test function template
- `fixture` - Pytest fixture template
- `error` - Error handler template
- `logger` - Logger setup
- `async` - Async function template

### TypeScript/React Snippets
- `rfc` - React functional component
- `hook` - Custom React hook
- `page` - Next.js page component
- `api` - Next.js API route
- `tw` - Tailwind CSS component
- `interface` - TypeScript interface
- `fetch` - Fetch API call template

## Extensions

The workspace recommends installing these extensions for optimal development experience:

### Essential
- Python
- Pylance
- Python Debugger
- ESLint
- Prettier
- TypeScript and JavaScript

### Python Development
- Black Formatter
- Flake8
- isort
- mypy Type Checker

### Frontend Development
- Tailwind CSS IntelliSense
- ES7+ React/Redux/React-Native snippets

### Productivity
- GitLens
- GitHub Copilot
- Thunder Client (API testing)
- Todo Tree

## Configuration Files

### Python Configuration
- `.flake8` - Flake8 linting configuration
- `pyproject.toml` - Black, isort, mypy, pytest configuration
- `requirements.txt` - Python dependencies with dev tools

### Frontend Configuration
- `.prettierrc` - Prettier formatting configuration
- `.prettierignore` - Files to ignore during formatting
- `eslint.config.mjs` - ESLint configuration
- `tsconfig.json` - TypeScript configuration

### VS Code Configuration
- `.vscode/settings.json` - Workspace settings
- `.vscode/tasks.json` - Task definitions
- `.vscode/launch.json` - Debug configurations
- `.vscode/extensions.json` - Recommended extensions
- `.vscode/python.code-snippets` - Python code snippets
- `.vscode/typescript.code-snippets` - TypeScript/React snippets

## Tips

### Keyboard Shortcuts
- `Ctrl+Shift+P` - Command palette (access all tasks)
- `F5` - Start debugging
- `Ctrl+F5` - Start without debugging
- `Ctrl+Shift+F5` - Restart debugging
- `Ctrl+\`` - Toggle terminal
- `Ctrl+Shift+\`` - New terminal

### Running Tasks from Terminal
You can also run tasks directly from the integrated terminal:
```bash
# Server tasks
cd server && source .venv/bin/activate && python main.py
cd server && source .venv/bin/activate && ./run_tests.sh all
cd server && source .venv/bin/activate && black app/ tests/

# Frontend tasks
cd app && npm run dev
cd app && npm run build
cd app && npm run lint
```

### Workspace Organization
- Server code is in `/server` directory
- Frontend code is in `/app` directory
- All VS Code configuration is in `/.vscode` directory
- Documentation and project files are in root directory

This configuration provides a comprehensive development environment with proper tooling for Python/FastAPI backend development and Next.js frontend development, all integrated within VS Code.
