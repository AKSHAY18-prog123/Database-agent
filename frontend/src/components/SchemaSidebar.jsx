import React, { useState } from 'react';
import { MessageSquare, Table, PlusCircle, Database, ChevronRight, ChevronDown, Key, Hash, Layers } from 'lucide-react';

export function SchemaSidebar({ activeTab, setActiveTab, dbInfo, onSelectDatabase, onSelectTableQuery }) {
  const [expandedTables, setExpandedTables] = useState({});
  const [currentLevel, setCurrentLevel] = useState('tables'); // 'databases' | 'tables'

  const toggleTable = (tableName) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  const tables = dbInfo?.tables || [];
  const allDatabases = dbInfo?.allDatabases || [];
  const activeDatabase = dbInfo?.database || 'school_management';

  const handleSelectDB = (dbName) => {
    onSelectDatabase(dbName);
    setCurrentLevel('tables');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-nav">
        <button 
          className={`nav-button ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={18} />
          <span>AI Chat Assistant</span>
        </button>

        <button 
          className={`nav-button ${activeTab === 'visual' ? 'active' : ''}`}
          onClick={() => setActiveTab('visual')}
        >
          <PlusCircle size={18} />
          <span>Visual Table Builder</span>
        </button>
      </div>

      {/* Drill-down Header & Breadcrumbs */}
      <div className="schema-tree-header" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {currentLevel === 'tables' && (
              <button
                onClick={() => setCurrentLevel('databases')}
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid var(--border-color)',
                  color: '#93c5fd',
                  borderRadius: '4px',
                  padding: '2px 6px',
                  fontSize: '0.7rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
                title="Back to Databases"
              >
                ← Databases
              </button>
            )}
            <span>{currentLevel === 'databases' ? 'All Databases' : `DB: ${activeDatabase}`}</span>
          </div>
          <Layers size={14} />
        </div>
      </div>

      <div className="tree-list">
        {/* LEVEL 1: DATABASES LIST */}
        {currentLevel === 'databases' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {allDatabases.map(db => (
              <div
                key={db}
                onClick={() => handleSelectDB(db)}
                className="table-header-row"
                style={{
                  background: db === activeDatabase ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  border: db === activeDatabase ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Database size={14} style={{ color: db === activeDatabase ? '#60a5fa' : 'var(--text-muted)' }} />
                  <span style={{ fontWeight: db === activeDatabase ? 700 : 500 }}>{db}</span>
                </div>
                <span className="table-badge">{db === activeDatabase ? 'Active' : 'Select →'}</span>
              </div>
            ))}
          </div>
        )}

        {/* LEVEL 2: TABLES & COLUMNS DRILL DOWN */}
        {currentLevel === 'tables' && (
          tables.length === 0 ? (
            <div style={{ padding: '16px', fontSize: '0.8rem', color: 'var(--text-dim)', textAlign: 'center' }}>
              No tables in database `{activeDatabase}`
            </div>
          ) : (
            tables.map((table) => {
              const isExpanded = expandedTables[table.name];
              return (
                <div key={table.name} className="tree-item">
                  <div 
                    className="table-header-row"
                    onClick={() => toggleTable(table.name)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <Table size={14} style={{ color: '#60a5fa' }} />
                      <span style={{ fontWeight: 600 }}>{table.name}</span>
                    </div>
                    <span className="table-badge">{table.rowCount} rows</span>
                  </div>

                  {isExpanded && (
                    <div className="column-list">
                      {table.columns.map((col) => (
                        <div key={col.name} className="column-item">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {col.key === 'PRI' ? (
                              <Key size={11} style={{ color: '#f59e0b' }} title="Primary Key" />
                            ) : (
                              <Hash size={11} style={{ color: 'var(--text-dim)' }} />
                            )}
                            <span>{col.name}</span>
                          </div>
                          <span className="column-type">{col.type}</span>
                        </div>
                      ))}
                      <button
                        onClick={() => onSelectTableQuery(`SELECT * FROM \`${table.name}\` LIMIT 50;`)}
                        style={{
                          margin: '6px 0 2px',
                          padding: '4px 8px',
                          fontSize: '0.72rem',
                          borderRadius: '4px',
                          background: 'rgba(59, 130, 246, 0.1)',
                          border: '1px solid rgba(59, 130, 246, 0.25)',
                          color: '#93c5fd',
                          cursor: 'pointer',
                          textAlign: 'center',
                          width: '100%'
                        }}
                      >
                        Inspect Data in Chat →
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )
        )}
      </div>
    </aside>
  );
}
