@echo off
REM Start script for Windows

echo Starting AI Chat Application Backend...

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo .env file not found. Creating from example...
    copy .env.example .env
    echo Please edit .env with your actual API keys and configuration
)

REM Start the server
echo Starting FastAPI server...
python run.py

pause