# spec.md — MedAI Diagnostics: Especificação Técnica

## 1. Visão Geral

MedAI Diagnostics é uma aplicação web de suporte clínico que utiliza modelos de linguagem multimodal (LLaMA via Groq) para analisar imagens médicas e retornar laudos estruturados em português, acompanhados de pesquisa acadêmica complementar.

**Casos de uso principais:**
- Análise rápida: upload de 1 imagem → laudo imediato
- Caso clínico: múltiplos exames + contexto do paciente → laudo consolidado
- Histórico: exames e casos salvos por usuário autenticado
- Prontuário: gerenciamento de pacientes com métricas e condições clínicas

---

## 2. Arquitetura de Produção

```
┌─────────────────────────────────────────────────────┐
│                     CLIENTE                         │
│              Browser / Mobile Browser               │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────┐
│                    VERCEL                            │
│           Frontend (React 19 + Vite)                │
│         Static files served from CDN                │
│   Route: /api/* → proxied to Railway backend        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS (VITE_API_URL)
┌──────────────────────▼──────────────────────────────┐
│                   RAILWAY                            │
│         Backend (FastAPI + Python 3.11)             │
│              uvicorn, porta 8000                    │
│  POST /api/analyze   POST /api/cases/analyze        │
│  GET  /api/history   POST /api/auth/*               │
│  CRUD /api/patients  POST /api/pdf                  │
└──────────────┬───────────────────┬──────────────────┘
               │ psycopg2 (IPv4)   │ HTTP
               │ pooler:5432       │
┌──────────────▼──────┐  ┌─────────▼──────────────────┐
│      SUPABASE       │  │         GROQ API            │
│   PostgreSQL DB     │  │  llama-4-scout (vision)     │
│  Connection Pooler  │  │  llama-3.3-70b (text)       │
│  (Session, IPv4)    │  └────────────────────────────┘
└─────────────────────┘
                            ┌────────────────────────┐
                            │      TAVILY (opcional)  │
                            │   Busca web acadêmica   │
                            └────────────────────────┘
```

---

## 3. Backend

### 3.1 Stack

| Componente       | Tecnologia              | Versão   |
|------------------|-------------------------|----------|
| Runtime          | Python                  | 3.11     |
| Framework        | FastAPI                 | latest   |
| ASGI Server      | uvicorn                 | latest   |
| ORM              | SQLAlchemy              | latest   |
| DB Driver        | psycopg2-binary         | latest   |
| IA Orchestration | agno                    | latest   |
| Vision LLM       | llama-4-scout-17b (Groq)| —        |
| Text LLM         | llama-3.3-70b (Groq)    | —        |
| Image Processing | Pillow + pydicom        | latest   |
| Auth             | python-jose + bcrypt    | —        |
| PDF              | fpdf2                   | latest   |
| Doc Parsing      | pymupdf + python-docx   | latest   |
| Web Search       | tavily-python           | latest   |
| Storage          | Supabase SDK            | latest   |

### 3.2 Estrutura de Arquivos

```
backend/
├── main.py          # FastAPI app, todos os endpoints, middleware CORS
├── agents.py        # process_image(): pipeline análise rápida
├── case_agents.py   # process_case(): pipeline caso clínico
├── database.py      # SQLAlchemy engine, models, get_db()
├── auth.py          # JWT tokens, bcrypt, Depends (optional/required)
├── doc_parser.py    # extract_text(): PDF + DOCX → texto
├── pdf_generator.py # generate_report_pdf(): laudo → PDF bytes
└── requirements.txt
```

### 3.3 Pipeline de Análise de Imagem (`agents.py`)

```
file_path
    │
    ▼
preprocess_img()
    ├── DICOM: pydicom → numpy → PIL (normalização Hounsfield)
    ├── Outros: PIL.open()
    └── Resize → 600px width → salva PNG temporário
    │
    ▼
Medical Image Agent (Groq / llama-4-scout vision)
    └── prompt: 4 seções (tipo/região, achados, diagnóstico, linguagem leiga)
    │
    ▼
format_res() → remove <think>...</think>
    │
    ▼
Research Agent (Groq / llama-3.3-70b + Tavily opcional)
    └── prompt: busca literatura baseada no laudo acima
    │
    ▼
format_res()
    │
    ▼
{ analysis: str, research: str, metadata: dict }
```

