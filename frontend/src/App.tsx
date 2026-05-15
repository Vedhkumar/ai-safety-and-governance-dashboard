import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import Sidebar from './components/common/Sidebar';
import Header from './components/common/Header';
import Login from './pages/Login';
import LiveMonitor from './pages/LiveMonitor';
import Analytics from './pages/Analytics';
import AuditExplorer from './pages/AuditExplorer';
import PolicyManager from './pages/PolicyManager';
import ModelComparison from './pages/ModelComparison';
import Settings from './pages/Settings';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <div className="page-content">{children}</div>
      </div>
    </div>
  );
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><DashboardLayout><LiveMonitor /></DashboardLayout></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><DashboardLayout><Analytics /></DashboardLayout></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute><DashboardLayout><AuditExplorer /></DashboardLayout></ProtectedRoute>} />
        <Route path="/policies" element={<ProtectedRoute><DashboardLayout><PolicyManager /></DashboardLayout></ProtectedRoute>} />
        <Route path="/compare" element={<ProtectedRoute><DashboardLayout><ModelComparison /></DashboardLayout></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><DashboardLayout><Settings /></DashboardLayout></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
