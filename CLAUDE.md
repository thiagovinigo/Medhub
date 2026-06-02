# CLAUDE.md

Guidance for Claude Code when working with this repository.

> Documentação de segurança detalhada: [seguranca.md](./seguranca.md)

## Project Overview

**MedAI Diagnostics** — plataforma full-stack de análise de imagens médicas com IA. O usuário faz upload de imagens (raio-X, RM, TC, ultrassom, DICOM), e dois agentes Groq/LLaMA retornam um laudo estruturado em português + pesquisa acadêmica relacionada.

## Deployment Architecture

```
Browser
  └─▶ Vercel (frontend)          https://<projeto>.vercel.app
        └─▶ Railway (backend)    https://<projeto>.up.railway.app
              └─▶ Supabase       PostgreSQL (connection pooler IPv4)
```

| Camada    | Plataforma | Stack                        |
|-----------|------------|------------------------------|
| Frontend  | Vercel     | React 19 + Vite              |
| Backend   | Railway    | FastAPI + Python 3.11        |
| Banco     | Supabase   | PostgreSQL (pooler porta 5432) |

### Variáveis de Ambiente

**Railway** (backend):
```
GROQ_API_KEY=...          # Obrigatório
TAVILY_API_KEY=...        # Opcional (habilita busca web)
DATABASE_URL=postgresql://postgres.xxx:[senha]@aws-0-[região].pooler.supabase.com:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=...          # anon key
SECRET_KEY=...            # JWT secret (mude em produção)
```

**Vercel** (frontend):
```
VITE_API_URL=https://<seu-backend>.up.railway.app
```

> **IMPORTANTE:** Use sempre a URL do **Connection Pooler** do Supabase (não a URL direta),
> pois Railway não suporta IPv6 e a URL direta resolve para IPv6.

## Repository Structure

```
medicina/
├── backend/              # FastAPI app (deployed on Railway)
│   ├── main.py           # Entry point, todos os endpoints REST
│   ├── agents.py         # Pipeline de IA: analyze + research
│   ├── case_agents.py    # Agentes para casos clínicos completos
│   ├── database.py       # SQLAlchemy models + engine
│   ├── auth.py           # JWT auth (bcrypt + python-jose)
│   ├── doc_parser.py     # Extração de texto de PDF/DOCX
│   ├── pdf_generator.py  # Geração de laudo em PDF (fpdf2)
│   └── requirements.txt
├── frontend/             # React app (deployed on Vercel)
│   ├── src/
│   │   ├── App.jsx       # Root component, state management
│   │   └── components/   # AuthModal, HistoryPanel, PatientPanel,
│   │                     # CaseWizard, SpecialtyDashboard, etc.
│   └── vite.config.js
├── api/                  # Vercel Python serverless (fallback/legacy)
│   └── index.py
├── vercel.json           # Build config: frontend + API routing
├── .python-version       # 3.11
└── .env                  # Local only (não commitar)
```

## Agent Pipeline

### Quick Analysis (`backend/agents.py`)

`process_image(file_path)` — pipeline sequencial com 2 agentes:

1. **Medical Image Agent** — `meta-llama/llama-4-scout-17b-16e-instruct` (vision, Groq)
   - Recebe imagem redimensionada para 600px de largura
   - Retorna laudo 4-seções em português: tipo/região, achados, diagnóstico, linguagem leiga
2. **Research Agent** — `llama-3.3-70b-versatile` (text, Groq) + Tavily opcional
   - Recebe o texto do laudo e busca literatura complementar

Preprocessing: `preprocess_img()` suporta DICOM (pydicom) e formatos comuns (Pillow).
Pós-processamento: `format_res()` remove tokens `<think>` do chain-of-thought.

### Case Analysis (`backend/case_agents.py`)

`process_case(payload)` — analisa casos clínicos completos com múltiplos exames + documentos.

## API Contract

| Método | Rota                             | Auth     | Descrição                        |
|--------|----------------------------------|----------|----------------------------------|
| GET    | `/`                              | —        | Health check                     |
| GET    | `/api/dbcheck`                   | —        | Diagnóstico de conexão DB        |
| POST   | `/api/analyze`                   | opcional | Upload de imagem → laudo IA      |
| POST   | `/api/cases/analyze`             | opcional | Caso clínico completo            |
| GET    | `/api/cases`                     | JWT      | Listar casos salvos              |
| POST   | `/api/suggest`                   | —        | Sugestão clínica por especialidade |
| POST   | `/api/pdf`                       | —        | Gerar PDF do laudo               |
| POST   | `/api/auth/register`             | —        | Cadastro                         |
| POST   | `/api/auth/login`                | —        | Login → token JWT                |
| GET    | `/api/auth/me`                   | JWT      | Dados do usuário logado          |
| GET    | `/api/history`                   | JWT      | Histórico de exames              |
| GET    | `/api/patients`                  | JWT      | Listar pacientes                 |
| POST   | `/api/patients`                  | JWT      | Criar paciente                   |
| GET    | `/api/patients/{id}`             | JWT      | Detalhe do paciente              |
| PUT    | `/api/patients/{id}`             | JWT      | Atualizar paciente               |
| POST   | `/api/patients/{id}/metrics`     | JWT      | Adicionar métrica (peso/altura)  |
| POST   | `/api/patients/{id}/conditions`  | JWT      | Adicionar condição clínica       |
| DELETE | `/api/patients/{id}/conditions/{cid}` | JWT | Remover condição            |
| GET    | `/api/patients/{id}/cases`       | JWT      | Casos do paciente                |

### Frontend API URL

`App.jsx` usa `import.meta.env.VITE_API_URL` com fallback para `http://localhost:8000` em dev:

```js
const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
```

## Running Locally

**Backend** (Terminal 1):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
# http://localhost:8000
```

**Frontend** (Terminal 2):
```powershell
cd frontend
npm install
npm run dev
# http://localhost:5173
```

Crie `.env` na raiz do projeto:
```
GROQ_API_KEY=...
TAVILY_API_KEY=...        # opcional
DATABASE_URL=...          # omita para usar SQLite local em /tmp
SECRET_KEY=dev-secret
```

## Security

Consulte [seguranca.md](./seguranca.md) para o guia completo. Resumo dos pontos críticos:

- **Nunca commitar `.env`** — chaves ficam nos painéis do Railway e Vercel
- **`SECRET_KEY`** deve estar definida no Railway (o fallback de dev é inseguro em produção)
- **`DATABASE_URL`** deve usar o Connection Pooler do Supabase (IPv4)
- Todas as queries já filtram por `user_id` — nunca retornar dados de outro usuário
- Uploads validam extensão em `main.py` antes de processar
- Prompts são fixos no código (`agents.py`) — usuário não controla as instruções da IA

## Known Issues

- **Railway + Supabase IPv6:** Railway não suporta IPv6. Sempre use a URL do **Connection Pooler** do Supabase (Project Settings → Database → Connection Pooling → Session mode, porta 5432) como `DATABASE_URL`.
- **Vercel Python bundle:** As dependências pesadas (agno, numpy, Pillow) podem aproximar o limite de 250 MB do Vercel. O backend em Railway é o deploy preferencial.
- **`load_dotenv(dotenv_path="../.env")`** em `main.py` e `agents.py` funciona localmente (`.env` na raiz) mas é ignorado em produção — as variáveis vêm diretamente da plataforma (Railway/Vercel).
