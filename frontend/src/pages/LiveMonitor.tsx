import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from '../hooks/useWebSocket';
import { useLiveStore } from '../stores/liveStore';
import type { LiveEvent } from '../stores/liveStore';
import './LiveMonitor.css';

function LiveCounter({ label, value, color }: { label: string; value: number | string; color: string }) {
  return (
    <div className="live-counter card">
      <div className="counter-value" style={{ color }}>{value}</div>
      <div className="counter-label">{label}</div>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'passed') return <span className="status-icon passed">✅</span>;
  if (status === 'blocked') return <span className="status-icon blocked">🚫</span>;
  return <span className="status-icon flagged">⚠️</span>;
}

function EventCard({ event, index }: { event: LiveEvent; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const time = new Date(event.timestamp).toLocaleTimeString();

  return (
    <motion.div
      className={`event-card card ${event.status}`}
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -40 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="event-row">
        <StatusIcon status={event.status} />
        <span className="event-time">{time}</span>
        <span className={`badge badge-${event.status}`}>{event.status}</span>
        <span className="event-model">{event.model}</span>
        <span className="event-latency">{event.latency_ms}ms</span>
        {event.injection_score !== undefined && (
          <div className="event-score">
            <span className="score-label">Inj:</span>
            <div className="score-bar" style={{ width: 60 }}>
              <div className={`score-bar-fill ${event.injection_score > 0.7 ? 'score-high' : event.injection_score > 0.4 ? 'score-medium' : 'score-low'}`}
                style={{ width: `${event.injection_score * 100}%` }} />
            </div>
            <span className="score-num">{(event.injection_score * 100).toFixed(0)}%</span>
          </div>
        )}
        {event.cost !== undefined && (
          <span className="event-cost">${event.cost.toFixed(4)}</span>
        )}
      </div>
      {expanded && (
        <motion.div className="event-details" initial={{ height: 0 }} animate={{ height: 'auto' }}>
          <div className="detail-grid">
            <div><strong>ID:</strong> {event.id}</div>
            <div><strong>Hallucination:</strong> {((event.hallucination_score || 0) * 100).toFixed(0)}%</div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default function LiveMonitor() {
  const { events, requestsPerMin, blocksPerMin, avgSafetyScore, isConnected } = useLiveStore();
  useWebSocket();

  // Generate simulated events for demo
  const { addEvent } = useLiveStore();
  useEffect(() => {
    if (events.length > 0) return;
    const models = ['gpt-4o', 'gpt-4o-mini', 'claude-3-sonnet', 'local-model'];
    const statuses = ['passed', 'passed', 'passed', 'flagged', 'blocked'];
    const interval = setInterval(() => {
      addEvent({
        type: 'request',
        id: Math.random().toString(36).slice(2, 14),
        timestamp: new Date().toISOString(),
        model: models[Math.floor(Math.random() * models.length)],
        status: statuses[Math.floor(Math.random() * statuses.length)],
        latency_ms: Math.floor(Math.random() * 400) + 80,
        injection_score: Math.random() * 0.5,
        hallucination_score: Math.random() * 0.4,
        cost: Math.random() * 0.01,
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="live-monitor fade-in">
      <div className="page-header">
        <h1>⚡ Live Monitor</h1>
        <p>Real-time feed of LLM requests flowing through the safety gateway</p>
      </div>

      <div className="grid-4" style={{ marginBottom: 'var(--space-lg)' }}>
        <LiveCounter label="Requests / min" value={requestsPerMin} color="var(--accent-cyan)" />
        <LiveCounter label="Blocks / min" value={blocksPerMin} color="var(--accent-rose)" />
        <LiveCounter label="Avg Safety Score" value={avgSafetyScore.toFixed(2)} color="var(--accent-emerald)" />
        <LiveCounter label="Connection" value={isConnected ? 'Live' : 'Demo Mode'} color={isConnected ? 'var(--accent-emerald)' : 'var(--accent-amber)'} />
      </div>

      <div className="event-feed">
        <AnimatePresence mode="popLayout">
          {events.map((event, i) => (
            <EventCard key={event.id + event.timestamp} event={event} index={i} />
          ))}
        </AnimatePresence>
        {events.length === 0 && (
          <div className="empty-state">
            <p>Waiting for requests...</p>
          </div>
        )}
      </div>
    </div>
  );
}
