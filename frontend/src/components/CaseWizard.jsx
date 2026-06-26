import React, { useState, useRef } from 'react';
import {
  ArrowRight, ArrowLeft, X, UploadCloud, FileSearch,
  Stethoscope, Download, FileText, Image,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const RESULT_TABS = [
  { key: 'detalhada',    label: 'Análise Detalhada' },
  { key: 'correlacao',  label: 'Correlação' },
  { key: 'profissional', label: 'Diagnóstico Profissional', note: 'para médicos' },
  { key: 'leigo',       label: 'Diagnóstico Leigo' },
  { key: 'sugestao',    label: 'Sugestão Médica' },
  { key: 'referencias', label: 'Referências' },
];

const SPECIALTY_SUGGESTIONS = {
  spine:     { label: 'Sugerir exercícios', type: 'exercise' },
  msk:       { label: 'Sugerir fisioterapia / exercícios', type: 'exercise' },
  endocrino: { label: 'Sugerir dieta', type: 'diet' },
  nutri:     { label: 'Sugerir plano alimentar', type: 'diet' },
  cardio:    { label: 'Sugerir hábitos saudáveis', type: 'lifestyle' },
};

function normTitle(s) {
  return (s || '').toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z\s]/g, '').trim();
}

function parseMarkdownTabs(analysis, research) {
  const chunks = [];
  let cur = null;
  const lines = ((analysis || '') + '\n\n' + (research || '')).split('\n');
  for (let line of lines) {
    const cleanLine = line.trim();
    // Identifica ## Header, ### Header, ou **Header** (se for sozinho na linha)
    let headerMatch = cleanLine.match(/^#{2,4}\s+(.*)$/);
    if (!headerMatch) {
      headerMatch = cleanLine.match(/^\*\*(.*?)\*\*$/);
    }
    
    if (headerMatch) {
      if (cur) chunks.push(cur);
      cur = { title: normTitle(headerMatch[1]), lines: [] };
    } else if (cur) {
      cur.lines.push(line);
    }
  }
  if (cur) chunks.push(cur);

  const find = (...keys) => {
    const c = chunks.filter(c => keys.some(k => c.title.includes(k)));
    return c.length ? c.map(x => x.lines.join('\n').trim()).join('\n\n---\n\n') : '';
  };

  const correlacaoBase = find('correlacao clinica', 'correlacao', 'achados criticos');
  const consolidado = find('diagnostico consolidado', 'recomendacoes');
  
  return {
    detalhada:    find('analise detalhada', 'analise tecnica', 'analise integrada', 'informacoes extraidas', 'analise', 'achados'),
    correlacao:   [correlacaoBase, consolidado].filter(Boolean).join('\n\n---\n\n'),
    profissional: find('diagnostico profissional', 'impressao diagnostica', 'diagnostico'),
    leigo:        find('linguagem simples', 'linguagem leiga', 'simples', 'leigo'),
    sugestao:     find('sugestao medica', 'sugestao'),
    referencias:  find('referencias bibliograficas', 'referencias'),
  };
}

const isDoc = (f) => /\.(pdf|doc|docx)$/i.test(f.name);

export default function CaseWizard({ token, patient, specialty, onBack }) {
  const card = specialty?.key !== undefined ? specialty : null;

  const [complaint, setComplaint] = useState('');
  const [allFiles, setAllFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [suggestion, setSuggestion] = useState(null);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('detalhada');

  const fileRef = useRef(null);

  const addFiles = (incoming) => {
    const arr = Array.from(incoming);
    setAllFiles(prev => {
      const existingNames = new Set(prev.map(f => f.name));
      return [...prev, ...arr.filter(f => !existingNames.has(f.name))];
    });
  };

  const removeFile = (i) => setAllFiles(prev => prev.filter((_, j) => j !== i));

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const imgFiles = allFiles.filter(f => !isDoc(f));
  const docFiles = allFiles.filter(f => isDoc(f));
  const canAnalyze = allFiles.length > 0;

  // ── Suggestion ───────────────────────────────────────────────────────────────
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

  // ── Analyze ──────────────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!canAnalyze) return;
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
      allFiles.forEach(f => formData.append('files', f));

      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res = await fetch(`${API}/api/cases/analyze`, { method: 'POST', body: formData, headers });
      if (!res.ok) {
        let msg = `Erro ${res.status}`;
        try {
          const d = await res.json();
          if (typeof d.detail === 'string') msg = d.detail;
          else if (Array.isArray(d.detail)) msg = d.detail.map(e => e.msg || JSON.stringify(e)).join(' | ');
          else if (d.detail) msg = JSON.stringify(d.detail);
          else if (d.message) msg = d.message;
          console.error('[analyze] backend error:', d);
        } catch { /* response not JSON */ }
        throw new Error(msg);
      }
      setResults(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── PDF download ─────────────────────────────────────────────────────────────
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
    const tabs = parseMarkdownTabs(results.analysis, results.research);
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
            <button className="btn-ghost" onClick={() => {
              setResults(null); setSuggestion(null);
              setActiveTab('detalhada'); setAllFiles([]);
              onBack?.();
            }}>
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
              <span className="badge-gray">
                {results.exams_processed} exame{results.exams_processed > 1 ? 's' : ''} analisado{results.exams_processed > 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}

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
          {!tabs[activeTab] ? (
            <p className="tab-empty">Seção não disponível para este tipo de análise.</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown>{tabs[activeTab]}</ReactMarkdown>
              {activeTab === 'sugestao' && suggestionLoading && (
                <div className="loading-state" style={{ minHeight: 120, marginTop: '1.5rem' }}>
                  <div className="spinner" />
                  <div className="loading-text">Gerando sugestão personalizada...</div>
                </div>
              )}
              {activeTab === 'sugestao' && suggestion && (
                <>
                  <hr className="markdown-divider" />
                  <div style={{ fontSize: '0.75rem', color: '#22c55e', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                    Detalhamento adicional gerado pela IA
                  </div>
                  <ReactMarkdown>{suggestion}</ReactMarkdown>
                </>
              )}
            </div>
          )}
        </div>
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
            Classificando {allFiles.length} arquivo{allFiles.length > 1 ? 's' : ''} · Correlacionando achados · Preparando segunda opinião
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
              Conte o motivo da consulta, seus sintomas ou dúvida sobre os resultados
            </div>
            <textarea className="form-textarea" rows={3}
              placeholder={card?.complaintHint || 'Ex: Fui ao médico com dor no joelho, ele pediu uma RM e um raio-X. Quero entender os resultados.'}
              value={complaint}
              onChange={e => setComplaint(e.target.value)} />
          </div>

          {/* Drop zone — aceita tudo de uma vez */}
          <div className="form-group">
            <label>Seus exames e documentos</label>
            <div className="form-hint">
              Adicione todos os arquivos de uma vez — imagens e PDFs juntos
            </div>

            <div
              className={`central-drop-zone${isDragging ? ' dragging' : ''}`}
              onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
            >
              <UploadCloud size={32} style={{ color: isDragging ? '#3b82f6' : '#475569', marginBottom: 6 }} />
              <span className="upload-text">
                {allFiles.length === 0
                  ? <>Arraste <strong>todos os arquivos</strong> aqui de uma vez</>
                  : <>{allFiles.length} arquivo{allFiles.length > 1 ? 's' : ''} adicionado{allFiles.length > 1 ? 's' : ''} — arraste mais ou clique</>
                }
              </span>
              <span className="upload-formats">
                Imagens (JPG, PNG, DICOM) · Documentos (PDF, DOC) · Exames de sangue
              </span>
              <input
                type="file" ref={fileRef} multiple className="hidden-input"
                accept="image/jpeg,image/png,image/jpg,image/bmp,.dcm,.pdf,.doc,.docx"
                onChange={e => { addFiles(e.target.files); e.target.value = ''; }}
              />
            </div>

            {/* Lista de arquivos */}
            {allFiles.length > 0 && (
              <div style={{ marginTop: 10 }}>
                {imgFiles.length > 0 && (
                  <div style={{ marginBottom: 6 }}>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                      Imagens ({imgFiles.length})
                    </div>
                    <div className="exam-files-list">
                      {allFiles.map((f, i) => !isDoc(f) && (
                        <div key={i} className="exam-file-chip">
                          <Image size={12} /><span>{f.name}</span>
                          <button type="button" onClick={() => removeFile(i)}><X size={11} /></button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {docFiles.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4 }}>
                      Documentos e exames laboratoriais ({docFiles.length})
                    </div>
                    <div className="exam-files-list">
                      {allFiles.map((f, i) => isDoc(f) && (
                        <div key={i} className="exam-file-chip doc-chip">
                          <FileText size={12} /><span>{f.name}</span>
                          <button type="button" onClick={() => removeFile(i)}><X size={11} /></button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>
      </div>

      {error && <div className="error-box" style={{ margin: '0 1.5rem 1rem' }}>⚠️ {error}</div>}

      <div className="wizard-footer">
        <div style={{ flex: 1, fontSize: '0.8rem', color: '#64748b' }}>
          {allFiles.length > 0
            ? `${allFiles.length} arquivo${allFiles.length > 1 ? 's' : ''} · a IA vai classificar e analisar tudo automaticamente`
            : 'Adicione ao menos um arquivo para analisar'}
        </div>
        <button
          className="btn-primary" style={{ width: 'auto', padding: '0.75rem 2.5rem' }}
          onClick={handleAnalyze} disabled={!canAnalyze || loading}
        >
          Analisar com IA <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}
