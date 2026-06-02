import React, { useState, useRef } from 'react';
import {
  ArrowRight, ArrowLeft, Plus, X, UploadCloud, FileSearch,
  Stethoscope, Download, FileText,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
const MODALITIES = ['MR', 'CT', 'XR', 'US', 'PET', 'NM', 'Outro'];

const RESULT_TABS = [
  { key: 'detalhada',    label: 'Análise Detalhada' },
  { key: 'correlacao',  label: 'Correlação' },
  { key: 'profissional', label: 'Diagnóstico Profissional', note: 'para médicos' },
  { key: 'leigo',       label: 'Diagnóstico Leigo' },
  { key: 'sugestao',    label: 'Sugestão Médica' },
  { key: 'referencias', label: 'Referências' },
];

function normTitle(s) {
  return (s || '').toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z\s]/g, '').trim();
}

function parseMarkdownTabs(analysis, research) {
  const chunks = [];
  let cur = null;
  const lines = ((analysis || '') + '\n\n' + (research || '')).split('\n');
  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (cur) chunks.push(cur);
      cur = { title: normTitle(line.slice(3)), lines: [] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) chunks.push(cur);

  const find = (...keys) => {
    const c = chunks.find(c => keys.some(k => c.title.includes(k)));
    return c ? c.lines.join('\n').trim() : '';
  };

  const correlacaoBase = find('correlacao clinica', 'correlacao');
  const consolidado = find('diagnostico consolidado', 'recomendacoes');
  return {
    detalhada:    find('analise detalhada', 'analise tecnica', 'analise integrada'),
    correlacao:   [correlacaoBase, consolidado].filter(Boolean).join('\n\n---\n\n'),
    profissional: find('diagnostico profissional', 'impressao diagnostica'),
    leigo:        find('linguagem simples', 'linguagem leiga'),
    sugestao:     find('sugestao medica', 'sugestao'),
    referencias:  find('referencias bibliograficas', 'referencias'),
  };
}

const SPECIALTY_SUGGESTIONS = {
  spine:     { label: 'Sugerir exercícios', type: 'exercise' },
  msk:       { label: 'Sugerir fisioterapia / exercícios', type: 'exercise' },
  endocrino: { label: 'Sugerir dieta', type: 'diet' },
  nutri:     { label: 'Sugerir plano alimentar', type: 'diet' },
  cardio:    { label: 'Sugerir hábitos saudáveis', type: 'lifestyle' },
};

function guessExamName(files) {
  if (!files || files.length === 0) return '';
  const name = files[0].name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ').trim();
  return name.charAt(0).toUpperCase() + name.slice(1);
}

function newExam(card) {
  return { name: '', modality: card?.suggestedModality || '', exam_date: '', files: [] };
}

function ExamBlock({ exam, index, total, onChange, onRemove }) {
  const fileRef = useRef(null);
  const addFiles = (newFiles) =>
    onChange({ ...exam, files: [...exam.files, ...Array.from(newFiles)] });

  return (
    <div className="exam-block">
      <div className="exam-block-header">
        <span className="exam-block-title">Exame {index + 1}</span>
        {total > 1 && (
          <button type="button" className="icon-btn" onClick={onRemove}><X size={16} /></button>
        )}
      </div>

      <div className="form-row">
        <div className="form-group" style={{ flex: 2 }}>
          <label>Nome do exame</label>
          <input className="form-input" placeholder="Ex: RM Coluna Cervical"
            value={exam.name} onChange={e => onChange({ ...exam, name: e.target.value })} />
        </div>
        <div className="form-group">
          <label>Tipo</label>
          <select className="form-input" value={exam.modality}
            onChange={e => onChange({ ...exam, modality: e.target.value })}>
            <option value="">Selecionar...</option>
            {MODALITIES.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label>Data</label>
          <input type="date" className="form-input" value={exam.exam_date}
            onChange={e => onChange({ ...exam, exam_date: e.target.value })} />
        </div>
      </div>

      {exam.files.length > 0 ? (
        <div className="exam-files-list">
          {exam.files.map((f, i) => (
            <div key={i} className="exam-file-chip">
              <FileSearch size={12} /><span>{f.name}</span>
              <button type="button"
                onClick={() => onChange({ ...exam, files: exam.files.filter((_, j) => j !== i) })}>
                <X size={11} />
              </button>
            </div>
          ))}
          <button type="button" className="exam-add-more-btn"
            onClick={() => fileRef.current?.click()}>
            <Plus size={12} /> adicionar mais imagens
          </button>
          <input type="file" ref={fileRef} multiple className="hidden-input"
            accept="image/jpeg,image/png,image/jpg,image/bmp,.dcm"
            onChange={e => addFiles(e.target.files)} />
        </div>
      ) : (
        <div className="exam-upload-area"
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); addFiles(e.dataTransfer.files); }}
          onClick={() => fileRef.current?.click()}>
          <UploadCloud size={24} style={{ color: '#3b82f6', marginBottom: 4 }} />
          <span className="upload-text">Arraste ou <span>clique para selecionar</span></span>
          <span className="upload-formats">JPG · PNG · DICOM (.dcm)</span>
          <input type="file" ref={fileRef} multiple className="hidden-input"
            accept="image/jpeg,image/png,image/jpg,image/bmp,.dcm"
            onChange={e => addFiles(e.target.files)} />
        </div>
      )}
    </div>
  );
}

export default function CaseWizard({ token, patient, specialty, onBack }) {
  const card = specialty?.key !== undefined ? specialty : null;

  const [complaint, setComplaint] = useState('');
  const [exams, setExams] = useState([newExam(card)]);
  const [docFiles, setDocFiles] = useState([]);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const docRef = useRef(null);
  const centralFileRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [suggestion, setSuggestion] = useState(null);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('detalhada');

  const updateExam = (i, val) => setExams(prev => prev.map((e, idx) => idx === i ? val : e));
  const removeExam = (i) => setExams(prev => prev.filter((_, idx) => idx !== i));

  // Each drag-drop onto the central zone = 1 exam
  const handleCentralDrop = (rawFiles) => {
    const files = Array.from(rawFiles);
    if (files.length === 0) return;
    const autoName = guessExamName(files);

    setExams(prev => {
      // If the first exam is still empty, fill it
      if (prev.length === 1 && prev[0].files.length === 0) {
        return [{ ...prev[0], files, name: prev[0].name || autoName }];
      }
      // Otherwise create a new exam block
      return [...prev, { name: autoName, modality: card?.suggestedModality || '', exam_date: '', files }];
    });
  };

  const hasFiles = exams.some(e => e.files.length > 0);
  const filledExams = exams.filter(e => e.files.length > 0).length;
  const canAnalyze = hasFiles || docFiles.length > 0;

  const handleSuggest = async () => {
    const config = SPECIALTY_SUGGESTIONS[card?.key];
    if (!config || !results) return;
    setSuggestionLoading(true);
    try {
      const res = await fetch(`${API}/api/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          specialty: card.key,
          analysis: results.analysis,
          suggestion_type: config.type,
        }),
      });
      if (!res.ok) throw new Error('Erro ao gerar sugestão');
      const data = await res.json();
      setSuggestion(data.suggestion);
      setActiveTab('sugestao');
    } catch (err) {
      setError(err.message);
    } finally {
      setSuggestionLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('patient_json', JSON.stringify({
        ...patient,
        chief_complaint: complaint,
        clinical_history: complaint,
        specialty: card?.key || null,
      }));

      const examsMeta = [];
      exams.forEach(exam => {
        if (exam.files.length > 0) {
          examsMeta.push({
            name: exam.name.trim() || card?.suggestedExams?.[0] || `Exame ${examsMeta.length + 1}`,
            modality: exam.modality,
            exam_date: exam.exam_date,
            file_count: exam.files.length,
          });
          exam.files.forEach(f => formData.append('files', f));
        }
      });
      formData.append('exams_json', JSON.stringify(examsMeta));
      docFiles.forEach(f => formData.append('doc_files', f));

      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/api/cases/analyze`, { method: 'POST', body: formData, headers });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Erro na análise'); }
      setResults(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!results) return;
    setPdfLoading(true);
    try {
      const res = await fetch(`${API}/api/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis: results.analysis, research: results.research,
          metadata: { patient_name: patient.name },
        }),
      });
      if (!res.ok) throw new Error('Erro ao gerar PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url;
      a.download = `segunda-opiniao-${patient.name || 'meu-exame'}.pdf`;
      a.click(); URL.revokeObjectURL(url);
    } catch (err) {
      setError('Erro ao gerar PDF: ' + err.message);
    } finally {
      setPdfLoading(false);
    }
  };

  // ── Results ──────────────────────────────────────────────────────────────────
  if (results) {
    return (
      <div className="wizard-results">
        <div className="wizard-results-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Stethoscope size={24} style={{ color: '#06b6d4' }} />
            <h2>Segunda Opinião — {patient.name}</h2>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {card?.key && SPECIALTY_SUGGESTIONS[card.key] && (
              <button className="btn-suggestion" onClick={handleSuggest} disabled={suggestionLoading}>
                {suggestionLoading ? 'Gerando...' : SPECIALTY_SUGGESTIONS[card.key].label}
              </button>
            )}
            <button className="btn-ghost" onClick={() => { setResults(null); setSuggestion(null); setActiveTab('detalhada'); onBack?.(); }}>
              Nova consulta
            </button>
            <button className="btn-secondary" onClick={handleDownloadPDF} disabled={pdfLoading}>
              <Download size={16} /> {pdfLoading ? 'Gerando...' : 'Baixar PDF'}
            </button>
          </div>
        </div>
        {card && (
          <div className="case-badge-row">
            <span className="badge" style={{ background: card.bg, color: card.color, border: `1px solid ${card.border}` }}>
              {card.emoji} {card.label}
            </span>
            {results.exams_processed > 0 && (
              <span className="badge-gray">{results.exams_processed} exame{results.exams_processed > 1 ? 's' : ''} analisado{results.exams_processed > 1 ? 's' : ''}</span>
            )}
          </div>
        )}
        {(() => {
          const tabs = parseMarkdownTabs(results.analysis, results.research);
          const content = tabs[activeTab] || '';
          return (
            <>
              <div className="results-tabs">
                {RESULT_TABS.map(t => (
                  <button key={t.key}
                    className={`results-tab-btn${activeTab === t.key ? ' active' : ''}`}
                    onClick={() => setActiveTab(t.key)}>
                    {t.label}
                    {t.note && <span className="tab-note">{t.note}</span>}
                  </button>
                ))}
              </div>
              <div className="results-tab-content">
                {!content ? (
                  <p className="tab-empty">Seção não disponível para este tipo de análise.</p>
                ) : (
                  <div className="markdown-body">
                    <ReactMarkdown>{content}</ReactMarkdown>
                    {activeTab === 'sugestao' && suggestionLoading && (
                      <div className="loading-state" style={{ minHeight: 120, marginTop: '1.5rem' }}>
                        <div className="spinner" />
                        <div className="loading-text">Gerando sugestão personalizada...</div>
                      </div>
                    )}
                    {activeTab === 'sugestao' && suggestion && (
                      <>
                        <hr className="markdown-divider" />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '1rem' }}>
                          <span style={{ fontSize: '0.75rem', color: '#22c55e', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Detalhamento adicional gerado pela IA</span>
                        </div>
                        <ReactMarkdown>{suggestion}</ReactMarkdown>
                      </>
                    )}
                  </div>
                )}
              </div>
            </>
          );
        })()}
      </div>
    );
  }

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="wizard-card">
        <div className="loading-state" style={{ minHeight: 320 }}>
          <div className="spinner" />
          <div className="loading-text">
            {card ? `Agente de ${card.label} analisando seus exames...` : 'Analisando seus exames...'}
          </div>
          <div className="loading-subtext">
            Processando {filledExams} exame{filledExams > 1 ? 's' : ''} · Correlacionando achados · Preparando segunda opinião
          </div>
        </div>
      </div>
    );
  }

  // ── Form ─────────────────────────────────────────────────────────────────────
  return (
    <div className="wizard-card">
      <div className="wizard-header">
        <button className="icon-btn" onClick={onBack}><ArrowLeft size={18} /></button>
        <div style={{ flex: 1 }}>
          <h2 className="wizard-title">Segunda Opinião com IA</h2>
          <div className="wizard-subtitle">
            {card ? `${card.emoji} ${card.label}` : '🔍 Análise Geral'} · {patient.name}
          </div>
        </div>
      </div>

      <div className="wizard-body">
        <div className="wizard-step" style={{ gap: '1.5rem' }}>

          {/* Queixa */}
          <div className="form-group">
            <label>O que aconteceu?</label>
            <div className="form-hint">
              Conte o motivo da consulta, o que o médico disse, seus sintomas ou sua dúvida
            </div>
            <textarea className="form-textarea" rows={4}
              placeholder={card?.complaintHint || 'Ex: Fui ao médico com dor no joelho, ele pediu uma RM e uma radiografia. Quero entender os resultados.'}
              value={complaint}
              onChange={e => setComplaint(e.target.value)} />
          </div>

          {/* Zona central de drop */}
          <div>
            <div className="form-group" style={{ marginBottom: 8 }}>
              <label>Seus exames e imagens</label>
              <div className="form-hint">
                Arraste cada exame separadamente — cada drop cria um exame automaticamente
              </div>
            </div>

            <div
              className={`central-drop-zone${isDraggingOver ? ' dragging' : ''}`}
              onDragOver={e => { e.preventDefault(); setIsDraggingOver(true); }}
              onDragLeave={() => setIsDraggingOver(false)}
              onDrop={e => { e.preventDefault(); setIsDraggingOver(false); handleCentralDrop(e.dataTransfer.files); }}
              onClick={() => centralFileRef.current?.click()}
            >
              <UploadCloud size={32} style={{ color: isDraggingOver ? '#3b82f6' : '#475569', marginBottom: 6 }} />
              {!hasFiles ? (
                <>
                  <span className="upload-text">Arraste as imagens do <strong>1º exame</strong> aqui</span>
                  <span className="upload-formats">JPG · PNG · DICOM (.dcm) · vários arquivos aceitos</span>
                </>
              ) : (
                <>
                  <span className="upload-text">
                    Arraste o <strong>{filledExams + 1}º exame</strong> aqui para adicionar automaticamente
                  </span>
                  <span className="upload-formats">{filledExams} exame{filledExams > 1 ? 's' : ''} adicionado{filledExams > 1 ? 's' : ''} · solte mais para criar novos</span>
                </>
              )}
              <input type="file" ref={centralFileRef} multiple className="hidden-input"
                accept="image/jpeg,image/png,image/jpg,image/bmp,.dcm"
                onChange={e => { handleCentralDrop(e.target.files); e.target.value = ''; }} />
            </div>

            {/* Blocos de exame */}
            {hasFiles && (
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {exams.map((exam, i) => (
                  <ExamBlock key={i} exam={exam} index={i} total={exams.length}
                    onChange={val => updateExam(i, val)}
                    onRemove={() => removeExam(i)} />
                ))}
                <button type="button" className="btn-add-exam"
                  onClick={() => setExams(prev => [...prev, newExam(card)])}>
                  <Plus size={16} /> Adicionar exame manualmente
                </button>
              </div>
            )}
          </div>

          {/* Documentos */}
          <div className="doc-upload-section" style={{ marginTop: 0 }}>
            <div className="doc-upload-label">
              <FileText size={15} />
              <span>Receitas e documentos</span>
              <span className="form-hint" style={{ margin: 0 }}>
                Laudo do médico, pedido de exame, resultado de sangue (PDF · DOC)
              </span>
            </div>
            <div className="doc-upload-area"
              onDragOver={e => e.preventDefault()}
              onDrop={e => { e.preventDefault(); setDocFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]); }}
              onClick={() => docRef.current?.click()}>
              <UploadCloud size={22} style={{ color: '#8b5cf6' }} />
              <span>Arraste documentos ou <span>clique para selecionar</span></span>
              <input type="file" ref={docRef} multiple className="hidden-input"
                accept=".pdf,.doc,.docx"
                onChange={e => setDocFiles(prev => [...prev, ...Array.from(e.target.files)])} />
            </div>
            {docFiles.length > 0 && (
              <div className="exam-files-list">
                {docFiles.map((f, i) => (
                  <div key={i} className="exam-file-chip doc-chip">
                    <FileText size={12} /><span>{f.name}</span>
                    <button type="button" onClick={() => setDocFiles(prev => prev.filter((_, j) => j !== i))}>
                      <X size={11} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {error && <div className="error-box" style={{ margin: '0 1.5rem 1rem' }}>⚠️ {error}</div>}

      <div className="wizard-footer">
        <div style={{ flex: 1 }} />
        <button className="btn-primary" style={{ width: 'auto', padding: '0.75rem 2.5rem' }}
          onClick={handleAnalyze} disabled={!canAnalyze || loading}>
          Analisar com IA <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}
