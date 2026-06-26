# FEAT-004: Persistencia de Casos de Usuarios Anonimos

**Status:** Backlog
**Prioridade:** Alta
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

Hoje, quando um usuario nao autenticado realiza uma analise de caso clinico (`POST /api/cases/analyze`), o resultado e exibido na tela mas nao e salvo no banco (o backend requer `user_id` para persistencia). Se o usuario fechar a aba ou navegar, o laudo e perdido para sempre. O objetivo e permitir que o usuario recupere o resultado apos fazer login/registro, sem perder o trabalho ja feito.

## Valor de Negocio

A friccao de "faca login antes de usar" e um dos maiores inibidores de conversao em produtos SaaS. Permitir o uso primeiro e pedir o cadastro depois aumenta a ativacao e a taxa de conversao de anonimos para usuarios registrados.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-009 | Usar o sistema sem login e ter o resultado preservado durante a sessao | Backlog |
| US-010 | Ser solicitado a criar conta para salvar o resultado antes de perder | Backlog |
| US-011 | Apos login, ver o resultado anonimo transferido para minha conta | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia tecnica bloqueadora. O fluxo de auth ja existe; o desafio e o gerenciamento de estado transitorio.

### Bloqueia:
- Nenhuma feature depende diretamente deste comportamento.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | Tres abordagens possiveis com trade-offs distintos: (a) localStorage no frontend, (b) sessao temporaria no backend com TTL, (c) salvar no DB com `user_id=null` e transferir apos login. A escolha errada gera retrabalho | Alto | Decidir abordagem antes de implementar: recomendado (c) — salvar com `user_id=null` e `session_token` (UUID anonimo em cookie), transferir no login. Mais robusto e permite recuperacao em outra aba |
| R2 | Operacional | Registros `user_id=null` permanentes poluem o banco. Sem limpeza, viram lixo acumulado | Medio | Job de limpeza (cron ou startup hook) que deleta registros anonimos com mais de 7 dias sem transferencia |
| R3 | Seguranca | Se o `session_token` anonimo for previsivel, um atacante pode reivindicar o caso de outro usuario | Alto | UUID v4 gerado com `secrets.token_urlsafe(32)`; validar que o token nao esta vinculado a outro user antes de transferir |
| R4 | UX | O usuario pode nao perceber que o resultado sera perdido ao fechar o navegador | Medio | Banner/aviso persistente: "Seu laudo nao esta salvo. Crie uma conta gratuita para salvar." |

## Conflitos Identificados

- O modelo `ClinicalCase` tem `user_id` com `nullable=False` no SQLAlchemy. A abordagem (c) requer alterar o schema para `nullable=True` — isso e uma migracao de banco que depende de Alembic (FEAT-010) ou deve ser feita manualmente com cuidado.

## Criterios de Conclusao (Definition of Done)

- [ ] Todas as user stories aceitas pelo PO
- [ ] Testes automatizados passando (>=80% cobertura)
- [ ] Revisao de codigo aprovada — validar seguranca do token anonimo
- [ ] Documentacao atualizada
- [ ] Deploy em staging validado

## Historico

| Data | Evento | Autor |
|------|--------|-------|
| 2026-06-06 | Feature criada via discovery do backlog | backlog-manager |
