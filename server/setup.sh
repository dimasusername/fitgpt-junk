#!/bin/bash

# AI Chat Application Backend Setup Script

echo "🔧 Setting up AI Chat Application Backend..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install fastapi uvicorn python-multipart pydantic pydantic-settings python-dotenv supabase

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
chmod +x start.sh
chmod +x setup.sh

# Run tests
echo "🧪 Running setup tests..."
python test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Backend setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys:"
    echo "   - GEMINI_API_KEY=your_gemini_api_key"
    echo "   - SUPABASE_URL=https://your-project.supabase.co"
    echo "   - SUPABASE_ANON_KEY=your_anon_key"
    echo "   - SUPABASE_SERVICE_KEY=your_service_key"
    echo ""
    echo "2. Start the server:"
    echo "   ./start.sh"
    echo ""
    echo "3. Test the API:"
    echo "   curl http://localhost:8000/api/health/live"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi