import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { auditApi } from '../services/api';
import './AuditExplorer.css';

export default function AuditExplorer() {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [filters, setFilters] = useState({ model: '', status: '', search: '' });
  const [selectedLog, setSelectedLog] = useState<any>(null);
  const [_loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await auditApi.getLogs({ page, per_page: 20, ...filters });
      setLogs(data.logs);
      setTotal(data.total);
      setPages(data.pages);
    } catch {
      // Demo data
      const demoLogs = Array.from({ length: 20 }, (_, i) => ({
        id: `demo-${i}`, timestamp: new Date(Date.now() - i * 3600000).toISOString(),
        model: ['gpt-4o', 'gpt-4o-mini', 'claude-3-sonnet'][i % 3],
        input_prompt: 'What is the meaning of life?', output_response: 'The meaning of life is a philosophical question...',
        input_tokens: 50 + i * 10, output_tokens: 100 + i * 20,
        total_cost: 0.001 * (i + 1), latency_ms: 150 + i * 30,
        injection_score: Math.random() * 0.3, hallucination_score: Math.random() * 0.4,
        toxicity_scores: { toxic: Math.random() * 0.1 }, bias_score: Math.random() * 0.2,
        pii_detected: i % 7 === 0, final_status: ['passed', 'passed', 'passed', 'flagged', 'blocked'][i % 5],
      }));
      setLogs(demoLogs);
      setTotal(150);
      setPages(8);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadLogs(); }, [page, filters]);

  const exportData = (format: string) => {
    const data = format === 'json' ? JSON.stringify(logs, null, 2) : 
      [Object.keys(logs[0] || {}).join(','), ...logs.map(l => Object.values(l).map(v => typeof v === 'object' ? JSON.stringify(v) : v).join(','))].join('\n');
    const blob = new Blob([data], { type: format === 'json' ? 'application/json' : 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `audit-logs.${format}`; a.click();
  };

  return (
    <div className="audit-page fade-in">
      <div className="page-header">
        <h1>📋 Audit Explorer</h1>
        <p>Search and analyze the complete audit trail of all LLM requests</p>
      </div>

      <div className="filter-bar card">
        <input className="input" placeholder="Search prompts & responses..." value={filters.search}
          onChange={e => setFilters({ ...filters, search: e.target.value })} style={{ maxWidth: 300 }} />
        <select className="select" value={filters.model} onChange={e => setFilters({ ...filters, model: e.target.value })} style={{ maxWidth: 180 }}>
          <option value="">All Models</option>
          <option value="gpt-4o">GPT-4o</option>
          <option value="gpt-4o-mini">GPT-4o Mini</option>
          <option value="claude-3-sonnet">Claude 3 Sonnet</option>
          <option value="local-model">Local Model</option>
        </select>
        <select className="select" value={filters.status} onChange={e => setFilters({ ...filters, status: e.target.value })} style={{ maxWidth: 150 }}>
          <option value="">All Status</option>
          <option value="passed">✅ Passed</option>
          <option value="flagged">⚠️ Flagged</option>
          <option value="blocked">🚫 Blocked</option>
        </select>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="btn btn-sm btn-secondary" onClick={() => exportData('csv')}>Export CSV</button>
          <button className="btn btn-sm btn-secondary" onClick={() => exportData('json')}>Export JSON</button>
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        <div className="table-container">
          <table>
            <thead>
              <tr><th>Time</th><th>Model</th><th>Status</th><th>Prompt</th><th>Injection</th><th>Hallucination</th><th>Latency</th><th>Cost</th></tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id} onClick={() => setSelectedLog(log)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td><span className="event-model">{log.model}</span></td>
                  <td><span className={`badge badge-${log.final_status}`}>{log.final_status}</span></td>
                  <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{log.input_prompt}</td>
                  <td>{((log.injection_score || 0) * 100).toFixed(0)}%</td>
                  <td>{((log.hallucination_score || 0) * 100).toFixed(0)}%</td>
                  <td>{log.latency_ms}ms</td>
                  <td>${log.total_cost?.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="pagination">
        <span className="pagination-info">Showing {logs.length} of {total} logs</span>
        <div className="pagination-controls">
          <button className="btn btn-sm btn-secondary" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span className="page-num">Page {page} of {pages}</span>
          <button className="btn btn-sm btn-secondary" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      </div>

      <AnimatePresence>
        {selectedLog && (
          <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedLog(null)}>
            <motion.div className="modal-content card" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h3>Request Detail</h3>
                <button className="btn btn-sm btn-secondary" onClick={() => setSelectedLog(null)}>✕</button>
              </div>
              <div className="modal-body">
                <div className="detail-section">
                  <h4>Input Prompt</h4>
                  <pre className="code-block">{selectedLog.input_prompt}</pre>
                </div>
                <div className="detail-section">
                  <h4>Output Response</h4>
                  <pre className="code-block">{selectedLog.output_response || '(blocked)'}</pre>
                </div>
                <div className="detail-grid-3">
                  <div><strong>Model:</strong> {selectedLog.model}</div>
                  <div><strong>Status:</strong> <span className={`badge badge-${selectedLog.final_status}`}>{selectedLog.final_status}</span></div>
                  <div><strong>Latency:</strong> {selectedLog.latency_ms}ms</div>
                  <div><strong>Injection:</strong> {((selectedLog.injection_score || 0) * 100).toFixed(1)}%</div>
                  <div><strong>Hallucination:</strong> {((selectedLog.hallucination_score || 0) * 100).toFixed(1)}%</div>
                  <div><strong>Cost:</strong> ${selectedLog.total_cost?.toFixed(4)}</div>
                  <div><strong>Input Tokens:</strong> {selectedLog.input_tokens}</div>
                  <div><strong>Output Tokens:</strong> {selectedLog.output_tokens}</div>
                  <div><strong>PII Detected:</strong> {selectedLog.pii_detected ? '⚠️ Yes' : '✅ No'}</div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
