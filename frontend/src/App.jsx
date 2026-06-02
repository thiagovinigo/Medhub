import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud, Activity, FileSearch, X, Stethoscope,
  ArrowRight, LogIn, LogOut, History, Download, User, Folder, Users,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import AuthModal from './components/AuthModal';
import HistoryPanel from './components/HistoryPanel';
import PatientPanel from './components/PatientPanel';
import PatientSelector from './components/PatientSelector';
import SpecialtyDashboard, { SPECIALTY_CARDS } from './components/SpecialtyDashboard';
import CaseWizard from './components/CaseWizard';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

export default function App() {
  // Auth
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('medhub_token'));
  const [authModal, setAuthModal] = useState(null); // 'login' | 'register'
  const [showHistory, setShowHistory] = useState(false);
  const [showPatients, setShowPatients] = useState(false);

  // App mode
  const [mode, setMode] = useState('home'); // 'home' | 'quick' | 'case'
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedSpecialty, setSelectedSpecialty] = useState(null); // card object | undefined (not yet chosen)
  const [pendingSpecialty, setPendingSpecialty] = useState(undefined); // set when user clicks specialty from home

  const goHome = () => {
    setMode('home'); setSelectedPatient(null);
    setSelectedSpecialty(undefined); setPendingSpecialty(undefined);
  };

  const handleSpecialtyFromHome = (card) => {
    setPendingSpecialty(card !== null ? card : { key: null, label: 'Análise Geral', emoji: '🔍' });
    setMode('case');
  };

  const handlePatientSelect = (p) => {
    setSelectedPatient(p);
    if (pendingSpecialty !== undefined) {
      setSelectedSpecialty(pendingSpecialty);
      setPendingSpecialty(undefined);
    } else {
      setSelectedSpecialty(undefined);
    }
  };

  // Quick analysis
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then(setUser)
      .catch(logout);
  }, []);

  const logout = () => {
    setUser(null); setToken(null);
    localStorage.removeItem('medhub_token');
  };
  const handleAuthSuccess = ({ token: t, user: u }) => {
    setToken(t); setUser(u);
    localStorage.setItem('medhub_token', t);
    setAuthModal(null);
  };

  // Quick analysis handlers
  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) { setFile(f); setPreview(URL.createObjectURL(f)); setResults(null); setError(null); }
  };
  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); setPreview(URL.createObjectURL(f)); setResults(null); setError(null); }
  };
  const handleClear = () => {
    setFile(null); setPreview(null); setResults(null); setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };
  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResults(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        body: formData,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ocorreu um erro na análise');
      }

      const data = await response.json();
      setResults(data);
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
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis: results.analysis, research: results.research, metadata: results.metadata }),
      });
      if (!res.ok) throw new Error('Erro ao gerar PDF');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'laudo-medhub.pdf';
      a.click(); URL.revokeObjectURL(url);
    } catch (err) {
      setError('Erro ao gerar PDF: ' + err.message);
    } finally {
      setPdfLoading(false);
    }
  };

  const isDicom = file?.name?.toLowerCase().endsWith('.dcm');

  const Header = () => (
    <header>
      <div className="header-top">
        <div className="logo-container" style={{ cursor: 'pointer' }} onClick={goHome}>
          <Activity className="logo-icon" size={32} />
          <h1>MedAI Diagnostics</h1>
        </div>
        <div className="header-actions">
          {user ? (
            <>
              <button className="btn-ghost" onClick={() => setShowPatients(true)}>
                <Users size={15} /> Pacientes
              </button>
              <button className="btn-ghost" onClick={() => setShowHistory(true)}>
                <History size={15} /> Histórico
              </button>
              <div className="user-chip"><User size={13} /> {user.name.split(' ')[0]}</div>
              <button className="btn-ghost" onClick={logout}><LogOut size={14} /> Sair</button>
            </>
          ) : (
            <>
              <button className="btn-ghost" onClick={() => setAuthModal('login')}>
                <LogIn size={15} /> Entrar
              </button>
              <button className="btn-outline" onClick={() => setAuthModal('register')}>Criar conta</button>
            </>
          )}
        </div>
      </div>
    </header>
  );

  return (
    <div className="app-container">
      <div className="bg-glow" />

      {authModal && <AuthModal mode={authModal} onClose={() => setAuthModal(null)} onSuccess={handleAuthSuccess} />}
      {showPatients && token && (
        <PatientPanel token={token} onClose={() => setShowPatients(false)} />
      )}
      {showHistory && token && (
        <HistoryPanel token={token}
          onSelect={r => { setResults(r); setMode('quick'); }}
          onClose={() => setShowHistory(false)} />
      )}

      <Header />

      {/* ── Home Mode — logged in: specialty grid ─────────────────────────── */}
      {mode === 'home' && user && (
        <main style={{ maxWidth: 760, margin: '0 auto', width: '100%', padding: '2rem' }}>
          <div className="specialty-dashboard">
            <div className="specialty-dash-body">
              <p className="specialty-dash-intro">
                Selecione a especialidade do exame ou consulta que deseja entender melhor.
                Nossa IA vai analisar seus exames e documentos e dar uma explicação clara.
              </p>

              {[1, 2, 3].map(tier => {
                const cards = SPECIALTY_CARDS.filter(c => c.tier === tier);
                if (!cards.length) return null;
                return (
                  <div key={tier} className="specialty-group">
                    {tier === 1 && <div className="specialty-group-label">Mais comuns</div>}
                    {tier === 2 && <div className="specialty-group-label">Outras especialidades</div>}
                    <div className="specialty-grid">
                      {cards.map(c => (
                        <div key={c.key} className="specialty-card"
                          style={{ '--card-color': c.color, '--card-bg': c.bg, '--card-border': c.border }}
                          onClick={() => handleSpecialtyFromHome(c)}>
                          <div className="specialty-card-emoji">{c.emoji}</div>
                          <div className="specialty-card-body">
                            <div className="specialty-card-label">{c.label}</div>
                            <div className="specialty-card-desc">{c.description}</div>
                          </div>
                          <ArrowRight size={16} className="specialty-card-arrow" />
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}

              <div className="specialty-group">
                <div className="specialty-grid">
                  <div className="specialty-card specialty-card-general"
                    onClick={() => handleSpecialtyFromHome(null)}>
                    <FileSearch size={22} style={{ color: '#64748b', flexShrink: 0 }} />
                    <div className="specialty-card-body">
                      <div className="specialty-card-label">Não sei / Análise Geral</div>
                      <div className="specialty-card-desc">A IA detecta automaticamente a especialidade pelo tipo de exame</div>
                    </div>
                    <ArrowRight size={16} className="specialty-card-arrow" />
                  </div>
                  <div className="specialty-card specialty-card-general"
                    onClick={() => setMode('quick')}>
                    <UploadCloud size={22} style={{ color: '#64748b', flexShrink: 0 }} />
                    <div className="specialty-card-body">
                      <div className="specialty-card-label">Análise Rápida</div>
                      <div className="specialty-card-desc">Upload de uma imagem para laudo imediato, sem perfil de paciente</div>
                    </div>
                    <ArrowRight size={16} className="specialty-card-arrow" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* ── Home Mode — guest: two-card UI ────────────────────────────────── */}
      {mode === 'home' && !user && (
        <main style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4rem 2rem', gap: '2rem' }}>
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', maxWidth: 560 }}>
            Análise de imagens médicas com inteligência artificial avançada.
            Escolha como deseja começar:
          </p>

          <div className="mode-cards">
            <div className="mode-card" onClick={() => setMode('quick')}>
              <UploadCloud size={40} className="mode-card-icon" />
              <h3>Análise Rápida</h3>
              <p>Faça o upload de uma imagem e receba o laudo de IA imediatamente. Ideal para testes e consultas pontuais.</p>
              <div className="mode-card-formats">JPG · PNG · DICOM</div>
              <button className="btn-primary" style={{ marginTop: 'auto' }}>
                Começar <ArrowRight size={16} />
              </button>
            </div>

            <div className="mode-card mode-card-featured" onClick={() => setMode('case')}>
              <Folder size={40} className="mode-card-icon" />
              <h3>Caso Clínico</h3>
              <p>Monte um caso completo com perfil do paciente, múltiplos exames e histórico clínico para um laudo consolidado e preciso.</p>
              <div className="mode-card-features">
                <span>✓ Múltiplas imagens por exame</span>
                <span>✓ Agentes especialistas</span>
                <span>✓ Contexto clínico completo</span>
              </div>
              <button className="btn-primary" style={{ marginTop: 'auto' }}>
                Criar Caso Clínico <ArrowRight size={16} />
              </button>
            </div>
          </div>

          <p className="hint-text">
            Faça <button className="link-btn" onClick={() => setAuthModal('login')}>login</button> ou{' '}
            <button className="link-btn" onClick={() => setAuthModal('register')}>crie uma conta</button>{' '}
            para salvar histórico e baixar laudos em PDF.
          </p>
        </main>
      )}

      {/* ── Case Mode — patient selection ─────────────────────────────────── */}
      {mode === 'case' && !selectedPatient && (
        <main style={{ maxWidth: 680, margin: '0 auto', width: '100%', padding: '2rem' }}>
          <PatientSelector token={token} onSelect={handlePatientSelect} onBack={goHome} />
        </main>
      )}

      {/* ── Case Mode — specialty dashboard ──────────────────────────────── */}
      {mode === 'case' && selectedPatient && selectedSpecialty === undefined && (
        <main style={{ maxWidth: 760, margin: '0 auto', width: '100%', padding: '2rem' }}>
          <SpecialtyDashboard
            patient={selectedPatient}
            onSelect={card => setSelectedSpecialty(card || { key: null, label: 'Análise Geral', emoji: '🔍' })}
            onBack={() => setSelectedPatient(null)}
          />
        </main>
      )}

      {/* ── Case Mode — wizard ────────────────────────────────────────────── */}
      {mode === 'case' && selectedPatient && selectedSpecialty !== undefined && (
        <main style={{ maxWidth: 760, margin: '0 auto', width: '100%', padding: '2rem' }}>
          <CaseWizard token={token} patient={selectedPatient} specialty={selectedSpecialty} onBack={() => setSelectedSpecialty(undefined)} />
        </main>
      )}

      {/* ── Quick Mode ────────────────────────────────────────────────────── */}
      {mode === 'quick' && (
        <main className={results ? 'has-results' : ''}>
          <section className="upload-card">
            <div className="upload-card-header">
              <button className="btn-ghost" onClick={() => { setMode('home'); handleClear(); }}>
                ← Voltar
              </button>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Análise Rápida</span>
            </div>

            {!preview ? (
              <div className="upload-area" onDragOver={e => e.preventDefault()}
                onDrop={handleDrop} onClick={() => fileInputRef.current?.click()}>
                <UploadCloud className="upload-icon" />
                <div className="upload-text">
                  Arraste e solte sua imagem médica aqui<br />
                  ou <span>clique para procurar</span>
                </div>
                <div className="upload-formats">JPG · PNG · BMP · DICOM (.dcm)</div>
                <input type="file" className="hidden-input" ref={fileInputRef}
                  onChange={handleFileChange}
                  accept="image/jpeg,image/png,image/jpg,image/bmp,.dcm" />
              </div>
            ) : (
              <div className="preview-container">
                {isDicom ? (
                  <div className="dicom-placeholder">
                    <FileSearch size={48} style={{ color: '#06b6d4' }} />
                    <div className="dicom-filename">{file.name}</div>
                  </div>
                ) : (
                  <img src={preview} alt="Medical scan preview" className="preview-image" />
                )}
                <button className="remove-image" onClick={handleClear} disabled={loading}><X size={18} /></button>
              </div>
            )}

            {error && <div className="error-box">⚠️ {error}</div>}

            <button className="btn-primary" onClick={handleAnalyze} disabled={!file || loading}>
              {loading ? 'Processando Imagem...' : 'Analisar Imagem Médica'}
              {!loading && <ArrowRight size={20} />}
            </button>

            {results && (
              <button className="btn-secondary" onClick={handleDownloadPDF} disabled={pdfLoading}>
                <Download size={17} /> {pdfLoading ? 'Gerando PDF...' : 'Baixar Laudo em PDF'}
              </button>
            )}
          </section>

          {(loading || results) && (
            <section className="results-card">
              <div className="results-header">
                <Stethoscope className="logo-icon" size={24} />
                <h2>Laudo de Inteligência Artificial</h2>
                {results?.metadata?.modality && <span className="badge">{results.metadata.modality}</span>}
              </div>
              <div className="results-content">
                {loading ? (
                  <div className="loading-state">
                    <div className="spinner" />
                    <div className="loading-text">Analisando achados clínicos e correlacionando literatura médica...</div>
                  </div>
                ) : results ? (
                  <div className="markdown-body">
                    <ReactMarkdown>{results.analysis}</ReactMarkdown>
                    <hr className="markdown-divider" />
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                      <FileSearch size={20} style={{ color: '#06b6d4' }} />
                      <h2 style={{ margin: 0, color: '#06b6d4' }}>Pesquisa Acadêmica Relacionada</h2>
                    </div>
                    <ReactMarkdown>{results.research}</ReactMarkdown>
                  </div>
                ) : null}
              </div>
            </section>
          )}
        </main>
      )}
    </div>
  );
}
