import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { MobileNav } from './components/MobileNav';
import { Dashboard } from './pages/Dashboard';
import { VolatilityComparison } from './pages/VolatilityComparison';
import { Forecast } from './pages/Forecast';
import './styles/global.css';
import './styles/components.css';

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    document.body.style.overflow = isSidebarOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [isSidebarOpen]);

  return (
    <Router>
      <div className="app-layout">
        <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
        <main className="main-content">
          <Header setIsSidebarOpen={setIsSidebarOpen} />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/volatility" element={<VolatilityComparison />} />
              <Route path="/forecast" element={<Forecast />} />
            </Routes>
          </div>
        </main>
        <MobileNav />
      </div>
    </Router>
  );
}

export default App;
