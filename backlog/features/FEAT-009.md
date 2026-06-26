# FEAT-009: Qualidade de Codigo e Observabilidade

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

Agrupa itens de qualidade de engenharia que nao entregam valor ao usuario final diretamente, mas sao pre-requisitos para o desenvolvimento sustentavel da plataforma:

1. **Testes automatizados** — zero cobertura atualmente. Priorizar testes de integracao para `/api/analyze` e `/api/cases/analyze`.
2. **Logging estruturado** — substituir todos os `print()` no backend por `logging` com niveis e formato JSON.
3. **Monitoramento (Sentry)** — rastrear erros em producao no Railway.
4. **CI/CD (GitHub Actions)** — pipeline para rodar testes e fazer deploy automatico.
5. **Caching de analise** — hash de arquivo para evitar reprocessamento duplicado.

## Valor de Negocio

Sem testes, qualquer refatoracao ou nova feature pode quebrar silenciosamente os pipelines de IA. Sem logging e monitoramento, bugs em producao sao descobertos apenas quando usuarios reclamam. O custo de debug sem observabilidade e 5-10x maior.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-023 | Backend retorna erro estruturado com trace id para facilitar debug | Backlog |
| US-024 | Analise do mesmo arquivo nao reprocessa se resultado ja esta em cache | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia bloqueadora. Pode ser iniciado em paralelo com qualquer outra feature.

### Bloqueia:
- Tecnicamente nenhuma feature depende de FEAT-009, mas a ausencia de testes aumenta o risco de regressao em todas as features implementadas depois.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | Testar endpoints que dependem da API Groq requer mocking. Sem mocks, os testes chamam a API real, aumentando custo e criando flakiness | Alto | Usar `pytest-httpx` ou `respx` para mockar chamadas HTTP ao Groq. Criar fixtures realistas de resposta |
| R2 | Operacional | O caching por hash de arquivo requer storage compartilhado (Redis ou DB). Em Railway com SQLite de fallback, Redis nao esta disponivel | Medio | Implementar caching na tabela `exam_records` (busca por hash de arquivo antes de chamar a IA). Nao requer Redis |
| R3 | Negocio | DSN do Sentry exposto no codigo fonte via hardcode | Critico | Sempre usar variavel de ambiente `SENTRY_DSN`; nunca hardcodar |

## Conflitos Identificados

- O item "CI/CD" e independente dos demais. Pode ser um PR separado sem dependencia com logging ou testes.

## Criterios de Conclusao (Definition of Done)

- [ ] Todas as user stories aceitas pelo PO
- [ ] Testes automatizados passando (>=80% cobertura) — este e o criterio principal desta feature
- [ ] Revisao de codigo aprovada
- [ ] Documentacao atualizada
- [ ] Deploy em staging validado

## Historico

| Data | Evento | Autor |
|------|--------|-------|
| 2026-06-06 | Feature criada via discovery do backlog | backlog-manager |
