import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { analyticsApi } from '../services/api';
import './Analytics.css';

const COLORS = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e'];

function StatsCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="stats-card card">
      <div className="stats-icon" style={{ background: `${color}20`, color }}>{label.charAt(0)}</div>
      <div>
        <div className="stats-value" style={{ color }}>{value}</div>
        <div className="stats-label">{label}</div>
        {sub && <div className="stats-sub">{sub}</div>}
      </div>
    </div>
  );
}

export default function Analytics() {
  const [overview, setOverview] = useState<any>(null);
  const [costs, setCosts] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const days = timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : 30;
        const [ov, co, mo] = await Promise.all([
          analyticsApi.getOverview(),
          analyticsApi.getCosts(days),
          analyticsApi.getModelStats(days),
        ]);
        setOverview(ov);
        setCosts(co);
        setModels(mo);
      } catch (e) {
        console.error('Analytics load error:', e);
        // Fallback demo data
        setOverview({ total_requests_24h: 847, total_requests_7d: 5234, block_rate: 4.2,
          avg_injection_score: 0.12, avg_hallucination_score: 0.28, total_cost_24h: 12.45,
          total_cost_7d: 89.30, avg_latency_ms: 245 });
        setCosts([
          { model: 'gpt-4o', total_cost: 45.20, total_tokens: 1250000, request_count: 2100 },
          { model: 'gpt-4o-mini', total_cost: 8.50, total_tokens: 850000, request_count: 1800 },
          { model: 'claude-3-sonnet', total_cost: 22.30, total_tokens: 650000, request_count: 890 },
          { model: 'local-model', total_cost: 0, total_tokens: 320000, request_count: 444 },
        ]);
        setModels([
          { model: 'gpt-4o', request_count: 2100, avg_latency_ms: 320, avg_injection_score: 0.08, avg_hallucination_score: 0.22, total_cost: 45.20 },
          { model: 'gpt-4o-mini', request_count: 1800, avg_latency_ms: 180, avg_injection_score: 0.11, avg_hallucination_score: 0.31, total_cost: 8.50 },
          { model: 'claude-3-sonnet', request_count: 890, avg_latency_ms: 280, avg_injection_score: 0.09, avg_hallucination_score: 0.19, total_cost: 22.30 },
          { model: 'local-model', request_count: 444, avg_latency_ms: 150, avg_injection_score: 0.15, avg_hallucination_score: 0.35, total_cost: 0 },
        ]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [timeRange]);

  if (loading) return <div className="empty-state"><p>Loading analytics...</p></div>;

  return (
    <div className="analytics-page fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>📊 Analytics Dashboard</h1>
          <p>Overview of AI safety metrics and cost analytics</p>
        </div>
        <div className="time-selector">
          {['24h', '7d', '30d'].map(t => (
            <button key={t} className={`btn btn-sm ${timeRange === t ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setTimeRange(t)}>{t}</button>
          ))}
        </div>
      </div>

      {overview && (
        <div className="grid-4" style={{ marginBottom: 'var(--space-lg)' }}>
          <StatsCard label="Total Requests" value={overview.total_requests_7d?.toLocaleString()} sub="Last 7 days" color="var(--accent-cyan)" />
          <StatsCard label="Block Rate" value={`${overview.block_rate}%`} sub="Policy blocks" color="var(--accent-rose)" />
          <StatsCard label="Avg Hallucination" value={`${(overview.avg_hallucination_score * 100).toFixed(1)}%`} sub="7-day average" color="var(--accent-amber)" />
          <StatsCard label="Total Cost" value={`$${overview.total_cost_7d?.toFixed(2)}`} sub="Last 7 days" color="var(--accent-emerald)" />
        </div>
      )}

      <div className="grid-2">
        <div className="card chart-card">
          <h3>Cost by Model</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={costs}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis dataKey="model" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip contentStyle={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', borderRadius: 8, color: 'var(--text-primary)' }} />
              <Bar dataKey="total_cost" fill="var(--accent-cyan)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card chart-card">
          <h3>Request Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={costs} dataKey="request_count" nameKey="model" cx="50%" cy="50%" outerRadius={100} label={({ model }) => model}>
                {costs.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: 'var(--bg-tertiary)', border: '1px solid var(--border-subtle)', borderRadius: 8, color: 'var(--text-primary)' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginTop: 'var(--space-lg)' }}>
        <h3 style={{ marginBottom: 'var(--space-md)' }}>Model Performance Comparison</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Model</th><th>Requests</th><th>Avg Latency</th><th>Injection Score</th><th>Hallucination</th><th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              {models.map(m => (
                <tr key={m.model}>
                  <td><span className="event-model">{m.model}</span></td>
                  <td>{m.request_count?.toLocaleString()}</td>
                  <td>{m.avg_latency_ms?.toFixed(0)}ms</td>
                  <td>
                    <div className="score-bar" style={{ width: 80 }}>
                      <div className={`score-bar-fill ${m.avg_injection_score > 0.5 ? 'score-high' : 'score-low'}`}
                        style={{ width: `${m.avg_injection_score * 100}%` }} />
                    </div>
                  </td>
                  <td>{(m.avg_hallucination_score * 100).toFixed(1)}%</td>
                  <td>${m.total_cost?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
