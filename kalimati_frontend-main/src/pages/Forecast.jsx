// src/pages/Forecast.jsx
import { useState, useEffect } from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { AlertCircle, Target, TrendingUp, Calendar } from 'lucide-react';
import { fetchProducts, fetchForecast } from '../api';
import '../styles/components.css';

export function Forecast() {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [steps, setSteps] = useState(30);
  
  const [chartData, setChartData] = useState([]);
  const [modelUsed, setModelUsed] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProducts()
      .then((list) => {
        setProducts(list);
        if (list.length > 0) setSelectedProduct(list[0]);
      })
      .catch(() => setError('Could not load products. Is the backend running?'));
  }, []);

  useEffect(() => {
    if (!selectedProduct) return;
    setLoading(true);
    setError(null);

    fetchForecast(selectedProduct, steps)
      .then((data) => {
        setModelUsed(data.model_used || 'ARIMA');
        setChartData(
          data.forecast.map((point) => ({
            date: point.record_date,
            forecast: point.predicted_avg_price,
            band: [point.lower_bound ?? 0, point.upper_bound ?? point.predicted_avg_price],
          }))
        );
      })
      .catch(() => setError('Failed to load ARIMA forecast. Check backend connection.'))
      .finally(() => setLoading(false));
  }, [selectedProduct, steps]);

  const currentPrediction = chartData.length > 0 ? chartData[0].forecast : 0;
  const futurePrediction = chartData.length > 0 ? chartData[chartData.length - 1].forecast : 0;
  const expectedShift = currentPrediction ? ((futurePrediction - currentPrediction) / currentPrediction * 100).toFixed(1) : 0;

  return (
    <div>
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Controls */}
      <div className="controls-row">
        <div className="control-group">
          <label htmlFor="product">Commodity</label>
          <select
            id="product"
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            className="input-select"
          >
            {products.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div className="control-group">
          <label htmlFor="steps">Forecast Horizon</label>
          <select
            id="steps"
            value={steps}
            onChange={(e) => setSteps(Number(e.target.value))}
            className="input-select"
          >
            {[7, 14, 30, 60, 90].map((n) => <option key={n} value={n}>{n} Days</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="state-container">Computing {modelUsed || 'ARIMA'} predictions...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Top Analytical Metrics */}
          <div>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon-wrapper" style={{ color: 'var(--accent-primary)', backgroundColor: 'rgba(4, 120, 87, 0.1)' }}>
                  <Calendar size={26} />
                </div>
                <div className="metric-content">
                  <span className="metric-label">Forecast Horizon</span>
                  <span className="metric-value">{steps} Days</span>
                  <div className="metric-footer">
                    <span className="caption">Model: {modelUsed}</span>
                  </div>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrapper" style={{ color: 'var(--accent-info)', backgroundColor: 'rgba(14, 165, 233, 0.1)' }}>
                  <Target size={26} />
                </div>
                <div className="metric-content">
                  <span className="metric-label">Start Prediction</span>
                  <span className="metric-value">Rs. {currentPrediction.toFixed(2)}</span>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrapper" style={{ color: 'var(--accent-secondary)', backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <TrendingUp size={26} />
                </div>
                <div className="metric-content">
                  <span className="metric-label">End Prediction</span>
                  <span className="metric-value">Rs. {futurePrediction.toFixed(2)}</span>
                  <div className="metric-footer">
                    <span className={`metric-badge ${expectedShift > 0 ? 'negative' : expectedShift < 0 ? 'positive' : 'neutral'}`}>
                      {expectedShift > 0 ? '+' : ''}{expectedShift}% Shift
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Predictive Trajectory & 95% Confidence Interval</h2>
            </div>
            
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                  <XAxis 
                    dataKey="date" 
                    stroke="var(--text-light)" 
                    fontSize={13} 
                    tickLine={false} 
                    axisLine={false}
                    minTickGap={40}
                    tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis 
                    stroke="var(--text-light)" 
                    fontSize={13} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(val) => `Rs ${val}`}
                    width={80}
                  />
                  <Tooltip 
                    contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                    formatter={(val, name) => {
                      if (name === '95% Confidence') return ['', ''];
                      return [`Rs. ${Number(val).toFixed(2)}`, 'Predicted Avg'];
                    }}
                    labelFormatter={(label) => new Date(label).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                  />
                  
                  {/* Confidence interval band */}
                  <Area 
                    type="monotone" 
                    dataKey="band" 
                    fill="url(#colorBand)" 
                    stroke="none" 
                    name="95% Confidence" 
                  />
                  
                  {/* Forecast line */}
                  <Line 
                    type="monotone" 
                    dataKey="forecast" 
                    stroke="var(--accent-primary)" 
                    strokeWidth={3} 
                    dot={false} 
                    name="Predicted Avg" 
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}