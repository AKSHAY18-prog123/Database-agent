import React, { useState } from 'react';
import { Database, Lock, Key, Check, AlertCircle, LogIn, Link, Settings } from 'lucide-react';
import axios from 'axios';

export function LoginModal({ isOpen, onLoginSuccess, API_BASE }) {
  const [connectMode, setConnectMode] = useState('uri'); // 'uri' | 'manual'
  const [dbType, setDbType] = useState('mysql'); // 'mysql' | 'postgres'
  
  // Connection String state
  const [connectionUri, setConnectionUri] = useState('');

  // Manual inputs state
  const [host, setHost] = useState('127.0.0.1');
  const [port, setPort] = useState(3306);
  const [user, setUser] = useState('root');
  const [password, setPassword] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');

  const [status, setStatus] = useState(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  if (!isOpen) return null;

  const handleEngineChange = (type) => {
    setDbType(type);
    if (type === 'postgres') {
      setPort(5432);
      setUser('postgres');
    } else {
      setPort(3306);
      setUser('root');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsAuthenticating(true);
    setStatus(null);

    try {
      const payload = connectMode === 'uri' ? {
        connection_uri: connectionUri,
        openai_api_key: openaiKey || null
      } : {
        db_type: dbType,
        host,
        port: parseInt(port, 10),
        user,
        password,
        openai_api_key: openaiKey || null
      };

      const res = await axios.post(`${API_BASE}/api/settings`, payload);

      if (res.data.connection_test && res.data.connection_test.status === 'success') {
        setStatus({ type: 'success', text: `✅ Authenticated! ${res.data.connection_test.message}` });
        setTimeout(() => {
          onLoginSuccess({ dbType, host, port, user, password, openaiKey, connectionUri });
        }, 500);
      } else {
        const errorMsg = res.data.connection_test?.message || 'Connection Refused: Check database service or password.';
        setStatus({ type: 'error', text: errorMsg });
      }
    } catch (err) {
      setStatus({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setIsAuthenticating(false);
    }
  };

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '8px',
    background: '#0b1120',
    border: '1px solid var(--border-color)',
    color: 'white',
    fontSize: '0.88rem',
    outline: 'none'
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: '520px', border: '1px solid rgba(59, 130, 246, 0.4)' }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 0 25px rgba(6, 182, 212, 0.4)',
            marginBottom: '10px'
          }}>
            <Database size={28} />
          </div>
          <h2 style={{ fontSize: '1.4rem', color: 'white', fontWeight: 800 }}>Universal Database Agent Login</h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Connect to your 🐬 <strong>MySQL</strong> or 🐘 <strong>PostgreSQL</strong> database.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', background: 'rgba(255,255,255,0.03)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <button
            type="button"
            onClick={() => setConnectMode('uri')}
            style={{
              flex: 1,
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.82rem',
              fontWeight: 700,
              cursor: 'pointer',
              background: connectMode === 'uri' ? 'var(--primary)' : 'transparent',
              color: connectMode === 'uri' ? 'white' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Link size={14} />
            <span>1-Click Connection String</span>
          </button>
          <button
            type="button"
            onClick={() => setConnectMode('manual')}
            style={{
              flex: 1,
              padding: '8px 12px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.82rem',
              fontWeight: 700,
              cursor: 'pointer',
              background: connectMode === 'manual' ? 'var(--primary)' : 'transparent',
              color: connectMode === 'manual' ? 'white' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            <Settings size={14} />
            <span>Manual Details</span>
          </button>
        </div>

        {status && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '18px',
            fontSize: '0.84rem',
            lineHeight: 1.5,
            background: status.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: status.type === 'success' ? '#34d399' : '#fca5a5',
            border: `1px solid ${status.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`
          }}>
            {status.text}
          </div>
        )}

        <form onSubmit={handleLogin}>
          {/* MODE 1: 1-Click Connection String */}
          {connectMode === 'uri' ? (
            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#93c5fd', fontWeight: 600, marginBottom: '6px' }}>
                Paste Database Connection String / URI
              </label>
              <input
                type="text"
                placeholder="postgres://user:pass@ep-db.neon.tech:5432/main  or  mysql://root:pass@localhost:3306/db"
                value={connectionUri}
                onChange={e => setConnectionUri(e.target.value)}
                style={{ ...inputStyle, borderColor: 'rgba(59, 130, 246, 0.5)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}
                required
              />
              <p style={{ fontSize: '0.74rem', color: 'var(--text-dim)', marginTop: '6px', lineHeight: 1.4 }}>
                💡 <strong>Non-Tech User Tip:</strong> Copy & paste 1 connection line from Neon.tech, Supabase, Aiven, Railway, or your host. The app auto-detects MySQL vs PostgreSQL!
              </p>
            </div>
          ) : (
            /* MODE 2: Manual Credentials Input */
            <>
              {/* Engine Switcher Pills */}
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Select Engine</label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={() => handleEngineChange('mysql')}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '8px',
                      border: dbType === 'mysql' ? '1px solid #3b82f6' : '1px solid var(--border-color)',
                      background: dbType === 'mysql' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                      color: dbType === 'mysql' ? '#93c5fd' : 'var(--text-muted)',
                      fontWeight: 700,
                      fontSize: '0.82rem',
                      cursor: 'pointer'
                    }}
                  >
                    🐬 MySQL
                  </button>
                  <button
                    type="button"
                    onClick={() => handleEngineChange('postgres')}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '8px',
                      border: dbType === 'postgres' ? '1px solid #8b5cf6' : '1px solid var(--border-color)',
                      background: dbType === 'postgres' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                      color: dbType === 'postgres' ? '#c084fc' : 'var(--text-muted)',
                      fontWeight: 700,
                      fontSize: '0.82rem',
                      cursor: 'pointer'
                    }}
                  >
                    🐘 PostgreSQL
                  </button>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Host</label>
                  <input type="text" value={host} onChange={e => setHost(e.target.value)} style={inputStyle} required />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Port</label>
                  <input type="number" value={port} onChange={e => setPort(e.target.value)} style={inputStyle} required />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Username</label>
                  <input type="text" value={user} onChange={e => setUser(e.target.value)} style={inputStyle} required />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', color: '#93c5fd', fontWeight: 600, marginBottom: '4px' }}>Password</label>
                  <input
                    type="password"
                    placeholder="Enter password..."
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    style={{ ...inputStyle, borderColor: 'rgba(59, 130, 246, 0.5)' }}
                  />
                </div>
              </div>
            </>
          )}

          <div style={{ marginBottom: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: '#60a5fa', fontWeight: 600, marginBottom: '4px' }}>
              OpenAI API Key (Optional)
            </label>
            <input
              type="password"
              placeholder="sk-..."
              value={openaiKey}
              onChange={e => setOpenaiKey(e.target.value)}
              style={inputStyle}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isAuthenticating}
            style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '0.95rem' }}
          >
            <LogIn size={18} />
            <span>{isAuthenticating ? 'Connecting Database...' : 'Connect Database'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
