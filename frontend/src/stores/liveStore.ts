import { create } from 'zustand';

export interface LiveEvent {
  type: string;
  id: string;
  timestamp: string;
  model: string;
  status: string;
  latency_ms: number;
  injection_score?: number;
  hallucination_score?: number;
  cost?: number;
}

interface LiveState {
  events: LiveEvent[];
  requestsPerMin: number;
  blocksPerMin: number;
  avgSafetyScore: number;
  isConnected: boolean;
  addEvent: (event: LiveEvent) => void;
  setConnected: (connected: boolean) => void;
  clearEvents: () => void;
}

export const useLiveStore = create<LiveState>((set) => ({
  events: [],
  requestsPerMin: 0,
  blocksPerMin: 0,
  avgSafetyScore: 0,
  isConnected: false,

  addEvent: (event) => {
    set((state) => {
      const newEvents = [event, ...state.events].slice(0, 100);
      const oneMinAgo = new Date(Date.now() - 60000).toISOString();
      const recent = newEvents.filter(e => e.timestamp > oneMinAgo);
      const blocks = recent.filter(e => e.status === 'blocked').length;
      const avgScore = recent.length > 0
        ? recent.reduce((sum, e) => sum + (e.injection_score || 0), 0) / recent.length
        : 0;
      return {
        events: newEvents,
        requestsPerMin: recent.length,
        blocksPerMin: blocks,
        avgSafetyScore: Math.round(avgScore * 100) / 100,
      };
    });
  },

  setConnected: (connected) => set({ isConnected: connected }),
  clearEvents: () => set({ events: [], requestsPerMin: 0, blocksPerMin: 0, avgSafetyScore: 0 }),
}));
