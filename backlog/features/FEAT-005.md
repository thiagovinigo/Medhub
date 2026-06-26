# FEAT-005: Historico Unificado com Filtros

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

Substituir as visualizacoes separadas de quick analysis e casos clinicos por uma timeline unificada que mistura os dois tipos de registro, com filtros por data, especialidade e paciente. Depende de FEAT-001 (casos na UI) e FEAT-003 (detalhe de caso) estarem prontos.

## Valor de Negocio

Um medico que usa a plataforma regularmente acumula dezenas de registros de tipos diferentes. A timeline unificada reduz a cognicao necessaria para encontrar um exame anterior e da a sensacao de repositorio clinico completo.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-012 | Ver todos os registros (quick + caso) em uma unica lista cronologica | Backlog |
| US-013 | Filtrar historico por especialidade | Backlog |
| US-014 | Filtrar historico por paciente | Backlog |
| US-015 | Filtrar historico por intervalo de datas | Backlog |

## Dependencias

### Depende de:
- FEAT-001: casos clinicos precisam aparecer na UI — Status: Backlog
- FEAT-003: ao clicar em um caso, precisa haver uma view de detalhe — Status: Backlog

### Bloqueia:
- Nenhuma feature depende de FEAT-005.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | Unificar dois endpoints (`/api/history` e `/api/cases`) no frontend requer normalizacao de schemas distintos. Alternativa melhor: criar um endpoint `/api/timeline` no backend que retorna os dois tipos paginados e ordenados por data | Medio | Avaliar custo de criar endpoint unificado vs. normalizacao no frontend. Endpoint unico e mais testavel |
| R2 | UX | Filtros multiplos combinados podem gerar estados vazios confusos para o usuario | Baixo | Mostrar mensagem de "Nenhum resultado para os filtros selecionados" com botao para limpar filtros |

## Conflitos Identificados

- **FEAT-001 tem sobreposicao de escopo:** FEAT-001 adiciona aba de casos na HistoryPanel existente; FEAT-005 substitui essa estrutura por uma timeline. Isso significa que o trabalho de FEAT-001 sera parcialmente refeito quando FEAT-005 for implementada. Alternativa: pular FEAT-001 e ir direto para FEAT-005, aceitando que casos ficam invisiveis por mais tempo. Decisao de produto necessaria.

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
