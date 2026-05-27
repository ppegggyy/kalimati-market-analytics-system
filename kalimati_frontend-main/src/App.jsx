import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { VolatilityComparison } from './pages/VolatilityComparison';
import { Forecast } from './pages/Forecast';
import './styles/global.css';

function App() {
  return (
    <Router>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Header />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/volatility" element={<VolatilityComparison />} />
              <Route path="/forecast" element={<Forecast />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
