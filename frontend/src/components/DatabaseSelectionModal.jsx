import React, { useState } from 'react';
import { Database, Plus, Check, ArrowRight, FolderPlus } from 'lucide-react';
import axios from 'axios';

export function DatabaseSelectionModal({ isOpen, onClose, allDatabases, onSelectDatabase, API_BASE }) {
  const [newDbName, setNewDbName] = useState('');
  const [selectedDb, setSelectedDb] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleSelectExisting = (e) => {
    e.preventDefault();
    const dbToSelect = selectedDb || allDatabases[0];
    if (dbToSelect) {
      onSelectDatabase(dbToSelect);
      onClose();
    }
  };

  const handleCreateNew = async (e) => {
    e.preventDefault();
    const name = newDbName.trim().replaceAll(' ', '_');
    if (!name) return;

    setIsCreating(true);
    setErrorMsg(null);

    try {
      // Execute CREATE DATABASE SQL
      const res = await axios.post(`${API_BASE}/api/chat`, {
        query: `create database ${name}`
      });

      if (res.data && res.data.sql) {
        onSelectDatabase(name);
        onClose();
      } else if (res.data.response) {
        onSelectDatabase(name);
        onClose();
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || err.message);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: '520px', border: '1px solid rgba(59, 130, 246, 0.4)' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 0 25px rgba(6, 182, 212, 0.4)',
            marginBottom: '12px'
          }}>
            <Database size={28} />
          </div>
          <h2 style={{ fontSize: '1.4rem', color: 'white', fontWeight: 800 }}>Choose Your Database Context</h2>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Select an existing database on your MySQL server or create a new database.
          </p>
        </div>

        {errorMsg && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            marginBottom: '16px',
            fontSize: '0.84rem',
            background: 'rgba(244, 63, 94, 0.15)',
            color: '#fca5a5',
            border: '1px solid rgba(244, 63, 94, 0.3)'
          }}>
            ❌ {errorMsg}
          </div>
        )}

        {/* Option A: Select Existing Database */}
        <form onSubmit={handleSelectExisting} style={{ marginBottom: '20px', background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: '#93c5fd', fontWeight: 700, marginBottom: '8px' }}>
            📁 Select Existing Database
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              value={selectedDb || (allDatabases[0] || '')}
              onChange={(e) => setSelectedDb(e.target.value)}
              style={{
                flex: 1,
                padding: '10px 12px',
                borderRadius: '8px',
                background: '#0b1120',
                border: '1px solid var(--border-color)',
                color: 'white',
                fontSize: '0.88rem',
                outline: 'none'
              }}
            >
              {allDatabases.map(db => (
                <option key={db} value={db}>{db}</option>
              ))}
            </select>
            <button type="submit" className="btn-primary" style={{ padding: '10px 16px', fontSize: '0.85rem' }}>
              <span>Connect</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        {/* Option B: Create New Database */}
        <form onSubmit={handleCreateNew} style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: '#34d399', fontWeight: 700, marginBottom: '8px' }}>
            ✨ Create a New Database
          </label>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              placeholder="e.g. company_db, ecommerce, hospital..."
              value={newDbName}
              onChange={(e) => setNewDbName(e.target.value)}
              style={{
                flex: 1,
                padding: '10px 12px',
                borderRadius: '8px',
                background: '#0b1120',
                border: '1px solid var(--border-color)',
                color: 'white',
                fontSize: '0.88rem',
                outline: 'none'
              }}
              required
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={isCreating || !newDbName.trim()}
              style={{ background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', padding: '10px 16px', fontSize: '0.85rem' }}
            >
              <Plus size={16} />
              <span>{isCreating ? 'Creating...' : 'Create DB'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
