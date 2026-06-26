# MedAI Diagnostics — TODO

> Atualizado: 2026-06-06

---

## ✅ Concluído

### Infra & Deploy
- [x] Backend FastAPI no Railway (Python 3.11)
- [x] Frontend React 19 + Vite no Vercel
- [x] Banco Supabase PostgreSQL via Connection Pooler (IPv4)
- [x] `vercel.json` com roteamento `/api/*` → Railway, SPA catch-all
- [x] `.python-version` e `requirements.txt` para compatibilidade Vercel
- [x] `seguranca.md` com guia de segurança do projeto

### Auth
- [x] Registro e login com email/senha
- [x] JWT (`python-jose`) + bcrypt via `auth.py`
- [x] `get_optional_user` / `get_required_user` para rotas mistas
- [x] Token persistido no `localStorage` (frontend)
- [x] `AuthModal` (login + registro em modal)

### Pipeline de IA — Quick Analysis
- [x] `agents.py`: Medical Image Agent (vision, LLaMA Scout 17B) → Research Agent (LLaMA 70B + Tavily)
- [x] Suporte a DICOM (pydicom + numpy), JPG, PNG, BMP
- [x] Pré-processamento: redimensiona para 600px, normaliza HU para DICOM
- [x] Prompt estruturado em 4 seções PT-BR (tipo/região, achados, diagnóstico, linguagem leiga)
- [x] Remoção de tokens `<think>` do chain-of-thought
- [x] Suporte a Tavily opcional (pesquisa web complementar)
- [x] Endpoint `POST /api/analyze`

### Pipeline de IA — Case Analysis
- [x] `case_agents.py`: agente por especialidade com prompts sistematizados
- [x] Especialidades cobertas: spine, neuro, thorax, abdomen, msk, cardio, endocrino, onco, breast, nutri
- [x] Prompts especializado por modalidade (TIRADS, Lung-RADS, BI-RADS, LI-RADS, Kellgren-Lawrence)
- [x] Correlação clínica cross-exames (múltiplos exames no mesmo caso)
- [x] Documentos (PDF/DOCX) extraídos como contexto textual para os agentes
- [x] Endpoint `POST /api/cases/analyze`
- [x] Persistência do caso no DB após análise (usuários logados)

### Pipeline de IA — Classificação de Arquivos
- [x] `classify_files_with_vision()` — LLaMA Scout identifica modalidade+região real da imagem
- [x] Frontend agrupa automaticamente múltiplos drops em blocos de exame
- [x] Documentos (PDF/DOC) são separados das imagens automaticamente
- [x] Endpoint `POST /api/classify-files`

### Pipeline de IA — Leitura de Documentos
- [x] `doc_parser.py`: extrai texto de PDF (pypdf) e DOCX (python-docx)
- [x] PDFs escaneados (sem texto): OCR via LLaMA Scout (vision) como fallback
- [x] Documentos injetados como contexto nos agentes de diagnóstico

### Pipeline de IA — Sugestões
- [x] `generate_suggestion()`: gera sugestões de dieta/exercício/hábitos por especialidade
- [x] Endpoint `POST /api/suggest`
- [x] Frontend exibe botão de sugestão para especialidades cabíveis (spine/msk → exercícios, cardio → hábitos, endocrino/nutri → dieta)

### Banco de Dados (`database.py`)
- [x] SQLAlchemy + PostgreSQL (Supabase) com fallback SQLite em `/tmp`
- [x] Tabelas: `users`, `exam_records`, `patients`, `patient_metrics`, `patient_conditions`, `clinical_cases`
- [x] `POST /api/analyze` salva `ExamRecord` para usuários logados
- [x] `POST /api/cases/analyze` salva `ClinicalCase` + cria `Patient` automaticamente
- [x] Endpoint de diagnóstico: `GET /api/dbcheck`

### Pacientes
- [x] CRUD completo: `GET/POST /api/patients`, `GET/PUT /api/patients/{id}`
- [x] Métricas de saúde: `POST /api/patients/{id}/metrics` (peso, altura)
- [x] Condições clínicas: `POST/DELETE /api/patients/{id}/conditions`
- [x] Casos por paciente: `GET /api/patients/{id}/cases`
- [x] `PatientPanel` no frontend (lista + criação de pacientes)
- [x] `PatientSelector` no wizard (seleciona ou cria paciente antes da análise)

