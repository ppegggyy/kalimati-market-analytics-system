// src/pages/Dashboard.jsx
import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, ComposedChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts';
import { Activity, TrendingUp, Banknote, AlertCircle, Calendar, Download } from 'lucide-react';
import { fetchProducts, fetchMovingAverage, fetchTrend, fetchLatestPrices } from '../api';
import { useBreakpoint } from '../hooks/useMediaQuery';
import { getChartMargin, getYAxisWidth, getAxisFontSize } from '../utils/chartHelpers';
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
  const { isMobile, isTablet } = useBreakpoint();
  const chartMargin = getChartMargin(isMobile, isTablet);
  const yAxisWidth = getYAxisWidth(isMobile, isTablet);
  const axisFontSize = getAxisFontSize(isMobile, isTablet);

  // Lazy initializer functions — only run once on mount, not every render
  const getInitialStartDate = () => {
    const d = new Date();
    d.setMonth(d.getMonth() - 6);
    return d.toISOString().split('T')[0];
  };

  const getInitialEndDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [compareProduct, setCompareProduct] = useState('');
  const [startDate, setStartDate] = useState(getInitialStartDate);
  const [endDate, setEndDate] = useState(getInitialEndDate);
  
  const [chartData, setChartData] = useState([]);
  const [rawMaData, setRawMaData] = useState([]);
  const [trend, setTrend] = useState(null);

  // Memoize expensive derived data — only recompute when raw data changes
  const seasonalData = useMemo(() => calculateAdvancedSeasonality(rawMaData), [rawMaData]);
  const shiftData = useMemo(() => calculateShiftDistribution(rawMaData), [rawMaData]);
  const compareProductOptions = useMemo(() => products.filter(p => p !== selectedProduct), [products, selectedProduct]);
  const recentChartData = useMemo(() => chartData.slice(-14), [chartData]);
  
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

    const fetches = [
      fetchMovingAverage(selectedProduct, 7, startDate, endDate),
      fetchTrend(selectedProduct, startDate, endDate),
    ];

    if (compareProduct) {
      fetches.push(fetchMovingAverage(compareProduct, 7, startDate, endDate));
    }

    Promise.all(fetches)
      .then(([maData, trendData, compareMaData]) => {
        let mergedData = maData.map((row) => ({
          date: row['Date'],
          price: row['Avg Price'],
          movingAvg: row['moving_avg_7d'] ?? null,
        }));

        if (compareProduct && compareMaData) {
          // Map compare data by date for merging
          const compareMap = new Map(compareMaData.map(r => [r['Date'], r]));
          mergedData = mergedData.map(row => {
            const match = compareMap.get(row.date);
            return {
              ...row,
              comparePrice: match ? match['Avg Price'] : null,
              compareMovingAvg: match ? match['moving_avg_7d'] : null,
            };
          });
        }

        setChartData(mergedData);
        setRawMaData(maData);
        setTrend(trendData);
      })
      .catch(() => setError('Failed to load chart data. Check backend logs.'))
      .finally(() => setLoading(false));
  }, [selectedProduct, compareProduct, startDate, endDate]);

  const handleDownloadCSV = () => {
    if (chartData.length === 0) return;
    
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Headers
    if (compareProduct) {
      csvContent += `Date,${selectedProduct} Actual Price,${selectedProduct} 7-Day MA,${compareProduct} Actual Price,${compareProduct} 7-Day MA\n`;
    } else {
      csvContent += `Date,Product,Actual Price,7-Day MA\n`;
    }
    
    // Rows
    chartData.forEach(row => {
      const date = row.date;
      const p1 = row.price !== null ? row.price : '';
      const ma1 = row.movingAvg !== null ? row.movingAvg : '';
      
      if (compareProduct) {
        const p2 = row.comparePrice !== null && row.comparePrice !== undefined ? row.comparePrice : '';
        const ma2 = row.compareMovingAvg !== null && row.compareMovingAvg !== undefined ? row.compareMovingAvg : '';
        csvContent += `${date},${p1},${ma1},${p2},${ma2}\n`;
      } else {
        csvContent += `${date},${selectedProduct},${p1},${ma1}\n`;
      }
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `market_analysis_${startDate}_to_${endDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

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
          <label htmlFor="compare-product">Compare With (Optional)</label>
          <select
            id="compare-product"
            value={compareProduct}
            onChange={(e) => setCompareProduct(e.target.value)}
            className="input-select"
          >
            <option value="">None</option>
            {compareProductOptions.map((p) => <option key={`comp-${p}`} value={p}>{p}</option>)}
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
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input-date"
              style={{ flex: 1 }}
            />
            <button 
              onClick={handleDownloadCSV} 
              className="btn-outline" 
              title="Download CSV"
              style={{ padding: '0.6rem', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '12px', border: '1px solid var(--border-dark)', backgroundColor: 'var(--bg-app)', cursor: 'pointer', height: '45px', width: '45px', color: 'var(--text-main)', flexShrink: 0 }}
            >
              <Download size={20} />
            </button>
          </div>
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
                <AreaChart data={chartData} margin={chartMargin}>
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
                    fontSize={axisFontSize} 
                    tickLine={false} 
                    axisLine={false}
                    minTickGap={isMobile ? 24 : 40}
                  />
                  <YAxis 
                    stroke="var(--text-light)" 
                    fontSize={axisFontSize} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(val) => `Rs ${val}`}
                    width={yAxisWidth}
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
                    name={selectedProduct || "Actual Price"}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="movingAvg" 
                    stroke="var(--accent-info)" 
                    strokeWidth={2} 
                    strokeDasharray="6 4" 
                    dot={false}
                    name={`${selectedProduct} 7-Day MA`}
                  />
                  {compareProduct && <Line type="monotone" dataKey="comparePrice" stroke="var(--accent-warning)" strokeWidth={2.5} dot={false} name={compareProduct} />}
                  {compareProduct && <Line type="monotone" dataKey="compareMovingAvg" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="6 4" dot={false} name={`${compareProduct} 7-Day MA`} />}
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
                  <ComposedChart data={seasonalData} margin={chartMargin}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis dataKey="month" stroke="var(--text-light)" fontSize={axisFontSize} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-light)" fontSize={axisFontSize} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={yAxisWidth} />
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
                  <BarChart data={seasonalData} margin={chartMargin}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis dataKey="month" stroke="var(--text-light)" fontSize={axisFontSize} tickLine={false} axisLine={false} />
                    <YAxis stroke="var(--text-light)" fontSize={axisFontSize} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={yAxisWidth} />
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
                      innerRadius={isMobile ? '48%' : '55%'}
                      outerRadius={isMobile ? '68%' : '78%'}
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
                    <Legend verticalAlign="bottom" height={isMobile ? 48 : 36} iconType="circle" wrapperStyle={{ fontSize: isMobile ? 11 : 12 }} />
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
                  <BarChart data={recentChartData} margin={chartMargin}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                    <XAxis 
                      dataKey="date" 
                      stroke="var(--text-light)" 
                      fontSize={axisFontSize} 
                      tickLine={false} 
                      axisLine={false}
                      minTickGap={isMobile ? 8 : 16}
                      tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis stroke="var(--text-light)" fontSize={axisFontSize} tickLine={false} axisLine={false} tickFormatter={(val) => `Rs ${val}`} width={yAxisWidth} />
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
              <div className="data-grid-container data-grid-scroll">
                <table className="data-grid">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th className="col-hide-mobile">Unit</th>
                      <th className="col-hide-tablet">Latest Date</th>
                      <th className="col-hide-mobile" style={{ textAlign: 'right' }}>Min Price</th>
                      <th className="col-hide-mobile" style={{ textAlign: 'right' }}>Max Price</th>
                      <th style={{ textAlign: 'right' }}>Avg Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {latestPricesData.map((item, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 600 }}>{item["Product"]}</td>
                        <td className="col-hide-mobile">{item["Unit"]}</td>
                        <td className="col-hide-tablet">
                          {new Date(item["Date"]).toLocaleDateString()}
                        </td>
                        <td className="col-hide-mobile" style={{ textAlign: 'right' }}>Rs. {item["Min Price"]?.toFixed(2) || '—'}</td>
                        <td className="col-hide-mobile" style={{ textAlign: 'right' }}>Rs. {item["Max Price"]?.toFixed(2) || '—'}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--accent-primary)' }}>
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