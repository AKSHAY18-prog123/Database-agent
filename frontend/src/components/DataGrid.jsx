import React, { useState } from 'react';
import { Download, Search, ArrowUpDown, Clock, CheckCircle } from 'lucide-react';

export function DataGrid({ columns = [], rows = [], executionTimeMs = 0, affectedRows = 0, sql = '' }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  if (!columns.length && !rows.length) {
    return null;
  }

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(col);
      setSortDir('asc');
    }
  };

  const filteredRows = rows.filter(row => {
    if (!searchTerm) return true;
    return Object.values(row).some(val =>
      String(val ?? '').toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  const sortedRows = [...filteredRows].sort((a, b) => {
    if (!sortCol) return 0;
    const valA = a[sortCol];
    const valB = b[sortCol];
    if (valA == null) return 1;
    if (valB == null) return -1;

    if (typeof valA === 'number' && typeof valB === 'number') {
      return sortDir === 'asc' ? valA - valB : valB - valA;
    }
    return sortDir === 'asc'
      ? String(valA).localeCompare(String(valB))
      : String(valB).localeCompare(String(valA));
  });

  const downloadCSV = () => {
    if (!columns.length || !rows.length) return;
    const header = columns.join(',');
    const csvRows = rows.map(r =>
      columns.map(col => {
        const val = r[col] ?? '';
        return `"${String(val).replace(/"/g, '""')}"`;
      }).join(',')
    );
    const blob = new Blob([[header, ...csvRows].join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_result_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="data-table-wrapper">
      <div className="data-table-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#34d399' }}>
            <CheckCircle size={14} />
            <span>{rows.length} rows returned</span>
          </div>
          {executionTimeMs > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              <Clock size={12} />
              <span>{executionTimeMs} ms</span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={13} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              type="text"
              placeholder="Search table..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                padding: '4px 10px 4px 28px',
                fontSize: '0.78rem',
                borderRadius: '16px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-color)',
                color: 'white',
                outline: 'none'
              }}
            />
          </div>

          <button
            onClick={downloadCSV}
            className="btn-secondary"
            style={{ padding: '4px 10px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '4px' }}
            title="Download results as CSV"
          >
            <Download size={13} />
            <span>CSV</span>
          </button>
        </div>
      </div>

      <div className="table-scroll">
        <table className="custom-table">
          <thead>
            <tr>
              {columns.map(col => (
                <th key={col} onClick={() => handleSort(col)} style={{ cursor: 'pointer' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{col}</span>
                    <ArrowUpDown size={12} style={{ opacity: sortCol === col ? 1 : 0.4, color: sortCol === col ? '#60a5fa' : 'inherit' }} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-dim)' }}>
                  No matching records found
                </td>
              </tr>
            ) : (
              sortedRows.map((row, idx) => (
                <tr key={idx}>
                  {columns.map(col => (
                    <td key={col}>{row[col] !== null && row[col] !== undefined ? String(row[col]) : <em style={{ color: 'var(--text-dim)' }}>NULL</em>}</td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
