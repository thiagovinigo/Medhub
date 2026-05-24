# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MedAI Diagnostics** — aplicação full-stack de análise de imagens médicas com IA. O usuário faz upload de uma imagem (raio-X, RM, TC, ultrassom), e dois agentes Groq/LLaMA retornam um laudo estruturado + pesquisa acadêmica relacionada.

## Architecture

Two independent services that must run simultaneously:

- **Backend** (`backend/`) — FastAPI + Python. Exposes a single endpoint `POST /api/analyze` that receives an image file, preprocesses it, and runs the two-agent pipeline.
- **Frontend** (`frontend/`) — React 19 + Vite. Single-page app that uploads the image and renders the markdown results.

### Agent Pipeline (`backend/agents.py`)

`process_image(file_path)` is the core function — it orchestrates two sequential `agno` agents:

1. **Medical Image Agent** — uses `meta-llama/llama-4-scout-17b-16e-instruct` (vision) via Groq to analyze the image and return a 4-section structured report in Portuguese.
2. **Research Agent** — uses `llama-3.3-70b-versatile` (text) via Groq + optional Tavily web search to find clinical literature based on the analysis from step 1.

Image preprocessing: `preprocess_img()` resizes images to 600px width before sending to the vision model, saving to a temp file that is cleaned up after use.

The `format_res()` helper strips `<think>` chain-of-thought tokens from model output before returning to the client.

### API Contract

`POST /api/analyze` — FormData with a single `file` field (jpg/jpeg/png/bmp/gif). Returns:
```json
{ "analysis": "<markdown string>", "research": "<markdown string>" }
```

The frontend hardcodes `http://localhost:8000` as the backend URL (`frontend/src/App.jsx:59`).

## Environment Setup

Create `.env` at the **project root** (not inside `backend/`):
```
GROQ_API_KEY=...       # Required — used by both agents
TAVILY_API_KEY=...     # Optional — enables web search in the research agent
```

`backend/main.py` and `backend/agents.py` both call `load_dotenv(dotenv_path="../.env")` to load from the root.

## Running Locally

**Backend** (Terminal 1):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
# Runs on http://localhost:8000
```

**Frontend** (Terminal 2):
```powershell
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## Frontend Commands

```powershell
cd frontend
npm run dev      # Dev server
npm run build    # Production build
npm run lint     # ESLint
npm run preview  # Preview production build
```

## Planned Features (from README)

- PDF report generation (FPDF/WeasyPrint)
- Patient history with SQLite
- Text report upload (PDF lab results) correlated with image analysis
- Multi-specialist agent routing (oncology, orthopedics, etc.)
- ABNT/PubMed citation format in prompts
