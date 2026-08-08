import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Copy, Check, ShieldAlert, Sparkles, Terminal, Code, Database, AlertCircle } from 'lucide-react';
import { DataGrid } from './DataGrid';

export function ChatInterface({ messages, onSendMessage, isLoading, currentInput, setCurrentInput, dbInfo }) {
  const [copiedIdx, setCopiedIdx] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleCopy = (code, idx) => {
    navigator.clipboard.writeText(code);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const handlePromptClick = (text) => {
    setCurrentInput(text);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!currentInput.trim() || isLoading) return;
    onSendMessage(currentInput);
    setCurrentInput('');
  };

  // Generate dynamic sample prompts based on active database
  const activeDb = dbInfo?.database || 'school_management';
  const tables = dbInfo?.tables || [];

  let samplePrompts = [];
  if (activeDb === 'school_management') {
    samplePrompts = [
      { label: "🎓 Show top 5 students by GPA", query: "Show top 5 students by GPA with their department names" },
      { label: "📚 List all courses & teachers", query: "List all courses along with their department and assigned teacher" },
      { label: "➕ Add a new table for library_books", query: "Create a new table for library_books with book_id, title, author, and available_copies" },
      { label: "👤 Insert a new student record", query: "Insert a new student named Rahul Sharma in Computer Science department with GPA 3.9" },
      { label: "🛑 Guardrail Test", query: "What is the capital of France and write a python script?", isOfftopic: true }
    ];
  } else if (activeDb === 'world') {
    samplePrompts = [
      { label: "🌍 Show top 5 cities by population", query: "Show top 5 cities by population in world" },
      { label: "🌐 List all countries", query: "List all countries in world" },
      { label: "🗣️ Count languages in countrylanguage", query: "Count total languages in countrylanguage" },
      { label: "➕ Create a new table in world", query: "Create a new table for country_presidents in world" },
      { label: "🛑 Guardrail Test", query: "Write a poem about cats", isOfftopic: true }
    ];
  } else {
    const t1 = tables[0]?.name || 'table_1';
    const t2 = tables[1]?.name || t1;
    samplePrompts = [
      { label: `📊 Show data from ${t1}`, query: `Show top 10 records from \`${t1}\` in \`${activeDb}\`` },
      { label: `🔢 Count rows in ${t2}`, query: `Count total rows in \`${t2}\` in \`${activeDb}\`` },
      { label: `➕ Create table in ${activeDb}`, query: `Create a new table for logs in \`${activeDb}\`` },
      { label: "🛑 Guardrail Test", query: "Write a recipe for pizza", isOfftopic: true }
    ];
  }

  return (
    <div className="chat-container">
      <div className="messages-list">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.sender}`}>
            <div className={`avatar ${msg.sender}`}>
              {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div className="message-bubble">
              {/* Guardrail trigger alert */}
              {!msg.is_relevant && msg.guardrail_message && (
                <div className="guardrail-card">
                  <ShieldAlert size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong style={{ fontSize: '0.9rem', color: '#fca5a5' }}>Database Guardrail Triggered</strong>
                    <p style={{ fontSize: '0.84rem', marginTop: '4px', lineHeight: 1.5 }}>
                      The chatbot is restricted to query and manipulate data in your connected MySQL databases only. Off-topic non-SQL questions are blocked.
                    </p>
                  </div>
                </div>
              )}

              {/* Response markdown */}
              <div style={{ fontSize: '0.92rem', lineHeight: 1.6 }}>
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>

              {/* SQL Code Block */}
              {msg.sql && (
                <div className="sql-box">
                  <div className="sql-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Terminal size={14} />
                      <span>Generated MySQL Query</span>
                      <span style={{
                        fontSize: '0.68rem',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        background: msg.operation_type === 'READ' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: msg.operation_type === 'READ' ? '#93c5fd' : '#fcd34d',
                        fontWeight: 600
                      }}>
                        {msg.operation_type || 'READ'}
                      </span>
                    </div>

                    <button
                      onClick={() => handleCopy(msg.sql, idx)}
                      style={{ background: 'transparent', border: 'none', color: '#93c5fd', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
                    >
                      {copiedIdx === idx ? <Check size={14} style={{ color: '#34d399' }} /> : <Copy size={14} />}
                      <span>{copiedIdx === idx ? 'Copied' : 'Copy SQL'}</span>
                    </button>
                  </div>
                  <pre className="sql-code">{msg.sql}</pre>
                </div>
              )}

              {/* Confirmation Gate Buttons */}
              {msg.requires_confirmation && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginTop: '14px',
                  padding: '12px',
                  borderRadius: '10px',
                  background: 'rgba(244, 63, 94, 0.1)',
                  border: '1px solid rgba(244, 63, 94, 0.3)'
                }}>
                  <button
                    className="btn-primary"
                    style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', border: 'none', fontSize: '0.84rem' }}
                    onClick={() => onSendMessage("yes", { confirmed: true, pending_sql: msg.pending_sql || msg.sql })}
                  >
                    <Check size={14} /> Confirm Action
                  </button>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: '0.84rem' }}
                    onClick={() => onSendMessage("cancel")}
                  >
                    Cancel Action
                  </button>
                </div>
              )}

              {/* Data Table Grid */}
              {msg.columns && msg.columns.length > 0 && (
                <DataGrid
                  columns={msg.columns}
                  rows={msg.rows}
                  executionTimeMs={msg.executionTimeMs}
                  affectedRows={msg.affectedRows}
                  sql={msg.sql}
                />
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="avatar assistant">
              <Bot size={18} />
            </div>
            <div className="message-bubble" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid rgba(59,130,246,0.3)', borderTopColor: '#3b82f6', borderRadius: '50%' }} />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                LangGraph Agent inspecting MySQL schema & generating query...
              </span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Suggested Prompts */}
      <div className="quick-prompts">
        {samplePrompts.map((p, i) => (
          <button
            key={i}
            className={`prompt-chip ${p.isOfftopic ? 'offtopic' : ''}`}
            onClick={() => handlePromptClick(p.query)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-input-box">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask a question about your tables or ask to create/add data in MySQL..."
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !currentInput.trim()}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