### Frontend — Fluxo Principal
- [x] `SpecialtyDashboard` — grid de especialidades para usuários logados (tiers 1/2/geral)
- [x] `CaseWizard` — wizard de análise com múltiplos exames + documentos
  - [x] Multi-upload por exame com drag-drop
  - [x] Autodetecção de nome do exame a partir do arquivo
  - [x] Campo de queixa principal
  - [x] Contexto do paciente (nome, data de nasc., sexo, peso, altura, condições)
  - [x] Abas de resultado: Análise Detalhada, Correlação, Profissional, Leigo, Sugestão, Referências
  - [x] Botão de geração de sugestão (diet/exercício) por especialidade
- [x] Quick Analysis (modo legado, único arquivo)
- [x] `HistoryPanel` — histórico de exames do usuário
- [x] Download de laudo em PDF (`pdf_generator.py` com fpdf2)
- [x] Header responsivo (login/logout, pacientes, histórico)

---

## 🔧 Em Andamento / Pendente

### Alta prioridade

- [ ] **Casos na HistoryPanel** — `GET /api/cases` existe mas a `HistoryPanel` só mostra `ExamRecord` (quick analysis). Exibir casos clínicos no histórico também.
- [ ] **Delete de paciente** — endpoint `DELETE /api/patients/{id}` não existe. Botão de exclusão no `PatientPanel` sem backend.
- [ ] **Edição de caso salvo** — não há como re-abrir e re-analisar um caso existente. Ver caso salvo em modo read-only.
- [ ] **Salvar casos de usuários anônimos** — atualmente casos de quem não está logado são perdidos.

### Média prioridade

- [ ] **Histórico unificado** — view que mistura quick analyses + casos clínicos em timeline, com filtros (data, especialidade, paciente).
- [ ] **Visualização de caso salvo** — página/modal para ver o laudo de um caso salvo do histórico.
- [ ] **Métricas do paciente em gráfico** — plotar peso/altura ao longo do tempo na `PatientPanel`.
- [ ] **Exportar caso como PDF** — o `CaseWizard` tem botão de PDF mas o endpoint usa `analysis`/`research` raw; integrar com o layout multi-seção do `CaseWizard`.
- [ ] **Validação de formulário** — o CaseWizard não valida se há ao menos 1 exame com arquivo antes de submeter.
- [ ] **Rate limiting no backend** — nenhum endpoint tem rate limit. Usar `slowapi` no FastAPI.
- [ ] **Timeout e retry no frontend** — análises longas podem falhar silenciosamente. Adicionar timeout explícito e feedback de progresso.

### Baixa prioridade / Melhorias

- [ ] **Comparação de exames** — tela lado a lado para comparar dois laudos do mesmo paciente.
- [ ] **Filtro por especialidade no histórico** — filtrar `HistoryPanel` por tipo de exame ou especialidade.
- [ ] **Share de laudo** — gerar link temporário de compartilhamento (estilo Google Docs viewer) para enviar ao médico.
- [ ] **PWA / Service Worker** — instalável no celular, funciona offline para visualizar laudos salvos.
- [ ] **Modo escuro** — dark mode toggle, especialmente útil para visualizar imagens médicas.
- [ ] **Suporte a múltiplos idiomas** — internacionalização (pelo menos EN + PT-BR).
- [ ] **Notificações** — notificar por email quando a análise de um caso demorado finalizar.
- [ ] **Deletar exame do histórico** — usuário não consegue remover um exame errado do histórico.
- [ ] **Upload de DICOM multi-slice** — suporte a séries DICOM (múltiplos .dcm de um mesmo estudo).

### DevOps / Qualidade

- [ ] **Testes automatizados** — zero cobertura atualmente. Priorizar testes de integração para os endpoints críticos (`/analyze`, `/cases/analyze`).
- [ ] **CI/CD** — pipeline GitHub Actions para rodar testes e fazer deploy automático.
- [ ] **Logging estruturado** — substituir `print()` por `logging` com níveis e JSON no backend.
- [ ] **Monitoramento** — Sentry ou similar para rastrear erros em produção no Railway.
- [ ] **Caching de análise** — se o mesmo arquivo for subido duas vezes, retornar resultado do cache (hash do arquivo).
- [ ] **Migração de schema** — usar Alembic para versionamento do schema do banco (hoje é `create_all` na startup).
