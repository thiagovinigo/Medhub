import React, { useState, useRef } from 'react';
import { UploadCloud, Activity, FileSearch, X, Stethoscope, ArrowRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreview(objectUrl);
      setResults(null);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      setFile(droppedFile);
      setPreview(URL.createObjectURL(droppedFile));
      setResults(null);
      setError(null);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setResults(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
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

  return (
    <div className="app-container">
      <div className="bg-glow"></div>
      
      <header>
        <div className="logo-container">
          <Activity className="logo-icon" size={36} />
          <h1>MedAI Diagnostics</h1>
        </div>
        <p>Análise de imagens médicas com inteligência artificial avançada. Faça o upload de um raio-X, RM ou tomografia para iniciar.</p>
      </header>

      <main className={results ? 'has-results' : ''}>
        {/* Lado Esquerdo: Upload */}
        <section className="upload-card">
          {!preview ? (
            <div 
              className="upload-area"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="upload-icon" />
              <div className="upload-text">
                Arraste e solte sua imagem médica aqui<br />
                ou <span>clique para procurar</span>
              </div>
              <input 
                type="file" 
                className="hidden-input" 
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/jpeg, image/png, image/jpg, image/bmp"
              />
            </div>
          ) : (
            <div className="preview-container">
              <img src={preview} alt="Medical scan preview" className="preview-image" />
              <button className="remove-image" onClick={handleClear} disabled={loading}>
                <X size={18} />
              </button>
            </div>
          )}

          {error && (
            <div style={{ color: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              ⚠️ {error}
            </div>
          )}

          <button 
            className="btn-primary" 
            onClick={handleAnalyze} 
            disabled={!file || loading}
          >
            {loading ? 'Processando Imagem...' : 'Analisar Imagem Médica'}
            {!loading && <ArrowRight size={20} />}
          </button>
        </section>

        {/* Lado Direito: Resultados */}
        {(loading || results) && (
          <section className="results-card">
            <div className="results-header">
              <Stethoscope className="logo-icon" size={24} />
              <h2>Laudo de Inteligência Artificial</h2>
            </div>
            
            <div className="results-content">
              {loading ? (
                <div className="loading-state">
                  <div className="spinner"></div>
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
    </div>
  );
}

export default App;
