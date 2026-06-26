# FEAT-010: Migracao de Schema com Alembic

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

O backend usa `Base.metadata.create_all()` na startup para criar as tabelas. Isso funciona para criacao inicial, mas e incapaz de aplicar mudancas de schema em tabelas ja existentes (adicionar coluna, alterar tipo, criar indice). Qualquer alteracao de modelo que nao seja additive silenciosamente ignora os dados em producao ou causa erro de startup.

Esta feature instala e configura o Alembic para gerenciamento de migracoes de schema de forma versionada e reproduzivel.

## Valor de Negocio

Sem Alembic, toda mudanca de schema em producao e um risco operacional: ou se faz manualmente via SQL no Supabase (propenso a erro), ou se apaga e recria as tabelas (perda de dados). Com a plataforma em crescimento, mudancas de schema serao frequentes (ex: FEAT-004 requer `user_id nullable`).

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-025 | Schema do banco atualizado automaticamente no deploy sem perda de dados | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia bloqueadora.

### Bloqueia:
- FEAT-004: Persistencia de Casos Anonimos requer `user_id nullable` na tabela `clinical_cases` — uma migracao Alembic e a forma segura de fazer isso em producao

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Operacional | A migracao inicial (baseline) precisa ser gerada a partir do schema atual ja existente em producao no Supabase. Se feita errado, o Alembic pode tentar recriar tabelas que ja existem | Alto | Gerar baseline com `alembic stamp head` apontando para o schema atual. Testar em ambiente de staging antes de producao |
| R2 | Operacional | O `create_all()` na startup precisa ser removido ou tornado um no-op apos Alembic estar configurado. Manter os dois em paralelo causa conflito | Medio | Substituir `create_all()` por `alembic upgrade head` no script de startup do Railway |
| R3 | Tecnico | Alembic nao detecta automaticamente renomeacao de colunas — trata como drop + add, o que perde dados | Baixo | Documentar que renomeacoes devem ser feitas manualmente com `op.alter_column()` |

## Conflitos Identificados

- Nenhum conflito com outras features. E uma feature de infraestrutura independente.

## Criterios de Conclusao (Definition of Done)

- [ ] Todas as user stories aceitas pelo PO
- [ ] Testes automatizados passando (>=80% cobertura)
- [ ] Revisao de codigo aprovada
- [ ] Documentacao atualizada
- [ ] Deploy em staging validado — incluindo rollback de migracao testado

## Historico

| Data | Evento | Autor |
|------|--------|-------|
| 2026-06-06 | Feature criada via discovery do backlog | backlog-manager |
