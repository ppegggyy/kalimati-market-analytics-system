import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, LineChart, Leaf, X } from 'lucide-react';
import '../styles/components.css';

export function Sidebar({ isSidebarOpen, setIsSidebarOpen }) {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/volatility', label: 'Volatility Analysis', icon: TrendingUp },
    { path: '/forecast', label: 'Price Forecast', icon: LineChart },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isSidebarOpen && (
        <div 
          className="sidebar-overlay" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="brand">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Leaf className="brand-icon" size={28} strokeWidth={2.5} />
            <span className="brand-name">Kalimati</span>
          </div>
          {/* Mobile Close Button */}
          <button 
            className="mobile-close-btn" 
            onClick={() => setIsSidebarOpen(false)}
            aria-label="Close Menu"
          >
            <X size={24} strokeWidth={2.5} />
          </button>
        </div>
        
        <nav className="nav-menu">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link 
                key={item.path} 
                to={item.path} 
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setIsSidebarOpen(false)} // Close drawer on navigation
              >
                <Icon className="nav-icon" size={20} strokeWidth={isActive ? 2.5 : 2} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
