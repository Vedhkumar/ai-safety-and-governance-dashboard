import { useAuthStore } from '../stores/authStore';

const BASE_URL = '/api';

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const token = useAuthStore.getState().accessToken;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  
  if (res.status === 401) {
    useAuthStore.getState().logout();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  
  return res.json();
}

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, role = 'viewer') =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password, role }) }),
};

// Audit Logs
export const auditApi = {
  getLogs: (params: Record<string, any> = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v != null && v !== '') searchParams.set(k, String(v)); });
    return request(`/audit/logs?${searchParams.toString()}`);
  },
  getLog: (id: string) => request(`/audit/logs/${id}`),
};

// Analytics
export const analyticsApi = {
  getOverview: () => request('/analytics/overview'),
  getSafetyTrends: (hours = 168) => request(`/analytics/safety?hours=${hours}`),
  getCosts: (days = 7) => request(`/analytics/costs?days=${days}`),
  getModelStats: (days = 7) => request(`/analytics/models?days=${days}`),
  getHeatmap: (days = 7) => request(`/analytics/heatmap?days=${days}`),
};

// Policies
export const policiesApi = {
  list: () => request('/policies'),
  create: (data: any) => request('/policies', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: any) => request(`/policies/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) => request(`/policies/${id}`, { method: 'DELETE' }),
  test: (prompt: string) => request('/policies/test', { method: 'POST', body: JSON.stringify({ prompt }) }),
};

// API Keys
export const keysApi = {
  list: () => request('/keys'),
  create: (data: any) => request('/keys', { method: 'POST', body: JSON.stringify(data) }),
  revoke: (id: string) => request(`/keys/${id}`, { method: 'DELETE' }),
};

// Compare
export const compareApi = {
  run: (data: any) => request('/compare', { method: 'POST', body: JSON.stringify(data) }),
  get: (id: string) => request(`/compare/${id}`),
};