### 3.4 Pipeline de Caso Clínico (`case_agents.py`)

Recebe payload:
```json
{
  "patient": { "name", "birth_date", "sex", "weight_kg", "conditions", "chief_complaint" },
  "exams": [{ "name", "modality", "exam_date", "image_paths": ["..."] }],
  "documents": [{ "name", "text" }]
}
```

Processa cada imagem com o Medical Image Agent, depois consolida tudo num único Research Agent especializado.

### 3.5 Autenticação

- JWT (HS256), expiração 30 dias
- `SECRET_KEY` via env var (fallback inseguro para dev: `"medhub-dev-secret-change-in-prod"`)
- `get_optional_user`: endpoints públicos com salvamento opcional no histórico
- `get_required_user`: endpoints que exigem conta (histórico, pacientes, casos)

### 3.6 Banco de Dados

**Conexão:** `DATABASE_URL` env var. Fallback: `sqlite:////tmp/medhub.db`.
- Auto-converte `postgres://` → `postgresql://`
- Auto-adiciona `?sslmode=require` para PostgreSQL

**Tabelas:**

```sql
users (id, name, email, hashed_password, created_at)
exam_records (id, user_id→users, filename, modality, analysis, research, created_at)
patients (id, user_id→users, name, birth_date, sex, height_cm, blood_type, created_at)
patient_metrics (id, patient_id→patients, date, weight_kg, height_cm, notes)
patient_conditions (id, patient_id→patients, condition, active)
clinical_cases (id, user_id→users, patient_id→patients, title, chief_complaint,
                clinical_history, exams_summary, analysis, research, created_at, analyzed_at)
```

### 3.7 Endpoints Completos

```
GET  /                              → { status }
GET  /api/dbcheck                   → diagnóstico de conexão DB

POST /api/auth/register             body: { name, email, password }
POST /api/auth/login                body: { email, password }
GET  /api/auth/me                   JWT required

POST /api/analyze                   FormData: file (img) — JWT opcional
POST /api/cases/analyze             FormData: patient_json, exams_json, files[], doc_files[]
GET  /api/cases                     JWT required
POST /api/suggest                   body: { specialty, analysis, suggestion_type, patient_context }
POST /api/pdf                       body: { analysis, research, metadata }

GET  /api/history                   JWT required
GET  /api/patients                  JWT required
POST /api/patients                  JWT required; body: PatientCreate
GET  /api/patients/{id}             JWT required
PUT  /api/patients/{id}             JWT required; body: PatientUpdate
POST /api/patients/{id}/metrics     JWT required; body: MetricCreate
POST /api/patients/{id}/conditions  JWT required; body: ConditionCreate
DELETE /api/patients/{id}/conditions/{cid}  JWT required
GET  /api/patients/{id}/cases       JWT required
```

### 3.8 CORS

```python
allow_origins=["*"]
allow_credentials=False   # Bearer tokens não precisam de credentials mode
allow_methods=["*"]
allow_headers=["*"]
```

---

## 4. Frontend

### 4.1 Stack

| Componente   | Tecnologia       |
|--------------|------------------|
| Framework    | React 19         |
| Build        | Vite             |
| Linguagem    | JavaScript (JSX) |
| Ícones       | lucide-react     |
| Markdown     | react-markdown   |
| Validação    | zod              |

### 4.2 Estrutura de Componentes

```
App.jsx                   # Root: state global, roteamento de modo, header
├── AuthModal             # Login / Registro
├── HistoryPanel          # Sidebar: histórico de exames do usuário
├── PatientPanel          # CRUD de pacientes + métricas + condições
├── PatientSelector       # Escolha/criação de paciente antes do Caso Clínico
├── SpecialtyDashboard    # Grid de especialidades médicas
└── CaseWizard            # Wizard multi-step para caso clínico completo
```

### 4.3 Modos de Operação

