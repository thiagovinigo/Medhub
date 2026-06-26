# FEAT-006: Metricas do Paciente em Grafico

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

O backend ja persiste `PatientMetric` com data, peso e altura. O `PatientPanel` exibe metricas como lista de texto, mas nao as visualiza graficamente. Plotar peso e altura ao longo do tempo em um grafico de linha simples dentro do painel do paciente.

## Valor de Negocio

Visualizacao de tendencias de peso/altura ao longo do tempo e diretamente relevante para especialidades como nutricao, endocrinologia e cardiologia — especialidades ja suportadas pela plataforma. Aumenta o valor clinico da ficha do paciente.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-016 | Ver grafico de evolucao de peso ao longo do tempo no perfil do paciente | Backlog |
| US-017 | Ver grafico de evolucao de altura no perfil do paciente | Backlog |

## Dependencias

### Depende de:
- Nenhuma dependencia bloqueadora. Dados ja existem no backend (`/api/patients/{id}` retorna `metrics`).

### Bloqueia:
- Nenhuma feature depende de FEAT-006.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | Adicionar uma biblioteca de graficos (Recharts, Chart.js, Victory) aumenta o bundle do frontend. Para um grafico simples, o impacto pode ser desproporcionalmente grande | Baixo | Usar Recharts (ja popular em React) ou implementar SVG simples sem biblioteca para 2 series de dados |
| R2 | UX | Pacientes com apenas 1 ou 2 medicoes nao mostram tendencias uteis — o grafico ficara vazio ou enganoso | Baixo | Renderizar o grafico apenas quando houver >=3 medicoes; caso contrario, exibir lista textual |

## Conflitos Identificados

- Nenhum conflito identificado.

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
