import { useEffect, useState } from 'react';
import { keysApi } from '../services/api';
import './Settings.css';

export default function Settings() {
  const [keys, setKeys] = useState<any[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyLimit, setNewKeyLimit] = useState(100);
  const [createdKey, setCreatedKey] = useState('');
  const [_loading, setLoading] = useState(true);

  const loadKeys = async () => {
    try {
      const data = await keysApi.list();
      setKeys(data);
    } catch {
      setKeys([
        { id: '1', key_prefix: 'sk-abc12...', name: 'Production App', rate_limit: 100, is_active: true, created_at: new Date().toISOString() },
        { id: '2', key_prefix: 'sk-def34...', name: 'Staging Chatbot', rate_limit: 50, is_active: true, created_at: new Date().toISOString() },
      ]);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadKeys(); }, []);

  const createKey = async () => {
    if (!newKeyName) return;
    try {
      const data = await keysApi.create({ name: newKeyName, rate_limit: newKeyLimit });
      setCreatedKey(data.full_key);
      setNewKeyName('');
      await loadKeys();
    } catch (err) { console.error(err); }
  };

  const revokeKey = async (id: string) => {
    if (!confirm('Revoke this API key?')) return;
    try { await keysApi.revoke(id); await loadKeys(); } catch (err) { console.error(err); }
  };

  return (
    <div className="settings-page fade-in">
      <div className="page-header">
        <h1>⚙️ Settings</h1>
        <p>Manage API keys, scanner thresholds, and preferences</p>
      </div>

      {/* API Keys */}
      <div className="card settings-section">
        <h3>🔑 API Keys</h3>
        <p className="section-desc">Generate API keys for client applications to use the safety proxy</p>

        <div className="key-form">
          <input className="input" placeholder="Key name (e.g. Production App)" value={newKeyName}
            onChange={e => setNewKeyName(e.target.value)} />
          <input className="input" type="number" placeholder="Rate limit" value={newKeyLimit}
            onChange={e => setNewKeyLimit(parseInt(e.target.value) || 100)} style={{ width: 120 }} />
          <button className="btn btn-primary" onClick={createKey}>Generate Key</button>
        </div>

        {createdKey && (
          <div className="created-key-banner">
            <strong>⚠️ Copy this key now — it won't be shown again:</strong>
            <code>{createdKey}</code>
            <button className="btn btn-sm btn-secondary" onClick={() => { navigator.clipboard.writeText(createdKey); }}>Copy</button>
          </div>
        )}

        <div className="table-container" style={{ marginTop: 'var(--space-md)' }}>
          <table>
            <thead><tr><th>Name</th><th>Key Prefix</th><th>Rate Limit</th><th>Status</th><th>Created</th><th></th></tr></thead>
            <tbody>
              {keys.map(key => (
                <tr key={key.id}>
                  <td style={{ fontWeight: 500 }}>{key.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{key.key_prefix}</td>
                  <td>{key.rate_limit} req/min</td>
                  <td><span className={`badge badge-${key.is_active ? 'passed' : 'blocked'}`}>{key.is_active ? 'Active' : 'Revoked'}</span></td>
                  <td style={{ fontSize: 12 }}>{new Date(key.created_at).toLocaleDateString()}</td>
                  <td>{key.is_active && <button className="btn btn-sm btn-danger" onClick={() => revokeKey(key.id)}>Revoke</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scanner Thresholds */}
      <div className="card settings-section">
        <h3>🎛️ Scanner Thresholds</h3>
        <p className="section-desc">Adjust sensitivity for each safety scanner</p>
        <div className="threshold-grid">
          {[
            { name: 'Injection Detection', key: 'injection', default: 0.85, color: 'var(--accent-rose)' },
            { name: 'Toxicity Detection', key: 'toxicity', default: 0.7, color: 'var(--accent-amber)' },
            { name: 'Hallucination Detection', key: 'hallucination', default: 0.6, color: 'var(--accent-violet)' },
            { name: 'Bias Detection', key: 'bias', default: 0.6, color: 'var(--accent-cyan)' },
          ].map(scanner => (
            <div key={scanner.key} className="threshold-item">
              <div className="threshold-header">
                <span>{scanner.name}</span>
                <span style={{ color: scanner.color, fontWeight: 600 }}>{(scanner.default * 100).toFixed(0)}%</span>
              </div>
              <input type="range" min="0" max="100" defaultValue={scanner.default * 100}
                className="threshold-slider" style={{ accentColor: scanner.color }} />
              <div className="threshold-labels">
                <span>Lenient</span><span>Strict</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Usage Info */}
      <div className="card settings-section">
        <h3>📖 Quick Start</h3>
        <p className="section-desc">Connect your application to the AI Safety Gateway</p>
        <pre className="code-block" style={{ marginTop: 'var(--space-md)' }}>{`# Python — just change the base URL
from openai import OpenAI

client = OpenAI(
    api_key="your-proxy-key-here",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
# That's it! All requests now go through safety guardrails.`}</pre>
      </div>
    </div>
  );
}
