import React, { useState, useEffect } from 'react';
import { Plus, ArrowLeft, User, X, ChevronRight } from 'lucide-react';

const API = 'http://localhost:8000';
const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const SEX_LABELS = { M: 'Masculino', F: 'Feminino', O: 'Outro' };

function TagInput({ tags, onChange, placeholder }) {
  const [input, setInput] = useState('');
  const handleKey = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && input.trim()) {
      e.preventDefault();
      if (!tags.includes(input.trim())) onChange([...tags, input.trim()]);
      setInput('');
    }
  };
  return (
    <div className="tag-input-wrap">
      {tags.map((t, i) => (
        <span key={i} className="tag-chip">
          {t}
          <button type="button" onClick={() => onChange(tags.filter((_, j) => j !== i))}>
            <X size={11} />
          </button>
        </span>
      ))}
      <input className="tag-input" value={input} onChange={e => setInput(e.target.value)}
        onKeyDown={handleKey} placeholder={tags.length === 0 ? placeholder : 'Adicionar...'} />
    </div>
  );
}

const calcAge = (birth_date) => {
  if (!birth_date) return null;
  return Math.floor((new Date() - new Date(birth_date)) / (365.25 * 24 * 3600 * 1000));
};

const normalizePatient = (p) => ({
  ...p,
  conditions: (p.conditions || []).map(c => typeof c === 'string' ? c : c.condition).filter(Boolean),
});

export default function PatientSelector({ token, onSelect, onBack }) {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(!!token);
  const [view, setView] = useState(token ? 'loading' : 'form');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const emptyForm = { name: '', birth_date: '', sex: '', height_cm: '', weight_kg: '', blood_type: '', conditions: [] };
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/patients`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data.map(normalizePatient) : [];
        setPatients(list);
        setView(list.length === 0 ? 'form' : 'list');
      })
      .catch(() => setView('form'))
      .finally(() => setLoading(false));
  }, [token]);

  const handleSave = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    if (!token) { onSelect(form); return; }

    setSaving(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          ...form,
          height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
          weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro ao salvar paciente');
      onSelect(normalizePatient(data));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="patient-selector">
        <div className="loading-state" style={{ minHeight: 200 }}><div className="spinner" /></div>
      </div>
    );
  }

  return (
    <div className="patient-selector">
      <div className="patient-selector-header">
        <button className="icon-btn" onClick={onBack}><ArrowLeft size={18} /></button>
        <div>
          <h2 className="wizard-title">
            {view === 'list' ? 'Selecionar Paciente' : patients.length > 0 ? 'Novo Paciente' : 'Cadastrar Paciente'}
          </h2>
          <div className="wizard-subtitle">Caso Clínico</div>
        </div>
        {view === 'list' && (
          <button className="btn-outline" onClick={() => { setForm(emptyForm); setView('form'); }}>
            <Plus size={14} /> Novo
          </button>
        )}
      </div>

      {view === 'list' && (
        <div className="patient-list">
          {patients.map(p => (
            <div key={p.id} className="patient-card" onClick={() => onSelect(p)}>
              <div className="patient-card-avatar"><User size={18} /></div>
              <div className="patient-card-info">
                <div className="patient-card-name">{p.name}</div>
                <div className="patient-card-meta">
                  {calcAge(p.birth_date) && <span>{calcAge(p.birth_date)} anos</span>}
                  {p.sex && <span>{SEX_LABELS[p.sex] || p.sex}</span>}
                  {p.blood_type && <span className="badge">{p.blood_type}</span>}
                </div>
                {p.conditions.length > 0 && (
                  <div className="patient-card-conditions">
                    {p.conditions.slice(0, 3).map((c, i) => <span key={i} className="badge-gray">{c}</span>)}
                    {p.conditions.length > 3 && <span className="badge-gray">+{p.conditions.length - 3}</span>}
                  </div>
                )}
              </div>
              <ChevronRight size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
            </div>
          ))}
        </div>
      )}

      {view === 'form' && (
        <form className="patient-create-form" onSubmit={handleSave}>
          {patients.length > 0 && (
            <button type="button" className="btn-ghost" style={{ alignSelf: 'flex-start', marginBottom: 4 }}
              onClick={() => setView('list')}>
              <ArrowLeft size={14} /> Voltar à lista
            </button>
          )}
          {!token && (
            <div className="form-hint-box">
              Faça login para salvar o perfil do paciente e reutilizá-lo em todos os exames.
            </div>
          )}

          <div className="form-group">
            <label>Nome completo *</label>
            <input className="form-input" placeholder="Ex: Thiago Vinicius Gonçalves"
              value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Data de nascimento</label>
              <input type="date" className="form-input" value={form.birth_date}
                onChange={e => setForm({ ...form, birth_date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Sexo</label>
              <select className="form-input" value={form.sex}
                onChange={e => setForm({ ...form, sex: e.target.value })}>
                <option value="">Selecionar...</option>
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
              </select>
            </div>
            <div className="form-group">
              <label>Tipo sanguíneo</label>
              <select className="form-input" value={form.blood_type}
                onChange={e => setForm({ ...form, blood_type: e.target.value })}>
                <option value="">Selecionar...</option>
                {BLOOD_TYPES.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Peso (kg)</label>
              <input type="number" step="0.1" className="form-input" placeholder="79.5"
                value={form.weight_kg} onChange={e => setForm({ ...form, weight_kg: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Altura (cm)</label>
              <input type="number" className="form-input" placeholder="169"
                value={form.height_cm} onChange={e => setForm({ ...form, height_cm: e.target.value })} />
            </div>
            {form.weight_kg && form.height_cm && (
              <div className="form-group">
                <label>IMC</label>
                <div className="form-input readonly">
                  {(parseFloat(form.weight_kg) / ((parseFloat(form.height_cm) / 100) ** 2)).toFixed(1)}
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Condições pré-existentes</label>
            <div className="form-hint">Pressione Enter após cada condição</div>
            <TagInput tags={form.conditions}
              onChange={v => setForm({ ...form, conditions: v })}
              placeholder="Ex: Diabetes tipo 2, Hipertensão..." />
          </div>

          {error && <div className="auth-error">⚠️ {error}</div>}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
            <button type="submit" className="btn-primary"
              style={{ width: 'auto', padding: '0.75rem 2rem' }}
              disabled={!form.name.trim() || saving}>
              {saving ? 'Salvando...' : token ? 'Salvar e Continuar' : 'Continuar'}
              <ChevronRight size={18} />
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
