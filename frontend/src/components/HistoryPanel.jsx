import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const API = 'http://localhost:8000';

export default function HistoryPanel({ token, onSelect, onClose }) {
  const [history, setHistory] = useState([]);
  const [cases, setCases] = useState([]);
  const [tab, setTab] = useState('cases'); // 'cases' | 'quick'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      fetch(`${API}/api/cases`, { headers }).then(r => r.json()).catch(() => []),
      fetch(`${API}/api/history`, { headers }).then(r => r.json()).catch(() => []),
    ]).then(([c, h]) => {
      setCases(Array.isArray(c) ? c : []);
      setHistory(Array.isArray(h) ? h : []);
      setLoading(false);
    });
  }, [token]);

  const fmtDate = iso => new Date(iso).toLocaleDateString('pt-BR');

  return (
    <div className="history-overlay" onClick={onClose}>
      <div className="history-panel" onClick={e => e.stopPropagation()}>
        <div className="history-header">
          <h3>Histórico</h3>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="history-tabs">
          <button className={`history-tab ${tab === 'cases' ? 'active' : ''}`} onClick={() => setTab('cases')}>
            Casos Clínicos {cases.length > 0 && <span className="tab-count">{cases.length}</span>}
          </button>
          <button className={`history-tab ${tab === 'quick' ? 'active' : ''}`} onClick={() => setTab('quick')}>
            Análises Rápidas {history.length > 0 && <span className="tab-count">{history.length}</span>}
          </button>
        </div>

        {loading ? (
          <div className="history-empty">Carregando...</div>
        ) : tab === 'cases' ? (
          cases.length === 0 ? (
            <div className="history-empty">Nenhum Caso Clínico salvo ainda.</div>
          ) : (
            <div className="history-list">
              {cases.map(c => (
                <div key={c.id} className="history-item" onClick={() => {
                  onSelect({ analysis: c.analysis, research: c.research, metadata: {} });
                  onClose();
                }}>
                  <div className="history-item-title">{c.title}</div>
                  <div className="history-item-meta">
                    {c.patient_name && <span className="badge">{c.patient_name}</span>}
                    {c.exams?.length > 0 && (
                      <span className="badge-gray">{c.exams.length} exame{c.exams.length > 1 ? 's' : ''}</span>
                    )}
                    <span>{fmtDate(c.created_at)}</span>
                  </div>
                  {c.chief_complaint && (
                    <div className="history-item-complaint">{c.chief_complaint}</div>
                  )}
                </div>
              ))}
            </div>
          )
        ) : (
          history.length === 0 ? (
            <div className="history-empty">Nenhuma análise rápida salva ainda.</div>
          ) : (
            <div className="history-list">
              {history.map(e => (
                <div key={e.id} className="history-item" onClick={() => {
                  onSelect({ analysis: e.analysis, research: e.research, metadata: { modality: e.modality } });
                  onClose();
                }}>
                  <div className="history-item-title">{e.filename || 'Exame sem nome'}</div>
                  <div className="history-item-meta">
                    {e.modality && <span className="badge">{e.modality}</span>}
                    <span>{fmtDate(e.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
