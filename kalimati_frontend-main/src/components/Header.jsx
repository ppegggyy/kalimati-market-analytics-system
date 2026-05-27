// src/components/Header.jsx
import { useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import '../styles/components.css';

export function Header({ setIsSidebarOpen }) {
  const location = useLocation();

  const getPageTitle = () => {
    switch(location.pathname) {
      case '/': return { title: 'Market Overview', subtitle: 'Comprehensive analysis of Kalimati agricultural commodities' };
      case '/volatility': return { title: 'Volatility Analysis', subtitle: 'Identify market instability and price fluctuations' };
      case '/forecast': return { title: 'Price Forecasting', subtitle: 'Predictive analytics using ARIMA statistical models' };
      default: return { title: 'Market Intelligence', subtitle: 'Manage and track your analytics' };
    }
  };

  const { title, subtitle } = getPageTitle();

  return (
    <header className="top-header">
      <div className="header-left">
        <button 
          className="mobile-menu-btn" 
          onClick={() => setIsSidebarOpen(true)}
          aria-label="Open Menu"
        >
          <Menu size={28} strokeWidth={2.5} />
        </button>
        <div className="header-title-area">
          <h1 className="h1">{title}</h1>
          <p className="subtitle">{subtitle}</p>
        </div>
      </div>
    </header>
  );
}
