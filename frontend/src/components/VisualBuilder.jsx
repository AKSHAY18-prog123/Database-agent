import React, { useState } from 'react';
import { Plus, Trash2, Database, Table, Check, AlertCircle, Play } from 'lucide-react';
import axios from 'axios';

export function VisualBuilder({ dbInfo, onRefreshSchema, API_BASE }) {
  const [activeSubTab, setActiveSubTab] = useState('create');
  
  // Create Table State
  const [newTableName, setNewTableName] = useState('');
  const [columns, setColumns] = useState([
    { name: 'id', type: 'INT', primary: true, nullable: false },
    { name: 'title', type: 'VARCHAR(100)', primary: false, nullable: false },
    { name: 'created_at', type: 'DATETIME', primary: false, nullable: true }
  ]);
  
  // Insert Row State
  const [selectedTable, setSelectedTable] = useState(dbInfo?.tables?.[0]?.name || '');
  const [rowValues, setRowValues] = useState({});

  // Raw SQL State
  const [rawSql, setRawSql] = useState('SELECT * FROM `students` LIMIT 10;');

  const [statusMessage, setStatusMessage] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAddColumn = () => {
    setColumns([...columns, { name: '', type: 'VARCHAR(100)', primary: false, nullable: true }]);
  };

  const handleRemoveColumn = (idx) => {
    setColumns(columns.filter((_, i) => i !== idx));
  };

  const handleColumnChange = (idx, field, value) => {
    const updated = [...columns];
    updated[idx][field] = value;
    setColumns(updated);
  };

  const handleCreateTable = async (e) => {
    e.preventDefault();
    if (!newTableName.trim()) {
      setStatusMessage({ type: 'error', text: 'Table name is required' });
      return;
    }

    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      const res = await axios.post(`${API_BASE}/api/database/create_table_visual`, {
        table_name: newTableName.trim(),
        columns: columns
      });

      if (res.data.success) {
        setStatusMessage({ type: 'success', text: `Table \`${newTableName}\` created successfully!` });
        setNewTableName('');
        onRefreshSchema();
      } else {
        setStatusMessage({ type: 'error', text: res.data.error || 'Failed to create table' });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInsertRow = async (e) => {
    e.preventDefault();
    if (!selectedTable) return;

    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      const res = await axios.post(`${API_BASE}/api/database/insert_data_visual`, {
        table_name: selectedTable,
        data: rowValues
      });

      if (res.data.success) {
        setStatusMessage({ type: 'success', text: `Row inserted successfully into \`${selectedTable}\`!` });
        setRowValues({});
        onRefreshSchema();
      } else {
        setStatusMessage({ type: 'error', text: res.data.error || 'Failed to insert row' });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunRawSql = async () => {
    if (!rawSql.trim()) return;
    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      const res = await axios.post(`${API_BASE}/api/database/raw_query`, { sql: rawSql });
      if (res.data.success) {
        setStatusMessage({ type: 'success', text: `Query executed successfully! (${res.data.affected_rows} rows)` });
        onRefreshSchema();
      } else {
        setStatusMessage({ type: 'error', text: res.data.error });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentTableObj = dbInfo?.tables?.find(t => t.name === selectedTable);

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto', height: '100%', overflowY: 'auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'white' }}>Visual Table & Data Builder</h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Create tables, add entities, or run custom SQL without writing manual DDL scripts.
        </p>
      </div>

      {/* Sub Tabs */}
      <div style={{ display: 'flex', gap: '12px', borderBottom: '1px solid var(--border-color)', marginBottom: '24px' }}>
        <button
          onClick={() => setActiveSubTab('create')}
          style={{
            padding: '10px 16px',
            fontSize: '0.88rem',
            fontWeight: 600,
            background: 'transparent',
            border: 'none',
            borderBottom: activeSubTab === 'create' ? '2px solid #3b82f6' : '2px solid transparent',
            color: activeSubTab === 'create' ? '#60a5fa' : 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          Create New Table
        </button>

        <button
          onClick={() => setActiveSubTab('insert')}
          style={{
            padding: '10px 16px',
            fontSize: '0.88rem',
            fontWeight: 600,
            background: 'transparent',
            border: 'none',
            borderBottom: activeSubTab === 'insert' ? '2px solid #3b82f6' : '2px solid transparent',
            color: activeSubTab === 'insert' ? '#60a5fa' : 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          Insert Entity/Row
        </button>

        <button
          onClick={() => setActiveSubTab('raw')}
          style={{
            padding: '10px 16px',
            fontSize: '0.88rem',
            fontWeight: 600,
            background: 'transparent',
            border: 'none',
            borderBottom: activeSubTab === 'raw' ? '2px solid #3b82f6' : '2px solid transparent',
            color: activeSubTab === 'raw' ? '#60a5fa' : 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          Raw SQL Scratchpad
        </button>
      </div>

      {statusMessage && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.88rem',
          background: statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
          border: `1px solid ${statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
          color: statusMessage.type === 'success' ? '#34d399' : '#fca5a5'
        }}>
          {statusMessage.type === 'success' ? <Check size={18} /> : <AlertCircle size={18} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* TAB 1: CREATE TABLE */}
      {activeSubTab === 'create' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <form onSubmit={handleCreateTable}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Table Name
              </label>
              <input
                type="text"
                placeholder="e.g. library_books, exam_schedules"
                value={newTableName}
                onChange={(e) => setNewTableName(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid var(--border-color)',
                  color: 'white',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h4 style={{ fontSize: '0.9rem', color: 'white' }}>Define Columns</h4>
              <button
                type="button"
                onClick={handleAddColumn}
                className="btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                <Plus size={14} /> Add Column
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
              {columns.map((col, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                  <input
                    type="text"
                    placeholder="Column Name"
                    value={col.name}
                    onChange={(e) => handleColumnChange(idx, 'name', e.target.value)}
                    style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.85rem' }}
                  />

                  <select
                    value={col.type}
                    onChange={(e) => handleColumnChange(idx, 'type', e.target.value)}
                    style={{ padding: '8px 12px', borderRadius: '6px', background: '#0b1120', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.85rem' }}
                  >
                    <option value="INT">INT</option>
                    <option value="VARCHAR(100)">VARCHAR(100)</option>
                    <option value="TEXT">TEXT</option>
                    <option value="DECIMAL(10,2)">DECIMAL(10,2)</option>
                    <option value="DATE">DATE</option>
                    <option value="DATETIME">DATETIME</option>
                    <option value="BOOLEAN">BOOLEAN</option>
                  </select>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={col.primary}
                      onChange={(e) => handleColumnChange(idx, 'primary', e.target.checked)}
                    />
                    Primary Key
                  </label>

                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={col.nullable}
                      onChange={(e) => handleColumnChange(idx, 'nullable', e.target.checked)}
                    />
                    Nullable
                  </label>

                  <button
                    type="button"
                    onClick={() => handleRemoveColumn(idx)}
                    style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>

            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating Table...' : 'Create Table in MySQL'}
            </button>
          </form>
        </div>
      )}

      {/* TAB 2: INSERT ROW */}
      {activeSubTab === 'insert' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <form onSubmit={handleInsertRow}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Select Table
              </label>
              <select
                value={selectedTable}
                onChange={(e) => {
                  setSelectedTable(e.target.value);
                  setRowValues({});
                }}
                style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', background: '#0b1120', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.9rem' }}
              >
                <option value="">-- Choose a table --</option>
                {dbInfo?.tables?.map(t => (
                  <option key={t.name} value={t.name}>{t.name} ({t.rowCount} rows)</option>
                ))}
              </select>
            </div>

            {currentTableObj && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '24px' }}>
                {currentTableObj.columns.map(col => {
                  if (col.key === 'PRI' && col.type.includes('int')) {
                    return null; // Skip auto-increment primary keys
                  }
                  return (
                    <div key={col.name}>
                      <label style={{ display: 'block', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                        {col.name} <span style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>({col.type})</span>
                      </label>
                      <input
                        type="text"
                        placeholder={`Enter ${col.name}...`}
                        value={rowValues[col.name] || ''}
                        onChange={(e) => setRowValues({ ...rowValues, [col.name]: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          borderRadius: '6px',
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid var(--border-color)',
                          color: 'white',
                          fontSize: '0.88rem'
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            )}

            <button type="submit" className="btn-primary" disabled={isSubmitting || !selectedTable}>
              {isSubmitting ? 'Inserting Entity...' : 'Insert Entity into Table'}
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: RAW SQL SCRATCHPAD */}
      {activeSubTab === 'raw' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              MySQL SQL Query
            </label>
            <textarea
              rows={5}
              value={rawSql}
              onChange={(e) => setRawSql(e.target.value)}
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#060911',
                border: '1px solid rgba(59,130,246,0.3)',
                color: '#a5f3fc',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <button onClick={handleRunRawSql} className="btn-primary" disabled={isSubmitting}>
            <Play size={16} /> Execute SQL
          </button>
        </div>
      )}
    </div>
  );
}
