import React, { useState } from 'react';
import { X } from 'lucide-react';

const API = 'http://localhost:8000';

export default function AuthModal({ mode, onClose, onSuccess }) {
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const isLogin = mode === 'login';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin ? { email: form.email, password: form.password } : form;
      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro ao autenticar.');
      onSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isLogin ? 'Entrar na conta' : 'Criar conta'}</h2>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <input className="auth-input" placeholder="Nome completo"
              value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
          )}
          <input className="auth-input" type="email" placeholder="Email"
            value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
          <input className="auth-input" type="password" placeholder="Senha (mínimo 6 caracteres)"
            value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
            required minLength={6} />
          {error && <div className="auth-error">⚠️ {error}</div>}
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? 'Aguarde...' : isLogin ? 'Entrar' : 'Criar conta'}
          </button>
        </form>
      </div>
    </div>
  );
}
