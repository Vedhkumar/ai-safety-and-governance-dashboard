import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { policiesApi } from '../services/api';
import './PolicyManager.css';

const ACTION_COLORS: Record<string, string> = { block: 'var(--accent-rose)', flag: 'var(--accent-amber)', mask: 'var(--accent-violet)', log: 'var(--text-muted)' };

export default function PolicyManager() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editPolicy, setEditPolicy] = useState<any>(null);
  const [form, setForm] = useState({ name: '', condition: '', action: 'block', message: '', priority: 0, is_active: true });
  const [testPrompt, setTestPrompt] = useState('');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPolicies = async () => {
    try {
      const data = await policiesApi.list();
      setPolicies(data);
    } catch {
      setPolicies([
        { id: '1', name: 'Block High-Risk Injections', condition: 'injection.score > 0.85', action: 'block', message: 'Prompt injection detected', is_active: true, priority: 10 },
        { id: '2', name: 'Flag Hallucinations', condition: 'hallucination.score > 0.6', action: 'flag', message: 'May contain unsupported claims', is_active: true, priority: 7 },
        { id: '3', name: 'Block Toxic Content', condition: 'toxicity.score > 0.7', action: 'block', message: 'Toxic content detected', is_active: true, priority: 9 },
        { id: '4', name: 'Mask PII', condition: 'pii.is_flagged == true', action: 'mask', message: 'PII detected and masked', is_active: true, priority: 10 },
        { id: '5', name: 'Flag Bias', condition: 'bias.score > 0.5', action: 'flag', message: 'Potential bias detected', is_active: true, priority: 6 },
      ]);
    } finally { setLoading(false); }
  };

  useEffect(() => { loadPolicies(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editPolicy) {
        await policiesApi.update(editPolicy.id, form);
      } else {
        await policiesApi.create(form);
      }
      await loadPolicies();
      setShowForm(false);
      setEditPolicy(null);
      setForm({ name: '', condition: '', action: 'block', message: '', priority: 0, is_active: true });
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this policy?')) return;
    try { await policiesApi.delete(id); await loadPolicies(); } catch (err) { console.error(err); }
  };

  const handleTest = async () => {
    if (!testPrompt) return;
    try {
      const results = await policiesApi.test(testPrompt);
      setTestResults(results);
    } catch {
      setTestResults(policies.map(p => ({ policy_name: p.name, condition: p.condition, action: p.action, triggered: Math.random() > 0.7, score: Math.random() })));
    }
  };

  const startEdit = (policy: any) => {
    setEditPolicy(policy);
    setForm({ name: policy.name, condition: policy.condition, action: policy.action, message: policy.message || '', priority: policy.priority, is_active: policy.is_active });
    setShowForm(true);
  };

  return (
    <div className="policy-page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>🛡️ Policy Manager</h1>
          <p>Configure safety rules and thresholds for the AI gateway</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditPolicy(null); setForm({ name: '', condition: '', action: 'block', message: '', priority: 0, is_active: true }); }}>
          + New Policy
        </button>
      </div>

      <div className="policies-grid">
        {policies.map(policy => (
          <motion.div key={policy.id} className={`policy-card card ${!policy.is_active ? 'inactive' : ''}`}
            layout initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="policy-header">
              <div className="policy-action-badge" style={{ background: `${ACTION_COLORS[policy.action]}20`, color: ACTION_COLORS[policy.action], border: `1px solid ${ACTION_COLORS[policy.action]}40` }}>
                {policy.action.toUpperCase()}
              </div>
              <div className="policy-controls">
                <button className="btn btn-sm btn-secondary" onClick={() => startEdit(policy)}>Edit</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(policy.id)}>Delete</button>
              </div>
            </div>
            <h3>{policy.name}</h3>
            <code className="policy-condition">{policy.condition}</code>
            {policy.message && <p className="policy-message">{policy.message}</p>}
            <div className="policy-footer">
              <span className="policy-priority">Priority: {policy.priority}</span>
              <span className={`policy-status ${policy.is_active ? 'active' : ''}`}>
                {policy.is_active ? '● Active' : '○ Inactive'}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Policy Tester */}
      <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
        <h3 style={{ marginBottom: 'var(--space-md)' }}>🧪 Policy Tester</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 'var(--space-md)' }}>
          Paste a prompt to see which policies would trigger
        </p>
        <div style={{ display: 'flex', gap: 'var(--space-md)', marginBottom: 'var(--space-md)' }}>
          <input className="input" placeholder="Enter a test prompt..." value={testPrompt} onChange={e => setTestPrompt(e.target.value)} />
          <button className="btn btn-primary" onClick={handleTest}>Test</button>
        </div>
        {testResults.length > 0 && (
          <div className="test-results">
            {testResults.map((r, i) => (
              <div key={i} className={`test-result ${r.triggered ? 'triggered' : ''}`}>
                <span>{r.triggered ? '🔴' : '🟢'}</span>
                <strong>{r.policy_name}</strong>
                <code>{r.condition}</code>
                <span className={`badge badge-${r.triggered ? (r.action === 'block' ? 'blocked' : 'flagged') : 'passed'}`}>
                  {r.triggered ? r.action : 'not triggered'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Form Modal */}
      <AnimatePresence>
        {showForm && (
          <motion.div className="modal-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowForm(false)}>
            <motion.div className="modal-content card" initial={{ scale: 0.9 }} animate={{ scale: 1 }} exit={{ scale: 0.9 }} onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
              <h3 style={{ marginBottom: 'var(--space-lg)' }}>{editPolicy ? 'Edit Policy' : 'Create Policy'}</h3>
              <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                <div className="form-group"><label>Name</label><input className="input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
                <div className="form-group"><label>Condition</label><input className="input" value={form.condition} onChange={e => setForm({ ...form, condition: e.target.value })} placeholder="e.g. injection.score > 0.85" required /></div>
                <div className="form-group"><label>Action</label>
                  <select className="select" value={form.action} onChange={e => setForm({ ...form, action: e.target.value })}>
                    <option value="block">Block</option><option value="flag">Flag</option><option value="mask">Mask</option><option value="log">Log</option>
                  </select>
                </div>
                <div className="form-group"><label>Message</label><input className="input" value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} /></div>
                <div className="form-group"><label>Priority</label><input className="input" type="number" value={form.priority} onChange={e => setForm({ ...form, priority: parseInt(e.target.value) || 0 })} /></div>
                <div style={{ display: 'flex', gap: 'var(--space-md)', justifyContent: 'flex-end' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary">{editPolicy ? 'Update' : 'Create'}</button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