```
home (não logado)  → cards: Análise Rápida | Caso Clínico
home (logado)      → grid de especialidades + atalhos
quick              → upload de 1 imagem → laudo
case               → PatientSelector → SpecialtyDashboard → CaseWizard
```

### 4.4 Gerenciamento de Estado

Estado centralizado em `App.jsx` (useState hooks). Sem biblioteca externa de state management.

- `user` / `token` — autenticação (token persiste em `localStorage`)
- `mode` — `'home' | 'quick' | 'case'`
- `selectedPatient` / `selectedSpecialty` — fluxo de caso clínico
- `file` / `preview` / `results` — análise rápida

### 4.5 URL do Backend

```js
const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
```

Em produção, `VITE_API_URL` deve ser definida na Vercel apontando para o Railway.

---

## 5. Infraestrutura de Deploy

### 5.1 Vercel (Frontend)

`vercel.json`:
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/index" },
    { "source": "/(.*)",       "destination": "/index.html"  }
  ]
}
```

A rewrite `/api/*` existe como fallback para a função Python em `api/index.py`. Em produção o frontend usa `VITE_API_URL` apontando diretamente para o Railway.

### 5.2 Railway (Backend)

- Start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- Python 3.11 (via `.python-version`)
- Variáveis de ambiente configuradas no painel do Railway

### 5.3 Supabase

- Banco PostgreSQL gerenciado
- **Usar obrigatoriamente a URL do Connection Pooler** (Session mode, porta 5432):
  ```
  postgresql://postgres.[projeto]:[senha]@aws-0-[região].pooler.supabase.com:5432/postgres
  ```
- Motivo: Railway resolve DNS em IPv6 para a URL direta; o pooler responde em IPv4.
- Storage bucket `medical-images` para imagens enviadas (opcional, via Supabase SDK).

---

## 6. Segurança

| Item                  | Status                                      |
|-----------------------|---------------------------------------------|
| HTTPS                 | Garantido por Vercel e Railway              |
| JWT                   | HS256, 30 dias, `SECRET_KEY` via env        |
| Senhas                | bcrypt (passlib)                            |
| SQL Injection         | Prevenido por SQLAlchemy ORM               |
| CORS                  | `allow_origins=["*"]` — aceitável para API pública de IA |
| Secrets em código     | Nenhum — todos via env vars                 |
| `SECRET_KEY` padrão   | **ALTERAR EM PRODUÇÃO** (Railway env var)   |
| Arquivos temporários  | Limpos após uso (`os.remove`)               |
| Validação de formato  | Extensões permitidas: jpg/jpeg/png/bmp/gif/dcm |

---

## 7. Desenvolvimento Local

### Pré-requisitos
- Python 3.11
- Node.js 18+
- Chaves: `GROQ_API_KEY` (obrigatório), `TAVILY_API_KEY` (opcional)

### Setup

```powershell
# Terminal 1 — Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
# → http://localhost:8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

`.env` na raiz do projeto:
```env
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly_...   # opcional
SECRET_KEY=dev-only-secret
# DATABASE_URL omitido → SQLite em /tmp
```

---

## 8. Problemas Conhecidos e Decisões Técnicas

| Problema | Causa | Solução Adotada |
|----------|-------|-----------------|
| Railway não conecta ao Supabase | Railway usa IPv6, Supabase direct URL resolve IPv6 | Usar URL do Connection Pooler (IPv4) |
| `load_dotenv("../. env")` em produção | Caminho relativo inexistente no Railway | Ignorado silenciosamente; vars vêm do painel |
| Bundle Vercel Python pesado | agno + numpy + Pillow > limite | Backend em Railway é deploy preferencial |
| DICOM sem visualização no browser | Formato binário proprietário | Placeholder de ícone + análise via backend |

---

## 9. Roadmap

- [ ] Geração de PDF com layout visual aprimorado (WeasyPrint)
- [ ] Correlação de laudos textuais (PDF laboratorial) com imagens
- [ ] Roteamento multi-especialista (Agente Oncologista, Ortopedista, etc.)
- [ ] Citations no formato ABNT/PubMed nos prompts de pesquisa
- [ ] Rate limiting nos endpoints de análise
- [ ] Testes automatizados (pytest + Playwright)
