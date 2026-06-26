# Registro de Riscos

> Ultima atualizacao: 2026-06-06

## Riscos Ativos

| ID | Feature | Tipo | Descricao | Severidade | Probabilidade | Mitigacao | Status |
|----|---------|------|-----------|------------|---------------|-----------|--------|
| RISK-001 | FEAT-002 | Seguranca | IDOR: endpoint DELETE /api/patients/{id} sem verificacao de user_id permite que usuario A exclua paciente de usuario B | Critico | Alta (sem o endpoint, e garantido que o bug existe quando for criado sem cuidado) | Filtrar por patient.user_id == current_user.id; retornar 404 (nao 403); teste de integracao com dois usuarios | Aberto |
| RISK-002 | FEAT-002 | Operacional | Cascade delete apaga ClinicalCase vinculados ao paciente sem aviso claro ao usuario | Alto | Alta | Dialogo de confirmacao explicito mencionando dados que serao perdidos; considerar soft-delete | Aberto |
| RISK-003 | FEAT-004 | Tecnico | Tres abordagens disponiveis para persistencia anonima com trade-offs distintos; escolha errada gera retrabalho significativo | Alto | Media | Decisao de produto necessaria antes de implementar: recomendar abordagem (c) — salvar no DB com anon_token e transferir no login | Aberto |
| RISK-004 | FEAT-004 | Seguranca | Token anonimo previsivel permite que atacante reivindique caso de outro usuario | Alto | Baixa | Usar secrets.token_urlsafe(32); validar que token nao esta vinculado a outro user_id antes de transferir | Aberto |
| RISK-005 | FEAT-004 | Operacional | Registros com user_id=null acumulam no banco sem TTL — poluicao de dados | Medio | Alta | Job de limpeza que deleta registros anonimos com mais de 7 dias | Aberto |
| RISK-006 | FEAT-004 | Tecnico | ClinicalCase.user_id tem nullable=False no SQLAlchemy — alterar em producao sem Alembic pode corromper dados | Alto | Alta | Implementar FEAT-010 (Alembic) antes de FEAT-004; nunca alterar schema em producao via create_all | Aberto |
| RISK-007 | FEAT-007 | Tecnico | Endpoint /api/pdf atual nao suporta estrutura multi-secao do caso clinico; modificar o endpoint quebra Quick Analysis em producao | Alto | Alta | Criar endpoint separado /api/pdf/case; nunca alterar o endpoint existente | Aberto |
| RISK-008 | FEAT-008 | Negocio | Sem rate limiting, um usuario malicioso (ou bug de retry loop) pode esgotar cota da API Groq gerando custos nao controlados | Alto | Media | Implementar slowapi com limites por endpoint antes do proximo ciclo de marketing/lancamento | Aberto |
| RISK-009 | FEAT-009 | Seguranca | DSN do Sentry hardcodado no codigo expoe o endpoint de telemetria | Critico | Baixa (risco futuro ao implementar) | Sempre usar variavel de ambiente SENTRY_DSN; nunca commitar o DSN | Aberto |
| RISK-010 | FEAT-010 | Operacional | Baseline incorreto do Alembic pode tentar recriar tabelas existentes em producao, causando erro de startup | Alto | Media | Gerar baseline em ambiente de staging espelhando producao; executar alembic stamp head manualmente antes do primeiro deploy | Aberto |
| RISK-011 | FEAT-001 | UX | Mistura de ExamRecord e ClinicalCase na HistoryPanel sem diferenciacao visual confunde o usuario | Medio | Alta | Badge de tipo (Quick / Caso Clinico) obrigatorio; icone diferente por tipo | Aberto |
| RISK-012 | FEAT-003 | Tecnico | exams_summary armazenado como JSON string sem versao — mudanca de formato no backend quebra views existentes silenciosamente | Medio | Media | Adicionar campo version ao JSON; validar schema no frontend ao ler | Aberto |
| RISK-013 | FEAT-003 | Negocio | Imagens originais dos exames nao sao armazenadas — usuario pode esperar ver as imagens e se frustrar | Medio | Alta | Indicar explicitamente na view de detalhe que apenas o laudo textual esta disponivel | Aberto |
| RISK-014 | FEAT-005 | UX | FEAT-001 adiciona aba de casos na HistoryPanel existente; FEAT-005 depois substituiria essa estrutura — retrabalho garantido se implementadas em sequencia sem planejamento | Medio | Alta | Decisao de produto: ou implementar FEAT-005 diretamente (pulando FEAT-001), ou aceitar que parte do trabalho de FEAT-001 sera refeito | Aberto |
| RISK-015 | Transversal | Tecnico | Zero cobertura de testes automatizados — qualquer refatoracao pode quebrar os pipelines de IA sem deteccao | Alto | Alta | Priorizar FEAT-009 (testes) antes das proximas features de alta complexidade | Aberto |

## Riscos Resolvidos

| ID | Feature | Descricao | Resolucao | Data |
|----|---------|-----------|-----------|------|
| — | — | — | — | — |
