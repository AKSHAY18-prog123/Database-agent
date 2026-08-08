import React, { useState } from 'react';
import { Database, ShieldCheck, RefreshCw, Settings, Palette } from 'lucide-react';

export function Header({ dbInfo, onSelectDatabase, onReSeed, onOpenSettings, isSeeding }) {
  const [currentTheme, setCurrentTheme] = useState('blue');
  const tableCount = dbInfo?.tables?.length || 0;
  const totalRows = dbInfo?.tables?.reduce((acc, t) => acc + (t.rowCount || 0), 0) || 0;
  const allDatabases = dbInfo?.allDatabases || [];
  const activeDatabase = dbInfo?.database || '';

  const changeTheme = (themeName) => {
    setCurrentTheme(themeName);
    if (themeName === 'blue') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', themeName);
    }
  };

  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-icon">
          <Database size={22} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="brand-title">Database AI Agent</span>
            <span className="brand-badge" style={{
              background: dbInfo?.db_type === 'postgres' ? 'rgba(139, 92, 246, 0.15)' : 'rgba(59, 130, 246, 0.15)',
              color: dbInfo?.db_type === 'postgres' ? '#c084fc' : '#93c5fd',
              borderColor: dbInfo?.db_type === 'postgres' ? 'rgba(139, 92, 246, 0.3)' : 'rgba(59, 130, 246, 0.3)'
            }}>
              {dbInfo?.db_type === 'postgres' ? '🐘 PostgreSQL' : '🐬 MySQL'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '3px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Connected DB:</span>
            <select
              value={activeDatabase}
              onChange={(e) => onSelectDatabase(e.target.value)}
              className="db-selector-pill"
              style={{
                background: '#0b1120',
                border: '1px solid var(--border-glow)',
                color: '#93c5fd',
                borderRadius: '16px',
                padding: '2px 10px',
                fontSize: '0.76rem',
                fontWeight: 700,
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {allDatabases.map(db => (
                <option key={db} value={db}>{db}</option>
              ))}
            </select>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 500 }}>
              ({tableCount} tables, {totalRows} records)
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Dynamic Theme Accent Picker */}
        <div className="theme-picker" title="Change Theme Accent Color">
          <Palette size={14} style={{ color: 'var(--text-muted)', marginLeft: '2px' }} />
          <div
            className={`theme-dot ${currentTheme === 'blue' ? 'active' : ''}`}
            style={{ background: '#3b82f6' }}
            onClick={() => changeTheme('blue')}
            title="Cyber Blue"
          />
          <div
            className={`theme-dot ${currentTheme === 'emerald' ? 'active' : ''}`}
            style={{ background: '#10b981' }}
            onClick={() => changeTheme('emerald')}
            title="Emerald Mint"
          />
          <div
            className={`theme-dot ${currentTheme === 'purple' ? 'active' : ''}`}
            style={{ background: '#8b5cf6' }}
            onClick={() => changeTheme('purple')}
            title="Royal Purple"
          />
          <div
            className={`theme-dot ${currentTheme === 'rose' ? 'active' : ''}`}
            style={{ background: '#f43f5e' }}
            onClick={() => changeTheme('rose')}
            title="Sunset Rose"
          />
        </div>

        {/* Guardrails Status Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#34d399',
          fontSize: '0.8rem',
          fontWeight: 600
        }}>
          <ShieldCheck size={16} />
          <span>Active Session</span>
        </div>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="btn-secondary"
          style={{ padding: '8px 14px', fontSize: '0.82rem', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Settings size={16} />
          <span>Settings</span>
        </button>
      </div>
    </header>
  );
}
