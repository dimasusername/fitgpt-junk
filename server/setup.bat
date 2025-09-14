@echo off
REM Setup script for Windows

echo Setting up AI Chat Application Backend...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Copy environment file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from example...
    copy .env.example .env
    echo WARNING: Please edit .env with your actual API keys and configuration
)

echo Setup complete!
echo.
echo To activate the virtual environment manually:
echo   venv\Scripts\activate.bat
echo.
echo To run the server:
echo   start.bat
echo.
echo To deactivate the virtual environment:
echo   deactivate

pause