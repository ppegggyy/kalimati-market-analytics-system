import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, LineChart } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/volatility', label: 'Volatility', icon: TrendingUp },
  { path: '/forecast', label: 'Forecast', icon: LineChart },
];

export function MobileNav() {
  const location = useLocation();

  return (
    <nav className="mobile-bottom-nav" aria-label="Main navigation">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        return (
          <Link
            key={item.path}
            to={item.path}
            className={`mobile-bottom-nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
