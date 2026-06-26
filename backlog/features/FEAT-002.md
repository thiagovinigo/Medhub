# FEAT-002: Delete de Paciente

**Status:** Backlog
**Prioridade:** Alta
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

O `PatientPanel` no frontend ja possui botao de exclusao de paciente, mas o endpoint `DELETE /api/patients/{id}` nao existe no backend. O botao nao faz nada ou falha silenciosamente. Implementar o endpoint com cascata correta e confirmacao no frontend.

## Valor de Negocio

CRUD incompleto gera frustracao imediata: o usuario ve um botao de excluir que nao funciona. Pacientes de teste ou cadastros errados ficam presos no sistema sem remocao possivel.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-004 | Excluir paciente com confirmacao | Backlog |
| US-005 | Feedback visual apos exclusao bem-sucedida | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia externa. O modelo `Patient` ja tem `cascade="all, delete"` configurado no SQLAlchemy, cobrindo metricas, condicoes e casos associados.

### Bloqueia:
- Nenhuma feature depende diretamente deste endpoint.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Operacional | O cascade `all, delete` no SQLAlchemy apaga automaticamente PatientMetric, PatientCondition e ClinicalCase vinculados. Isso pode excluir casos clinicos analisados que o usuario nao pretendia perder | Alto | Exibir aviso explicito na confirmacao: "Todos os casos clinicos e metricas deste paciente serao excluidos permanentemente." Considerar soft-delete como alternativa |
| R2 | Tecnico | Ausencia de verificacao de `user_id` no endpoint permitiria que usuario A exclua paciente de usuario B (IDOR) | Critico | Endpoint DEVE filtrar `patient.user_id == current_user.id` antes de deletar. Testar com usuarios distintos |
| R3 | UX | Nao ha como desfazer a exclusao | Medio | Considerar periodo de graca (soft-delete com flag `deleted_at`) para versao futura |

## Conflitos Identificados

- Nenhum conflito com outras features identificado.

## Criterios de Conclusao (Definition of Done)

- [ ] Todas as user stories aceitas pelo PO
- [ ] Testes automatizados passando (>=80% cobertura)
- [ ] Revisao de codigo aprovada — validar que IDOR nao e possivel (R2 Critico)
- [ ] Documentacao atualizada
- [ ] Deploy em staging validado

## Historico

| Data | Evento | Autor |
|------|--------|-------|
| 2026-06-06 | Feature criada via discovery do backlog | backlog-manager |
