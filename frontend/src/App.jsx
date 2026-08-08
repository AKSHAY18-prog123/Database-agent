import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Header } from './components/Header';
import { SchemaSidebar } from './components/SchemaSidebar';
import { ChatInterface } from './components/ChatInterface';
import { VisualBuilder } from './components/VisualBuilder';
import { LoginModal } from './components/LoginModal';
import { SettingsModal } from './components/SettingsModal';
import { DatabaseSelectionModal } from './components/DatabaseSelectionModal';

const API_BASE = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : '';

export function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'visual'
  const [dbInfo, setDbInfo] = useState({ database: '', tables: [], allDatabases: [] });
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDbSelectionOpen, setIsDbSelectionOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentInput, setCurrentInput] = useState('');

  // Initial welcome message
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: "👋 Welcome to your **SQL AI Agent**!\n\nI can answer questions about your database tables, list records, run statistics, create new tables, and add entities.\n\n*Strict Database Guardrails are enabled: I will only respond to questions related to your connected SQL database and tables.*",
      is_relevant: true,
      columns: [],
      rows: []
    }
  ]);

  const [isLoading, setIsLoading] = useState(false);

  // Fetch Database Tree Schema
  const fetchSchema = async (dbName = null) => {
    if (!isAuthenticated) return;
    try {
      const url = dbName ? `${API_BASE}/api/database/schema?db_name=${encodeURIComponent(dbName)}` : `${API_BASE}/api/database/schema`;
      const res = await axios.get(url);
      if (res.data) {
        setDbInfo(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch schema:', err);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchSchema();
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = async (creds) => {
    setIsAuthenticated(true);
    setIsDbSelectionOpen(true);
    await fetchSchema();
  };

  const handleSendMessage = async (userQuery, opts = {}) => {
    const userMsg = { sender: 'user', text: userQuery };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const payload = {
        query: userQuery,
        confirmed: opts.confirmed || false,
        pending_sql: opts.pending_sql || null,
        db_config: {
          database: dbInfo?.database || null
        }
      };

      const res = await axios.post(`${API_BASE}/api/chat`, payload);
      const data = res.data;

      const botMsg = {
        sender: 'assistant',
        text: data.response || (data.is_relevant ? 'Query processed.' : data.guardrail_message),
        is_relevant: data.is_relevant,
        guardrail_message: data.guardrail_message,
        sql: data.sql,
        operation_type: data.operation_type,
        requires_confirmation: data.requires_confirmation,
        pending_sql: data.pending_sql,
        columns: data.columns || [],
        rows: data.rows || [],
        affectedRows: data.affected_rows || 0,
        executionTimeMs: data.execution_time_ms || 0,
        error: data.error
      };

      setMessages(prev => [...prev, botMsg]);

      if (data.auth_required) {
        setIsSettingsOpen(true);
      }

      if (data.switched_database) {
        fetchSchema(data.switched_database);
      } else if (data.operation_type && data.operation_type !== 'READ' && data.operation_type !== 'CHAT' && !data.requires_confirmation) {
        fetchSchema(dbInfo.database);
      }
    } catch (err) {
      const errorMsg = {
        sender: 'assistant',
        text: `❌ Error connecting to SQL Agent server: ${err.message}`,
        is_relevant: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReSeed = async () => {
    setIsSeeding(true);
    try {
      const res = await axios.post(`${API_BASE}/api/database/seed`);
      if (res.data.status === 'success') {
        fetchSchema();
        setMessages(prev => [
          ...prev,
          {
            sender: 'assistant',
            text: "✅ **Database Re-seeded Successfully!**\n\nThe `school_management` database has been restored with 35+ realistic records across `departments`, `teachers`, `students`, `courses`, `enrollments`, and `grades`.",
            is_relevant: true
          }
        ]);
      }
    } catch (err) {
      alert("Failed to seed database: " + err.message);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleSelectDatabase = (dbName) => {
    fetchSchema(dbName);
  };

  const handleSelectTableQuery = (sqlQuery) => {
    setActiveTab('chat');
    handleSendMessage(sqlQuery);
  };

  return (
    <div className="app-container">
      <SchemaSidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        dbInfo={dbInfo}
        onSelectDatabase={handleSelectDatabase}
        onSelectTableQuery={handleSelectTableQuery}
      />

      <div className="main-content">
        <Header
          dbInfo={dbInfo}
          onSelectDatabase={handleSelectDatabase}
          onReSeed={handleReSeed}
          onOpenSettings={() => setIsSettingsOpen(true)}
          isSeeding={isSeeding}
        />

        {activeTab === 'chat' && (
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            currentInput={currentInput}
            setCurrentInput={setCurrentInput}
            dbInfo={dbInfo}
          />
        )}

        {activeTab === 'visual' && (
          <VisualBuilder
            dbInfo={dbInfo}
            onRefreshSchema={fetchSchema}
            API_BASE={API_BASE}
          />
        )}

        <LoginModal
          isOpen={!isAuthenticated}
          onLoginSuccess={handleLoginSuccess}
          API_BASE={API_BASE}
        />

        <DatabaseSelectionModal
          isOpen={isAuthenticated && isDbSelectionOpen}
          onClose={() => setIsDbSelectionOpen(false)}
          allDatabases={dbInfo?.allDatabases || []}
          onSelectDatabase={(db) => {
            fetchSchema(db);
            setIsDbSelectionOpen(false);
          }}
          API_BASE={API_BASE}
        />

        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          API_BASE={API_BASE}
          onSettingsSaved={fetchSchema}
        />
      </div>
    </div>
  );
}

export default App;
