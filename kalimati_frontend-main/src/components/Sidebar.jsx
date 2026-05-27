import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, LineChart, Leaf } from 'lucide-react';
import '../styles/components.css';

export function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/volatility', label: 'Volatility Analysis', icon: TrendingUp },
    { path: '/forecast', label: 'Price Forecast', icon: LineChart },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <Leaf className="brand-icon" size={28} strokeWidth={2.5} />
        <span className="brand-name">Kalimati</span>
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
            >
              <Icon className="nav-icon" size={20} strokeWidth={isActive ? 2.5 : 2} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
