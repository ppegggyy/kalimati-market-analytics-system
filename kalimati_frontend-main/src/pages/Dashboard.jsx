// src/pages/Dashboard.jsx
import { useState, useEffect } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ComposedChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';
import { Activity, TrendingUp, Banknote, AlertCircle, Calendar } from 'lucide-react';
import { fetchProducts, fetchMovingAverage, fetchTrend, fetchLatestPrices } from '../api';
import '../styles/components.css';

function calculateAdvancedSeasonality(data) {
  const monthlyData = Array(12).fill(null).map(() => []);

  data.forEach(row => {
    if (!row.Date || !row['Avg Price']) return;
    const month = new Date(row.Date).getMonth();
    monthlyData[month].push(row['Avg Price']);
  });

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  return monthNames.map((name, i) => {
    const prices = monthlyData[i];
    if (prices.length === 0) return { month: name, avg: 0, min: 0, max: 0, volatility: 0, envelope: [0, 0] };
    
    const sum = prices.reduce((a, b) => a + b, 0);
    const avg = sum / prices.length;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    
    const variance = prices.reduce((acc, val) => acc + Math.pow(val - avg, 2), 0) / prices.length;
    const stdDev = Math.sqrt(variance);

    return {
      month: name,
      avg: Number(avg.toFixed(2)),
      min: Number(min.toFixed(2)),
      max: Number(max.toFixed(2)),
      volatility: Number(stdDev.toFixed(2)),
      envelope: [Number(min.toFixed(2)), Number(max.toFixed(2))] // For the Area band
    };
  });
}

function calculateShiftDistribution(data) {
  let up = 0, down = 0, stable = 0;
  for (let i = 1; i < data.length; i++) {
    const prev = data[i - 1]['Avg Price'];
    const curr = data[i]['Avg Price'];
    if (curr > prev) up++;
    else if (curr < prev) down++;
    else stable++;
  }
  return [
    { name: 'Price Increases', value: up, fill: 'var(--accent-warning)' },
    { name: 'Price Decreases', value: down, fill: 'var(--accent-primary)' },
    { name: 'Stable Days', value: stable, fill: 'var(--text-light)' }
  ];
}

