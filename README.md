# FitGPT - AI Chat Application

A full-stack ChatGPT-like web application with advanced AI features and document RAG capabilities.

## Project Structure

This is a monorepo containing:

- **Frontend** (`app/`) - Next.js with shadcn/ui components
- **Backend** (`server/`) - FastAPI with Supabase integration
- **Ancient History Documents** (`ancient_history_pdfs/`) - Sample documents for RAG testing

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Git

### Development Setup

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd fitgpt
   ```

2. **Open in VS Code (Recommended):**
   ```bash
   code fitgpt.code-workspace
   ```

3. **Setup Backend:**
   ```bash
   cd server
   ./setup.sh
   ./start.sh
   ```

4. **Setup Frontend:**
   ```bash
   cd app
   npm install
   npm run dev
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Features

### Current Implementation
- ✅ FastAPI backend with health monitoring
- ✅ Next.js frontend with chat UI components
- ✅ Supabase database integration
- ✅ Google Gemini AI integration
- ✅ Comprehensive test suite with pytest
- ✅ Professional development environment setup

### Roadmap
- [ ] **Chat Interface**
  - [ ] Streaming responses
  - [ ] Sidebar with history
  - [ ] Edit previous messages with DB serialization
  - [ ] Notion-inspired look and feel
  - [ ] Multi-Agent collaboration (ReAct, tool-using agents)

- [ ] **File Upload and RAG**
  - [ ] Upload files (PDF, DOCX, TXT)
  - [ ] Text extraction and chunking
  - [ ] Vector embeddings storage
  - [ ] RAG implementation for document-based Q&A
  - [ ] Vector database integration (FAISS, Pinecone, etc.)

## Development

### VS Code Integration
This project includes a complete VS Code workspace configuration:
- Multi-root workspace for frontend/backend development
- Python environment auto-detection
- Debug configurations for both frontend and backend
- Recommended extensions and settings
- Integrated testing with pytest

### Testing
```bash
# Backend tests
cd server
./run_tests.sh            # All tests
./run_tests.sh fast       # Quick tests (unit + API)
./run_tests.sh coverage   # With coverage report

# Frontend tests
cd app
npm test                  # When implemented
```

### Project Documentation
- [Backend Documentation](server/README.md)
- [Frontend Documentation](app/README.md)
- [Testing Guide](server/tests/README.md)
- [VS Code Workspace Setup](.vscode/README.md)

## Technology Stack

### Backend
- **Framework:** FastAPI with async support
- **Database:** Supabase (PostgreSQL)
- **AI:** Google Gemini API
- **Testing:** pytest with asyncio support
- **Environment:** Python virtual environment (.venv)

### Frontend
- **Framework:** Next.js 14 with TypeScript
- **UI:** shadcn/ui components with Tailwind CSS
- **Chat Components:** Adapted from shadcn-chat examples
- **Build Tool:** Next.js with Turbopack

### Development Tools
- **IDE:** VS Code with multi-root workspace
- **Version Control:** Git with organized .gitignore
- **Testing:** Comprehensive test suite with coverage reporting
- **Scripts:** Automated setup and development scripts

