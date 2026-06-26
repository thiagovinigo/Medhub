# FEAT-003: Visualizacao de Caso Salvo (read-only)

**Status:** Backlog
**Prioridade:** Alta
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

Apos o usuario clicar em um caso clinico na HistoryPanel (entregue por FEAT-001), ele precisa ver o conteudo completo do caso — laudo, correlacao, secoes por especialidade, pesquisa — em modo leitura. Nao ha hoje nenhuma rota ou modal para exibir um caso salvo: o `CaseWizard` e um formulario de entrada, nao uma view de resultado persistido.

Nota: o backlog original lista "Editar e re-analisar" como requisito desta feature. Isso esta fora do escopo aqui — re-analise e uma feature separada e mais complexa (FEAT-003 foca apenas em visualizacao read-only).

## Valor de Negocio

O historico sem a capacidade de visualizar o conteudo e inutil. O medico precisa consultar laudos anteriores para comparacao clinica e continuidade do cuidado.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-006 | Abrir caso salvo em modal/pagina de leitura | Backlog |
| US-007 | Navegar entre secoes do laudo (abas) no modo leitura | Backlog |
| US-008 | Baixar PDF de um caso salvo diretamente do historico | Backlog |

## Dependencias

### Depende de:
- FEAT-001: a lista de casos precisa estar acessivel na UI para o usuario poder clicar em um item — Status: Backlog

### Bloqueia:
- FEAT-005: Historico Unificado precisa de uma rota de detalhe para cada tipo de registro
- FEAT-007: Exportar caso como PDF usa os mesmos dados renderizados aqui

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | O backend armazena `exams_summary` como JSON string e `analysis`/`research` como texto livre. A view precisa parsear e renderizar esses campos de forma estruturada — qualquer mudanca de formato no backend quebraria a view | Medio | Versionar o formato do JSON em `exams_summary` (campo `version`). Adicionar schema validation no frontend ao ler |
| R2 | UX | O layout do CaseWizard e altamente interativo (drag-drop, abas de input). Reutilizar o mesmo componente para exibicao read-only pode gerar confusao | Medio | Criar um componente `CaseReportView` separado, reutilizando apenas as abas de resultado |
| R3 | Negocio | Imagens originais dos exames nao sao armazenadas (apenas o laudo textual). O usuario pode esperar ver as imagens e se frustrar | Medio | Indicar claramente na view que apenas o laudo esta disponivel; imagens nao sao persistidas |

## Conflitos Identificados

- **Backlog original mistura "ver caso" e "re-analisar caso"** em um unico item. Separar: FEAT-003 = visualizacao; re-analise = feature futura com escopo proprio (requer novo upload de arquivos ou armazenamento de imagens, o que e uma decisao de produto separada).

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
