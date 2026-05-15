import { useAuthStore } from '../../stores/authStore';
import { useLocation } from 'react-router-dom';
import './Header.css';

const pageTitles: Record<string, string> = {
  '/': 'Live Monitor',
  '/analytics': 'Analytics Dashboard',
  '/audit': 'Audit Explorer',
  '/policies': 'Policy Manager',
  '/compare': 'Model Comparison',
  '/settings': 'Settings',
};

export default function Header() {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'Dashboard';

  return (
    <header className="header">
      <div className="header-left">
        <h2 className="header-title">{title}</h2>
      </div>
      <div className="header-right">
        <div className="header-user">
          <div className="user-avatar">
            {user?.email?.charAt(0).toUpperCase() || 'A'}
          </div>
          <div className="user-info">
            <span className="user-email">{user?.email}</span>
            <span className="user-role">{user?.role}</span>
          </div>
          <button className="btn btn-sm btn-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
