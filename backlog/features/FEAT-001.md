# FEAT-001: Casos Clinicos na HistoryPanel

**Status:** Backlog
**Prioridade:** Alta
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

O endpoint `GET /api/cases` existe no backend e retorna os casos clinicos salvos do usuario logado, mas o componente `HistoryPanel` do frontend consome apenas `GET /api/history` (que retorna somente `ExamRecord` de quick analysis). O usuario nao ve seus casos clinicos completos no historico — dados ja existem no banco, apenas nao sao exibidos.

## Valor de Negocio

Casos clinicos sao o produto principal da plataforma. Um medico que salvou um caso completo (multiplos exames, correlacao clinica, laudo por especialidade) nao consegue recupera-lo pela UI. Isso gera perda de confianca e impossibilita o uso da plataforma como repositorio clinico.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-001 | Ver lista de casos clinicos no historico | Backlog |
| US-002 | Distinguir quick analysis de caso clinico no historico | Backlog |
| US-003 | Navegar para detalhe de um caso clinico a partir do historico | Backlog |

## Dependencias

### Depende de:
- Nenhuma. O endpoint `GET /api/cases` ja existe e funciona.

### Bloqueia:
- FEAT-003: Visualizacao de Caso Salvo depende de ter a lista de casos acessivel na UI
- FEAT-005: Historico Unificado depende que ambos os tipos de registro sejam visiveis

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | UX | A mistura de dois tipos de item (ExamRecord e ClinicalCase) na mesma lista pode confundir o usuario se nao houver distinção visual clara | Medio | Usar badge/tag de tipo (Quick / Caso Clinico) e icone diferente |
| R2 | Tecnico | O schema de resposta de `/api/cases` difere de `/api/history` — o frontend precisara normalizar dois formatos distintos | Medio | Criar funcao adaptadora no frontend antes de renderizar |
| R3 | Negocio | Usuario pode ter dezenas de casos salvos; sem paginacao o endpoint retorna tudo | Baixo | Endpoint ja tem limit=50 para history; verificar se /api/cases tem o mesmo limite e adicionar se necessario |

## Conflitos Identificados

- **FEAT-005 (Historico Unificado):** Ha sobreposicao de escopo. FEAT-001 exibe casos em aba separada dentro da HistoryPanel existente; FEAT-005 funde tudo em uma timeline unica. Resolucao proposta: implementar FEAT-001 como passo intermediario (aba "Casos" na HistoryPanel), e FEAT-005 unifica e substitui essa aba depois. Nao duplicar trabalho.

## Criterios de Conclusao (Definition of Done)

- [ ] Todas as user stories aceitas pelo PO
- [ ] Testes automatizados passando (>=80% cobertura)
- [ ] Revisao de codigo aprovada
- [ ] Documentacao atualizada
- [ ] Deploy em staging validado

## Historico

| Data | Evento | Autor |
|------|--------|-------|
| 2026-06-06 | Feature criada via discovery do backlog | backlog-manager |
