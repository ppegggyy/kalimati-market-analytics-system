// src/pages/VolatilityComparison.jsx
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { AlertCircle } from 'lucide-react';
import { fetchProducts, fetchVolatility } from '../api';
import '../styles/components.css';

const MAX_PRODUCTS = 20;

export function VolatilityComparison() {
  const [volatilityData, setVolatilityData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadVolatility() {
      setLoading(true);
      setError(null);
      try {
        const allProducts = await fetchProducts();
        const top20 = allProducts.slice(0, MAX_PRODUCTS);
        const results = await Promise.allSettled(
          top20.map((product) => fetchVolatility(product))
        );

        const data = results
          .map((r, i) => {
            if (r.status === 'fulfilled') {
              return {
                name: top20[i],
                std_dev: r.value.std_dev_avg_price,
                unit: r.value.unit,
                count: r.value.record_count,
              };
            }
            return null;
          })
          .filter(Boolean)
          .sort((a, b) => b.std_dev - a.std_dev);

        setVolatilityData(data);
      } catch (err) {
        setError('Failed to load volatility data. Is the backend running?');
      } finally {
        setLoading(false);
      }
    }
    loadVolatility();
  }, []);

  const getVolatilityBadge = (stdDev) => {
    if (stdDev > 30) return <span className="metric-badge negative">High Risk</span>;
    if (stdDev > 10) return <span className="metric-badge neutral" style={{color: 'var(--accent-warning)', background: 'rgba(245, 158, 11, 0.1)'}}>Medium Risk</span>;
    return <span className="metric-badge positive">Stable</span>;
  };

  return (
    <div>
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="state-container">Loading volatility analysis...</div>
      ) : (
        <div className="dashboard-grid">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Market Volatility Index (Top {MAX_PRODUCTS})</h2>
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volatilityData} margin={{ top: 10, right: 30, left: 10, bottom: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                  <XAxis 
                    dataKey="name" 
                    stroke="var(--text-light)" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                    height={120}
                  />
                  <YAxis 
                    stroke="var(--text-light)" 
                    fontSize={12} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(val) => `Rs ${val}`}
                    width={80}
                  />
                  <Tooltip 
                    cursor={{ fill: 'var(--bg-app)' }}
                    contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                    formatter={(val) => [`Rs. ${Number(val).toFixed(2)}`, 'Std Deviation']}
                  />
                  <Bar 
                    dataKey="std_dev" 
                    fill="var(--accent-primary)" 
                    radius={[6, 6, 0, 0]} 
                    barSize={32}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Detailed Volatility Metrics</h2>
            </div>
            <div className="data-grid-container">
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>Commodity</th>
                    <th>Unit Measurement</th>
                    <th>Standard Deviation (Rs)</th>
                    <th>Data Points Tracked</th>
                    <th>Risk Status</th>
                  </tr>
                </thead>
                <tbody>
                  {volatilityData.map((item) => (
                    <tr key={item.name}>
                      <td style={{ fontWeight: 600 }}>{item.name}</td>
                      <td>{item.unit}</td>
                      <td>Rs. {Number(item.std_dev).toFixed(2)}</td>
                      <td>{item.count} records</td>
                      <td>{getVolatilityBadge(item.std_dev)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}