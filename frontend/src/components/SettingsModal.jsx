import React, { useState } from 'react';
import { X, Key, Database, Check, AlertCircle, Save } from 'lucide-react';
import axios from 'axios';

export function SettingsModal({ isOpen, onClose, API_BASE, onSettingsSaved }) {
  const [host, setHost] = useState('127.0.0.1');
  const [port, setPort] = useState(3306);
  const [user, setUser] = useState('root');
  const [password, setPassword] = useState('24bca7190');
  const [database, setDatabase] = useState('school_management');
  const [openaiKey, setOpenaiKey] = useState('');

  const [status, setStatus] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setStatus(null);

    try {
      const res = await axios.post(`${API_BASE}/api/settings`, {
        host,
        port: parseInt(port, 10),
        user,
        password,
        openai_api_key: openaiKey || null
      });

      if (res.data.status === 'updated') {
        setStatus({ type: 'success', text: `Saved! ${res.data.connection_test.message}` });
        onSettingsSaved();
      }
    } catch (err) {
      setStatus({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={20} style={{ color: '#60a5fa' }} />
            <h3 style={{ fontSize: '1.1rem', color: 'white', fontWeight: 700 }}>Connection & AI Settings</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {status && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            marginBottom: '16px',
            fontSize: '0.84rem',
            background: status.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: status.type === 'success' ? '#34d399' : '#fca5a5',
            border: `1px solid ${status.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
          }}>
            {status.text}
          </div>
        )}

        <form onSubmit={handleSave}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Host</label>
              <input type="text" value={host} onChange={e => setHost(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Port</label>
              <input type="number" value={port} onChange={e => setPort(e.target.value)} style={inputStyle} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Username</label>
              <input type="text" value={user} onChange={e => setUser(e.target.value)} style={inputStyle} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} style={inputStyle} />
            </div>
          </div>

          <div style={{ marginBottom: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#93c5fd', fontWeight: 600, marginBottom: '4px' }}>
              OpenAI API Key (Optional)
            </label>
            <input
              type="password"
              placeholder="sk-..."
              value={openaiKey}
              onChange={e => setOpenaiKey(e.target.value)}
              style={inputStyle}
            />
            <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px' }}>
              Used for LangChain/LangGraph agent NL to SQL generation. Fallback rules active if omitted.
            </p>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
            <button type="button" onClick={onClose} className="btn-secondary">Close</button>
            <button type="submit" className="btn-primary" disabled={isSaving}>
              <Save size={14} /> Save & Test Connection
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: '8px 12px',
  borderRadius: '6px',
  background: 'rgba(255, 255, 255, 0.05)',
  border: '1px solid var(--border-color)',
  color: 'white',
  fontSize: '0.85rem'
};
