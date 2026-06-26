# FEAT-007: Exportar Caso Clinico como PDF (CaseWizard)

**Status:** Backlog
**Prioridade:** Media
**Criado em:** 2026-06-06
**Ultima atualizacao:** 2026-06-06

---

## Descricao

O `CaseWizard` ja possui botao "Gerar PDF", mas o endpoint `POST /api/pdf` recebe apenas os campos `analysis` e `research` (formato do Quick Analysis) e nao contempla a estrutura multi-secao do caso clinico (correlacao, laudo por especialidade, contexto do paciente, dados dos exames). O PDF gerado para casos clinicos e incompleto ou incorreto.

## Valor de Negocio

O PDF e o artefato de saida principal da plataforma — e o documento que o medico imprime, envia ao paciente ou arquiva no prontuario. Um PDF com estrutura errada compromete a credibilidade da plataforma.

## User Stories Relacionadas

| ID | Titulo | Status |
|----|--------|--------|
| US-018 | Gerar PDF completo de um caso clinico com todas as secoes | Backlog |
| US-019 | Baixar PDF de um caso ja salvo a partir do historico | Backlog |

## Dependencias

### Depende de:
- FEAT-003: a view de caso salvo (historico) precisa existir para que US-019 faca sentido — Status: Backlog

### Bloqueia:
- Nenhuma feature depende de FEAT-007.

## Riscos

| # | Tipo | Descricao | Severidade | Mitigacao |
|---|------|-----------|------------|-----------|
| R1 | Tecnico | O `pdf_generator.py` usa fpdf2 com um layout fixo de 2 colunas para `analysis` + `research`. Adicionar secoes de correlacao, especialidade, contexto do paciente e exames requer refatoracao significativa do gerador | Alto | Criar um novo endpoint `POST /api/pdf/case` especifico para casos clinicos com schema proprio, em vez de sobrecarregar o endpoint existente. Manter `/api/pdf` para quick analysis sem alteracoes |
| R2 | UX | Usuarios esperam que o PDF tenha aparencia profissional (cabecalho com logo, rodape com data/assinatura) | Medio | Adicionar cabecalho e rodape padrao no `pdf_generator.py`; definir layout antes de implementar |

## Conflitos Identificados

- **Conflito com endpoint existente `/api/pdf`:** Nao modificar o schema do endpoint atual — ele serve o Quick Analysis e ja esta em producao. Criar endpoint separado `/api/pdf/case`.

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
