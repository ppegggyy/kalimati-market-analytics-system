import { Link } from 'react-router-dom';
import '../styles/components.css';

export function Navigation() {
  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-link">Dashboard</Link>
        <Link to="/volatility" className="nav-link">Volatility Comparison</Link>
        <Link to="/forecast" className="nav-link">Forecast</Link>
      </div>
    </nav>
  );
}
