# Mapa de Dependencias

> Ultima atualizacao: 2026-06-06

## Grafo de Dependencias

```
FEAT-001 (Casos na HistoryPanel)
  └─▶ FEAT-003 (Visualizacao de Caso Salvo)
        └─▶ FEAT-005 (Historico Unificado)
        └─▶ FEAT-007 (Exportar Caso como PDF)
              └─▶ US-019 (Download PDF do historico)

FEAT-010 (Alembic)
  └─▶ FEAT-004 (Persistencia Anonima)
        └─▶ US-011 (Transferencia apos login)
  └─▶ US-024 (Cache de analise — coluna file_hash)

US-001 (Lista de casos)
  └─▶ US-002 (Badge de tipo)
  └─▶ US-003 (Clique → detalhe)

US-004 (Delete de paciente)
  └─▶ US-005 (Feedback visual)

US-006 (Abrir caso)
  └─▶ US-007 (Abas no modo leitura)
  └─▶ US-008 (PDF do historico)
        └─▶ US-018 (Endpoint /api/pdf/case)

US-009 (Analise anonima)
  └─▶ US-010 (CTA de registro)
  └─▶ US-011 (Transferencia apos login)

US-012 (Timeline unificada)
  └─▶ US-013 (Filtro por especialidade)
  └─▶ US-014 (Filtro por paciente)
  └─▶ US-015 (Filtro por datas)

US-016 (Grafico de peso)
  └─▶ US-017 (Grafico de altura)

US-018 (Endpoint PDF para casos)
  └─▶ US-019 (Download PDF do historico)

US-023 (Logging + Sentry): independente
US-021 (Rate limit): independente
US-022 (Validacao CaseWizard): independente
US-025 (Alembic): independente
```

## Tabela de Dependencias

| Artefato | Depende de | Motivo | Status da Dependencia |
|----------|-----------|--------|----------------------|
| FEAT-003 | FEAT-001 | Lista de casos na UI precisa existir antes da view de detalhe | Backlog |
| FEAT-005 | FEAT-001 | Timeline unificada pressupoe que casos estao visiveis na UI | Backlog |
| FEAT-005 | FEAT-003 | Ao clicar em um item, precisa de rota de detalhe | Backlog |
| FEAT-007 | FEAT-003 | US-019 (download do historico) requer a view de detalhe | Backlog |
| FEAT-004 | FEAT-010 | `user_id nullable` no schema requer migracao Alembic segura | Backlog |
| US-002 | US-001 | Badge de tipo e apresentado sobre a lista de casos | Backlog |
| US-003 | US-001 | Clique em item da lista dispara navegacao para detalhe | Backlog |
| US-005 | US-004 | Feedback visual depende do endpoint de delete existir | Backlog |
| US-007 | US-006 | Abas sao parte da view de detalhe | Backlog |
| US-008 | US-006 | Botao de PDF fica na view de detalhe | Backlog |
| US-008 | US-018 | Endpoint /api/pdf/case precisa existir | Backlog |
| US-010 | US-009 | CTA aparece apos analise anonima existir | Backlog |
| US-011 | US-009 | Transferencia pressupoe que houve analise anonima | Backlog |
| US-011 | FEAT-010 | Schema com user_id nullable | Backlog |
| US-013 | US-012 | Filtros sao adicionados sobre a timeline | Backlog |
| US-014 | US-012 | Filtros sao adicionados sobre a timeline | Backlog |
| US-015 | US-012 | Filtros sao adicionados sobre a timeline | Backlog |
| US-017 | US-016 | Grafico de altura reutiliza componente de grafico | Backlog |
| US-019 | US-018 | Download usa o endpoint criado em US-018 | Backlog |
| US-019 | US-006 | Botao fica na view de detalhe | Backlog |
| US-024 | FEAT-010 | Adicionar coluna file_hash requer migracao Alembic | Backlog |

## Dependencias Criticas (bloqueadoras)

| Artefato Bloqueado | Bloqueador | Acao Necessaria |
|-------------------|------------|-----------------|
| FEAT-003 | FEAT-001 | Implementar FEAT-001 primeiro; FEAT-003 pode comecar com stub "Em breve" |
| FEAT-004 | FEAT-010 | Implementar Alembic antes de alterar schema de ClinicalCase em producao |
| US-011 | FEAT-010 | Mesma razao — user_id nullable e migracao de schema |
| US-024 | FEAT-010 | Coluna file_hash requer migracao antes de ser usada |
| FEAT-005 | FEAT-001 + FEAT-003 | Nao iniciar sem ambas concluidas — retrabalho garantido |
