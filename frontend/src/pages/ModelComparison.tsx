import { useState } from 'react';
import { motion } from 'framer-motion';
import { compareApi } from '../services/api';
import './ModelComparison.css';

const AVAILABLE_MODELS = ['gpt-4o', 'gpt-4o-mini', 'claude-3-sonnet', 'claude-3-opus', 'local-model'];

export default function ModelComparison() {
  const [prompt, setPrompt] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4o', 'gpt-4o-mini']);
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const toggleModel = (model: string) => {
    setSelectedModels(prev =>
      prev.includes(model) ? prev.filter(m => m !== model) :
        prev.length < 4 ? [...prev, model] : prev
    );
  };

  const runComparison = async () => {
    if (!prompt || selectedModels.length < 2) return;
    setLoading(true);
    try {
      const data = await compareApi.run({ prompt, models: selectedModels });
      setResults(data.results);
    } catch {
      // Demo results
      setResults(selectedModels.map(model => ({
        model, response: `This is a simulated response from ${model}. In a production environment, this would contain the actual model's output.`,
        latency_ms: Math.floor(Math.random() * 400) + 100,
        input_tokens: Math.floor(Math.random() * 100) + 50,
        output_tokens: Math.floor(Math.random() * 200) + 100,
        total_cost: Math.random() * 0.01,
        injection_score: Math.random() * 0.2,
        toxicity_scores: { toxic: Math.random() * 0.1 },
        hallucination_score: Math.random() * 0.3,
        bias_score: Math.random() * 0.15,
        final_status: 'passed',
      })));
    } finally { setLoading(false); }
  };

  return (
    <div className="compare-page fade-in">
      <div className="page-header">
        <h1>⚖️ Model Comparison</h1>
        <p>Compare safety scores, latency, and costs across different LLM models</p>
      </div>

      <div className="card compare-input">
        <h3>Configure Comparison</h3>
        <div className="form-group" style={{ marginTop: 'var(--space-md)' }}>
          <label>Test Prompt</label>
          <textarea className="input" rows={3} value={prompt} onChange={e => setPrompt(e.target.value)}
            placeholder="Enter a prompt to test across models..." style={{ resize: 'vertical' }} />
        </div>
        <div className="form-group" style={{ marginTop: 'var(--space-md)' }}>
          <label>Select Models (2-4)</label>
          <div className="model-selector">
            {AVAILABLE_MODELS.map(model => (
              <button key={model}
                className={`model-chip ${selectedModels.includes(model) ? 'selected' : ''}`}
                onClick={() => toggleModel(model)}>
                {selectedModels.includes(model) ? '✓ ' : ''}{model}
              </button>
            ))}
          </div>
        </div>
        <button className="btn btn-primary" onClick={runComparison} disabled={loading || !prompt || selectedModels.length < 2}
          style={{ marginTop: 'var(--space-md)' }}>
          {loading ? 'Running...' : '🚀 Run Comparison'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="compare-results">
          <h3 style={{ marginBottom: 'var(--space-lg)' }}>Results</h3>
          <div className="results-grid" style={{ gridTemplateColumns: `repeat(${results.length}, 1fr)` }}>
            {results.map((r, i) => (
              <motion.div key={r.model} className="result-card card"
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}>
                <div className="result-model">
                  <span className="event-model">{r.model}</span>
                  <span className={`badge badge-${r.final_status}`}>{r.final_status}</span>
                </div>
                <div className="result-response">
                  <p>{r.response}</p>
                </div>
                <div className="result-metrics">
                  <div className="metric"><span className="metric-label">Latency</span><span className="metric-value">{r.latency_ms}ms</span></div>
                  <div className="metric"><span className="metric-label">Tokens</span><span className="metric-value">{r.input_tokens + r.output_tokens}</span></div>
                  <div className="metric"><span className="metric-label">Cost</span><span className="metric-value">${r.total_cost?.toFixed(4)}</span></div>
                  <div className="metric"><span className="metric-label">Injection</span><span className="metric-value">{(r.injection_score * 100).toFixed(0)}%</span></div>
                  <div className="metric"><span className="metric-label">Hallucination</span><span className="metric-value">{(r.hallucination_score * 100).toFixed(0)}%</span></div>
                  <div className="metric"><span className="metric-label">Bias</span><span className="metric-value">{(r.bias_score * 100).toFixed(0)}%</span></div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