export function Dashboard() {
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2026-05-22');
  
  const [chartData, setChartData] = useState([]);
  const [seasonalData, setSeasonalData] = useState([]);
  const [shiftData, setShiftData] = useState([]);
  const [trend, setTrend] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [latestPricesData, setLatestPricesData] = useState([]);
  const [loadingLatest, setLoadingLatest] = useState(true);

  useEffect(() => {
    fetchProducts()
      .then((list) => {
        setProducts(list);
        if (list.length > 0) setSelectedProduct(list[0]);
      })
      .catch(() => setError('Could not load products. Is the backend running?'));
      
    fetchLatestPrices()
      .then((data) => setLatestPricesData(data))
      .catch((err) => console.error('Failed to load latest prices', err))
      .finally(() => setLoadingLatest(false));
  }, []);

  useEffect(() => {
    if (!selectedProduct) return;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchMovingAverage(selectedProduct, 7, startDate, endDate),
      fetchTrend(selectedProduct, startDate, endDate),
    ])
      .then(([maData, trendData]) => {
        setChartData(
          maData.map((row) => ({
            date: row['Date'],
            price: row['Avg Price'],
            movingAvg: row['moving_avg_7d'] ?? null,
          }))
        );
        setSeasonalData(calculateAdvancedSeasonality(maData));
        setShiftData(calculateShiftDistribution(maData));
        setTrend(trendData);
      })
      .catch(() => setError('Failed to load chart data. Check backend logs.'))
      .finally(() => setLoading(false));
  }, [selectedProduct, startDate, endDate]);

  const latestPrice = chartData.length > 0 ? chartData[chartData.length - 1].price : 0;
  const prevPrice = chartData.length > 1 ? chartData[chartData.length - 2].price : latestPrice;
  const dayChange = latestPrice - prevPrice;
  const dayChangePct = prevPrice ? ((dayChange / prevPrice) * 100).toFixed(1) : 0;

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
          <label htmlFor="start-date">Analysis Start</label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="input-date"
          />
        </div>
        <div className="control-group">
          <label htmlFor="end-date">Analysis End</label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="input-date"
          />
        </div>
      </div>

      {loading ? (
        <div className="state-container">Computing market analytics...</div>
      ) : (
        <>
          {/* Top Metrics */}
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-icon-wrapper">
                <Banknote size={26} />
              </div>
              <div className="metric-content">
                <span className="metric-label">Current Market Rate</span>
                <span className="metric-value">Rs. {latestPrice.toFixed(2)}</span>
                <div className="metric-footer">
                  <span className={`metric-badge ${dayChange > 0 ? 'negative' : dayChange < 0 ? 'positive' : 'neutral'}`}>
                    {dayChange > 0 ? '+' : ''}{dayChangePct}% today
                  </span>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon-wrapper" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-secondary)' }}>
                <Activity size={26} />
              </div>
              <div className="metric-content">
                <span className="metric-label">Price Volatility Index</span>
                <span className="metric-value">
                  {trend?.volatility != null && !isNaN(Number(trend.volatility)) 
                    ? `Rs. ${Number(trend.volatility).toFixed(2)}` 
                    : '—'}
                </span>
                <div className="metric-footer">
                  <span className="caption">Std dev over period</span>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div className="metric-icon-wrapper" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', color: 'var(--accent-warning)' }}>
                <TrendingUp size={26} />
              </div>
              <div className="metric-content">
                <span className="metric-label">Historical Peak Value</span>
                <span className="metric-value">
                  {trend?.highest_price?.value != null && !isNaN(Number(trend.highest_price.value)) 
                    ? `Rs. ${Number(trend.highest_price.value).toFixed(2)}` 
                    : '—'}
                </span>
              </div>
            </div>
            
            <div className="metric-card">
              <div className="metric-icon-wrapper" style={{ backgroundColor: 'rgba(14, 165, 233, 0.1)', color: 'var(--accent-info)' }}>
                <Calendar size={26} />
              </div>
              <div className="metric-content">
                <span className="metric-label">Period Mean Price</span>
                <span className="metric-value">
                  {trend?.mean_price != null && !isNaN(Number(trend.mean_price)) 
                    ? `Rs. ${Number(trend.mean_price).toFixed(2)}` 
                    : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Main Chart */}
          <div className="card" style={{ marginBottom: 40 }}>
            <div className="card-header">
              <h2 className="card-title">Macro Price Trajectory & Moving Average</h2>
            </div>
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
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
                    formatter={(val) => [`Rs. ${Number(val).toFixed(2)}`]}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="price" 
                    stroke="var(--accent-primary)" 
                    strokeWidth={2.5}
                    fillOpacity={1} 
                    fill="url(#colorPrice)" 
                    name="Actual Price"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="movingAvg" 
                    stroke="var(--accent-info)" 
                    strokeWidth={2} 
                    strokeDasharray="6 4" 
                    fill="none" 
                    name="7-Day MA"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Advanced Analytics Grid */}
          <div className="dashboard-grid">
            
            {/* Min-Max Price Envelope */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Seasonal Price Range Envelope</h2>
              </div>
              <div className="chart-wrapper-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={seasonalData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis dataKey="month" stroke="var(--text-light)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-light)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={80} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                      formatter={(val, name) => {
                        if (name === 'Price Range (Min-Max)') return ['', ''];
                        return [`Rs. ${val}`, name];
                      }}
                    />
                    <Area type="monotone" dataKey="envelope" fill="rgba(4, 120, 87, 0.1)" stroke="none" name="Price Range (Min-Max)" />
                    <Line type="monotone" dataKey="avg" stroke="var(--accent-primary)" strokeWidth={3} dot={true} name="Average Price" />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Seasonal Volatility */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Seasonal Volatility (Monthly Std Dev)</h2>
              </div>
              <div className="chart-wrapper-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={seasonalData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis dataKey="month" stroke="var(--text-light)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-light)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={80} />
                    <Tooltip 
                      cursor={{ fill: 'var(--bg-app)' }}
                      contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                      formatter={(val) => [`Rs. ${val}`, 'Volatility (Std Dev)']}
                    />
                    <Bar dataKey="volatility" fill="var(--accent-warning)" radius={[6, 6, 0, 0]} barSize={28} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Distribution */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Market Stability Distribution</h2>
              </div>
              <div className="chart-wrapper-sm" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={shiftData}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={110}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                    >
                      {shiftData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                      formatter={(val) => [`${val} Days`, 'Occurrence']}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Recent 14-Day Trend */}
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Recent 14-Day Price Movement</h2>
              </div>
              <div className="chart-wrapper-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData.slice(-14)} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="var(--text-light)" 
                      fontSize={11} 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis stroke="var(--text-light)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={80} />
                    <Tooltip 
                      cursor={{ fill: 'var(--bg-app)' }}
                      contentStyle={{ borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-lg)' }}
                      formatter={(val) => [`Rs. ${Number(val).toFixed(2)}`, 'Price']}
                      labelFormatter={(label) => new Date(label).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                    />
                    <Bar dataKey="price" fill="var(--accent-info)" radius={[4, 4, 0, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
          </div>
          
          {/* Today's Market Snapshot */}
          <div className="card" style={{ marginTop: 24, marginBottom: 40 }}>
            <div className="card-header">
              <h2 className="card-title">Today's Market Snapshot</h2>
            </div>
            {loadingLatest ? (
              <div style={{ padding: 20 }}>Loading latest prices...</div>
            ) : (
              <div className="data-grid-container" style={{ maxHeight: 400, overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg-card)', zIndex: 1 }}>
                    <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)' }}>Product</th>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)' }}>Unit</th>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)' }}>Latest Date</th>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)', textAlign: 'right' }}>Min Price</th>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)', textAlign: 'right' }}>Max Price</th>
                      <th style={{ padding: '12px 16px', color: 'var(--text-light)', textAlign: 'right' }}>Avg Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestPricesData.map((item, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border-light)', backgroundColor: i % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)' }}>
                        <td style={{ padding: '12px 16px', fontWeight: 500 }}>{item["Product"]}</td>
                        <td style={{ padding: '12px 16px', color: 'var(--text-light)' }}>{item["Unit"]}</td>
                        <td style={{ padding: '12px 16px', color: 'var(--text-light)' }}>
                          {new Date(item["Date"]).toLocaleDateString()}
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right' }}>Rs. {item["Min Price"]?.toFixed(2) || '—'}</td>
                        <td style={{ padding: '12px 16px', textAlign: 'right' }}>Rs. {item["Max Price"]?.toFixed(2) || '—'}</td>
                        <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600, color: 'var(--accent-primary)' }}>
                          Rs. {item["Avg Price"]?.toFixed(2) || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}