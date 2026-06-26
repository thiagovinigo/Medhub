# FEAT-008: Seguranca e Resiliencia (Rate Limiting + Timeout + Retry)

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

Agrupa tres itens de resiliencia que compartilham o mesmo escopo de risco de producao:

1. **Rate limiting no backend** — nenhum endpoint tem limite de requisicoes. Endpoints de analise de IA (que consomem tokens da Groq) sao especialmente vulneraveis a abuso e custos nao controlados.
2. **Timeout e retry no frontend** — requisicoes de analise longas (15-40s) falham silenciosamente sem feedback. O usuario nao sabe se deve esperar ou re-submeter.
3. **Validacao de formulario no CaseWizard** — o wizard submete sem validar se ha ao menos um arquivo carregado por exame.

Estes tres itens sao agrupados porque compartilham o mesmo objetivo: tornar o sistema seguro e confiavel em condicoes reais de uso.

## Valor de Negocio

Sem rate limiting, um unico usuario malicioso (ou um bug no frontend causando requisicoes em loop) pode esgotar a cota da API Groq e derrubar o servico para todos os usuarios. O custo mensal da API pode escalar de forma nao controlada.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-020 | Receber mensagem clara quando o servidor esta processando uma analise longa | Backlog |
| US-021 | Ver erro explicativo se o limite de requisicoes for atingido | Backlog |
| US-022 | Nao conseguir submeter o CaseWizard sem ao menos um arquivo carregado | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia bloqueadora.

### Bloqueia:
- Nenhuma feature depende de FEAT-008.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | `slowapi` usa Redis ou memoria local para contagem de requisicoes. Em Railway com instancia unica, memoria local funciona. Com multiplas instancias (scale-out), cada instancia tem seu proprio contador — o limite efetivo seria N x limite configurado | Medio | Usar memoria local inicialmente (aceitavel para escala atual). Documentar a limitacao para quando houver scale-out |
| R2 | Negocio | Rate limit muito restritivo bloqueia usuarios legitimos que fazem multiplas analises em sequencia | Medio | Configurar limites por endpoint: analyze = 10/min por IP, auth = 5/min, outros = 60/min |
| R3 | UX | Retry automatico no frontend pode submeter um arquivo grande duas vezes, duplicando o processamento e o custo | Baixo | Retry apenas em erros de rede (timeout, 503); nao fazer retry em erros de negocio (400, 422, 429) |

## Conflitos Identificados

- Nenhum conflito com outras features identificado.

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
