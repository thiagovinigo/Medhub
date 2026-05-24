import React, { useState, useEffect } from 'react';
import { X, Plus, ArrowLeft, Edit2, Check } from 'lucide-react';

const API = 'http://localhost:8000';
const today = () => new Date().toISOString().split('T')[0];
const calcAge = (bd) => bd ? Math.floor((new Date() - new Date(bd)) / (365.25 * 24 * 3600 * 1000)) : null;
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('pt-BR') : '';
const SEX_LABELS = { M: 'Masculino', F: 'Feminino', O: 'Outro' };
const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function PatientPanel({ token, onClose }) {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('list');       // 'list' | 'create' | 'detail'
  const [selected, setSelected] = useState(null); // full patient object
  const [cases, setCases] = useState([]);

  // edit profile
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);

  // metrics
  const [metricOpen, setMetricOpen] = useState(false);
  const [metricForm, setMetricForm] = useState({ date: today(), weight_kg: '', height_cm: '', notes: '' });

  // conditions
  const [condInput, setCondInput] = useState('');

  // create
  const [createForm, setCreateForm] = useState(emptyCreate());
  const [createError, setCreateError] = useState('');

  function emptyCreate() {
    return { name: '', birth_date: '', sex: '', height_cm: '', blood_type: '' };
  }

  const h = { Authorization: `Bearer ${token}` };
  const hJson = { ...h, 'Content-Type': 'application/json' };

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const data = await fetch(`${API}/api/patients`, { headers: h }).then(r => r.json());
      setPatients(Array.isArray(data) ? data : []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPatients(); }, []);

  const openPatient = async (p) => {
    const [full, pCases] = await Promise.all([
      fetch(`${API}/api/patients/${p.id}`, { headers: h }).then(r => r.json()),
      fetch(`${API}/api/patients/${p.id}/cases`, { headers: h }).then(r => r.json()).catch(() => []),
    ]);
    setSelected(full);
    setCases(Array.isArray(pCases) ? pCases : []);
    setEditForm({
      name: full.name,
      birth_date: full.birth_date || '',
      sex: full.sex || '',
      blood_type: full.blood_type || '',
      height_cm: full.height_cm || '',
    });
    setEditMode(false);
    setMetricOpen(false);
    setCondInput('');
    setView('detail');
  };

  const refreshSelected = async () => {
    const full = await fetch(`${API}/api/patients/${selected.id}`, { headers: h }).then(r => r.json());
    setSelected(full);
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/patients/${selected.id}`, {
        method: 'PUT', headers: hJson,
        body: JSON.stringify({ ...editForm, height_cm: editForm.height_cm ? parseFloat(editForm.height_cm) : null }),
      });
      await refreshSelected();
      setEditMode(false);
    } finally {
      setSaving(false);
    }
  };

  const addMetric = async () => {
    if (!metricForm.weight_kg && !metricForm.height_cm) return;
    await fetch(`${API}/api/patients/${selected.id}/metrics`, {
      method: 'POST', headers: hJson,
      body: JSON.stringify({
        ...metricForm,
        weight_kg: metricForm.weight_kg ? parseFloat(metricForm.weight_kg) : null,
        height_cm: metricForm.height_cm ? parseFloat(metricForm.height_cm) : null,
      }),
    });
    await refreshSelected();
    setMetricForm({ date: today(), weight_kg: '', height_cm: '', notes: '' });
    setMetricOpen(false);
  };

  const addCondition = async () => {
    if (!condInput.trim()) return;
    await fetch(`${API}/api/patients/${selected.id}/conditions`, {
      method: 'POST', headers: hJson,
      body: JSON.stringify({ condition: condInput.trim() }),
    });
    setCondInput('');
    await refreshSelected();
  };

  const removeCondition = async (cid) => {
    await fetch(`${API}/api/patients/${selected.id}/conditions/${cid}`, { method: 'DELETE', headers: h });
    setSelected(prev => ({ ...prev, conditions: prev.conditions.filter(c => c.id !== cid) }));
  };

  const createPatient = async (e) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;
    setCreateError('');
    try {
      const res = await fetch(`${API}/api/patients`, {
        method: 'POST', headers: hJson,
        body: JSON.stringify({ ...createForm, height_cm: createForm.height_cm ? parseFloat(createForm.height_cm) : null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      await fetchPatients();
      await openPatient(data);
    } catch (err) {
      setCreateError(err.message);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="history-overlay" onClick={onClose}>
      <div className="history-panel patient-panel" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="history-header">
          {view !== 'list' ? (
            <button className="icon-btn" onClick={() => { setView('list'); setSelected(null); }}>
              <ArrowLeft size={18} />
            </button>
          ) : <span style={{ width: 32 }} />}
          <h3>
            {view === 'list' && 'Pacientes'}
            {view === 'create' && 'Novo Paciente'}
            {view === 'detail' && (selected?.name || 'Paciente')}
          </h3>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="patient-panel-body">

          {/* ── List ── */}
          {view === 'list' && (
            <>
              <div className="patient-panel-toolbar">
                <button className="btn-outline" onClick={() => { setCreateForm(emptyCreate()); setCreateError(''); setView('create'); }}>
                  <Plus size={14} /> Novo Paciente
                </button>
              </div>
              {loading ? (
                <div className="history-empty">Carregando...</div>
              ) : patients.length === 0 ? (
                <div className="history-empty">Nenhum paciente cadastrado ainda.</div>
              ) : (
                <div className="history-list">
                  {patients.map(p => {
                    const age = calcAge(p.birth_date);
                    const conds = (p.conditions || []).map(c => typeof c === 'string' ? c : c.condition);
                    return (
                      <div key={p.id} className="history-item" onClick={() => openPatient(p)}>
                        <div className="history-item-title">{p.name}</div>
                        <div className="history-item-meta">
                          {age && <span className="badge">{age} anos</span>}
                          {p.sex && <span className="badge-gray">{SEX_LABELS[p.sex] || p.sex}</span>}
                          {p.blood_type && <span className="badge">{p.blood_type}</span>}
                          {p.weight_kg && <span className="badge-gray">{p.weight_kg} kg</span>}
                        </div>
                        {conds.length > 0 && (
                          <div className="history-item-complaint">
                            {conds.slice(0, 3).join(' · ')}{conds.length > 3 ? ` +${conds.length - 3}` : ''}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}

          {/* ── Create ── */}
          {view === 'create' && (
            <div className="patient-panel-form">
              <form onSubmit={createPatient} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div className="form-group">
                  <label>Nome completo *</label>
                  <input className="form-input" placeholder="Ex: Thiago Vinicius Gonçalves"
                    value={createForm.name} onChange={e => setCreateForm({ ...createForm, name: e.target.value })} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Data de nascimento</label>
                    <input type="date" className="form-input" value={createForm.birth_date}
                      onChange={e => setCreateForm({ ...createForm, birth_date: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Sexo</label>
                    <select className="form-input" value={createForm.sex}
                      onChange={e => setCreateForm({ ...createForm, sex: e.target.value })}>
                      <option value="">Selecionar...</option>
                      <option value="M">Masculino</option>
                      <option value="F">Feminino</option>
                      <option value="O">Outro</option>
                    </select>
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Tipo sanguíneo</label>
                    <select className="form-input" value={createForm.blood_type}
                      onChange={e => setCreateForm({ ...createForm, blood_type: e.target.value })}>
                      <option value="">Selecionar...</option>
                      {BLOOD_TYPES.map(b => <option key={b} value={b}>{b}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Altura (cm)</label>
                    <input type="number" className="form-input" placeholder="169"
                      value={createForm.height_cm}
                      onChange={e => setCreateForm({ ...createForm, height_cm: e.target.value })} />
                  </div>
                </div>
                {createError && <div className="auth-error">⚠️ {createError}</div>}
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button type="submit" className="btn-primary"
                    style={{ width: 'auto', padding: '0.65rem 1.75rem' }}
                    disabled={!createForm.name.trim()}>
                    Salvar Paciente
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* ── Detail ── */}
          {view === 'detail' && selected && (() => {
            const age = calcAge(selected.birth_date);
            const latestW = selected.weight_kg;
            const imc = latestW && selected.height_cm
              ? (latestW / ((selected.height_cm / 100) ** 2)).toFixed(1) : null;
            const conds = (selected.conditions || []);

            return (
              <div className="patient-detail">

                {/* Perfil */}
                <div className="patient-section">
                  <div className="patient-section-header">
                    <span className="patient-section-title">Perfil</span>
                    {!editMode
                      ? <button className="btn-ghost btn-sm" onClick={() => setEditMode(true)}><Edit2 size={13} /> Editar</button>
                      : <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn-ghost btn-sm" onClick={() => setEditMode(false)}>Cancelar</button>
                          <button className="btn-primary btn-sm" onClick={saveEdit} disabled={saving}>
                            <Check size={13} /> {saving ? '...' : 'Salvar'}
                          </button>
                        </div>
                    }
                  </div>

                  {!editMode ? (
                    <div className="patient-info-grid">
                      {age !== null && <div className="patient-info-item"><span>Idade</span><strong>{age} anos</strong></div>}
                      {selected.birth_date && <div className="patient-info-item"><span>Nascimento</span><strong>{fmtDate(selected.birth_date)}</strong></div>}
                      {selected.sex && <div className="patient-info-item"><span>Sexo</span><strong>{SEX_LABELS[selected.sex] || selected.sex}</strong></div>}
                      {selected.blood_type && <div className="patient-info-item"><span>Sangue</span><strong>{selected.blood_type}</strong></div>}
                      {selected.height_cm && <div className="patient-info-item"><span>Altura</span><strong>{selected.height_cm} cm</strong></div>}
                      {latestW && <div className="patient-info-item"><span>Peso</span><strong>{latestW} kg</strong></div>}
                      {imc && <div className="patient-info-item"><span>IMC</span><strong>{imc}</strong></div>}
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 10 }}>
                      <div className="form-group">
                        <label>Nome</label>
                        <input className="form-input" value={editForm.name}
                          onChange={e => setEditForm({ ...editForm, name: e.target.value })} />
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Nascimento</label>
                          <input type="date" className="form-input" value={editForm.birth_date}
                            onChange={e => setEditForm({ ...editForm, birth_date: e.target.value })} />
                        </div>
                        <div className="form-group">
                          <label>Sexo</label>
                          <select className="form-input" value={editForm.sex}
                            onChange={e => setEditForm({ ...editForm, sex: e.target.value })}>
                            <option value="">Selecionar...</option>
                            <option value="M">Masculino</option>
                            <option value="F">Feminino</option>
                            <option value="O">Outro</option>
                          </select>
                        </div>
                      </div>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Tipo sanguíneo</label>
                          <select className="form-input" value={editForm.blood_type}
                            onChange={e => setEditForm({ ...editForm, blood_type: e.target.value })}>
                            <option value="">Selecionar...</option>
                            {BLOOD_TYPES.map(b => <option key={b} value={b}>{b}</option>)}
                          </select>
                        </div>
                        <div className="form-group">
                          <label>Altura (cm)</label>
                          <input type="number" className="form-input" value={editForm.height_cm}
                            onChange={e => setEditForm({ ...editForm, height_cm: e.target.value })} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Condições */}
                <div className="patient-section">
                  <div className="patient-section-header">
                    <span className="patient-section-title">Condições Pré-existentes</span>
                  </div>
                  <div className="conditions-chips">
                    {conds.length === 0 && (
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Nenhuma condição registrada.</span>
                    )}
                    {conds.map(c => (
                      <span key={c.id} className="tag-chip">
                        {c.condition}
                        <button type="button" onClick={() => removeCondition(c.id)}><X size={11} /></button>
                      </span>
                    ))}
                  </div>
                  <div className="condition-add-row">
                    <input className="form-input" placeholder="Adicionar condição..."
                      value={condInput} onChange={e => setCondInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addCondition())} />
                    <button className="btn-outline btn-sm" onClick={addCondition} disabled={!condInput.trim()}>
                      <Plus size={14} />
                    </button>
                  </div>
                </div>

                {/* Medições */}
                <div className="patient-section">
                  <div className="patient-section-header">
                    <span className="patient-section-title">Histórico de Medições</span>
                    <button className="btn-ghost btn-sm" onClick={() => setMetricOpen(v => !v)}>
                      <Plus size={13} /> {metricOpen ? 'Cancelar' : 'Adicionar'}
                    </button>
                  </div>
                  {metricOpen && (
                    <div className="metric-form">
                      <div className="form-row">
                        <div className="form-group">
                          <label>Data</label>
                          <input type="date" className="form-input" value={metricForm.date}
                            onChange={e => setMetricForm({ ...metricForm, date: e.target.value })} />
                        </div>
                        <div className="form-group">
                          <label>Peso (kg)</label>
                          <input type="number" step="0.1" className="form-input" placeholder="79.5"
                            value={metricForm.weight_kg}
                            onChange={e => setMetricForm({ ...metricForm, weight_kg: e.target.value })} />
                        </div>
                        <div className="form-group">
                          <label>Altura (cm)</label>
                          <input type="number" className="form-input" placeholder="169"
                            value={metricForm.height_cm}
                            onChange={e => setMetricForm({ ...metricForm, height_cm: e.target.value })} />
                        </div>
                      </div>
                      <div className="form-group">
                        <label>Observação</label>
                        <input className="form-input" placeholder="Ex: pós-consulta cardiologista"
                          value={metricForm.notes}
                          onChange={e => setMetricForm({ ...metricForm, notes: e.target.value })} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button className="btn-primary btn-sm" onClick={addMetric}
                          disabled={!metricForm.weight_kg && !metricForm.height_cm}>
                          <Check size={13} /> Salvar
                        </button>
                      </div>
                    </div>
                  )}
                  {(selected.metrics || []).length === 0 ? (
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: '8px 0 0' }}>Nenhuma medição registrada.</p>
                  ) : (
                    <div className="metrics-list">
                      {selected.metrics.map(m => {
                        const mImc = m.weight_kg && m.height_cm
                          ? (m.weight_kg / ((m.height_cm / 100) ** 2)).toFixed(1) : null;
                        return (
                          <div key={m.id} className="metric-row">
                            <span className="metric-date">{fmtDate(m.date)}</span>
                            {m.weight_kg && <span className="badge-gray">{m.weight_kg} kg</span>}
                            {m.height_cm && <span className="badge-gray">{m.height_cm} cm</span>}
                            {mImc && <span className="badge-gray">IMC {mImc}</span>}
                            {m.notes && <span className="metric-notes">{m.notes}</span>}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Casos */}
                {cases.length > 0 && (
                  <div className="patient-section">
                    <div className="patient-section-header">
                      <span className="patient-section-title">Casos Clínicos ({cases.length})</span>
                    </div>
                    <div className="history-list" style={{ padding: 0 }}>
                      {cases.map(c => (
                        <div key={c.id} className="history-item">
                          <div className="history-item-title">{c.title}</div>
                          <div className="history-item-meta">
                            <span>{fmtDate(c.created_at)}</span>
                            {c.exams?.length > 0 && (
                              <span className="badge-gray">{c.exams.length} exame{c.exams.length > 1 ? 's' : ''}</span>
                            )}
                          </div>
                          {c.chief_complaint && <div className="history-item-complaint">{c.chief_complaint}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

        </div>
      </div>
    </div>
  );
}
