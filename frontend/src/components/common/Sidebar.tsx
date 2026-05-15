import { NavLink, useLocation } from 'react-router-dom';
import { useState } from 'react';
import './Sidebar.css';

const navItems = [
  { path: '/', label: 'Live Monitor', icon: '⚡' },
  { path: '/analytics', label: 'Analytics', icon: '📊' },
  { path: '/audit', label: 'Audit Explorer', icon: '📋' },
  { path: '/policies', label: 'Policy Manager', icon: '🛡️' },
  { path: '/compare', label: 'Model Comparison', icon: '⚖️' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">🛡️</span>
          {!collapsed && <span className="logo-text">AI Safety</span>}
        </div>
        <button
          className="collapse-btn"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
            end={item.path === '/'}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span className="nav-label">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && (
          <div className="sidebar-badge">
            <span className="pulse-dot"></span>
            <span>Gateway Active</span>
          </div>
        )}
      </div>
    </aside>
  );
}
