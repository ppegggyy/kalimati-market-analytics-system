// src/api.js
// All communication with the FastAPI backend goes through this file.
// The Vite proxy in vite.config.js forwards /api → http://localhost:8000/api

const BASE = '/api/v1';

// ── Products ────────────────────────────────────────────────────────────────
// Returns: string[]  e.g. ["Bittergourd", "Broccoli", ..., "Yam"]

export async function fetchProducts() {
  const res = await fetch(`${BASE}/prices/products`);
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

// ── Price history with moving average ───────────────────────────────────────
// Returns: [{ Date, Product, Unit, "Max Price", "Min Price", "Avg Price",
//             moving_avg_7d }, ...]

export async function fetchMovingAverage(
  product,
  window = 7,
  startDate = null,
  endDate = null
) {
  const params = new URLSearchParams({ product, window });
  if (startDate) params.append('start_date', startDate);
  if (endDate)   params.append('end_date',   endDate);
  const res = await fetch(`${BASE}/analytics/moving-average?${params}`);
  if (!res.ok) throw new Error('Failed to fetch moving average');
  return res.json();
}

// ── Volatility for one product ──────────────────────────────────────────────
// Returns: { product, unit, start_date, end_date,
//            std_dev_avg_price, record_count }

export async function fetchVolatility(
  product,
  startDate = null,
  endDate = null
) {
  const params = new URLSearchParams({ product });
  if (startDate) params.append('start_date', startDate);
  if (endDate)   params.append('end_date',   endDate);
  const res = await fetch(`${BASE}/analytics/volatility?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch volatility for ${product}`);
  return res.json();
}

// ── Trend summary ───────────────────────────────────────────────────────────
// Returns: { overall_change_pct, highest_price, lowest_price,
//            mean_price, volatility }

export async function fetchTrend(product, startDate = null, endDate = null) {
  const params = new URLSearchParams({ product });
  if (startDate) params.append('start_date', startDate);
  if (endDate)   params.append('end_date',   endDate);
  const res = await fetch(`${BASE}/analytics/trend?${params}`);
  if (!res.ok) throw new Error('Failed to fetch trend');
  return res.json();
}

// ── Latest prices for all products ─────────────────────────────────────────
// Returns: PriceRecord[]  (one entry per product, most recent date)

export async function fetchLatestPrices() {
  const res = await fetch(`${BASE}/prices/latest`);
  if (!res.ok) throw new Error('Failed to fetch latest prices');
  return res.json();
}

// ── ARIMA forecast ──────────────────────────────────────────────────────────
// Returns: { product, model_used,
//            forecast: [{ record_date, predicted_avg_price,
//                         lower_bound, upper_bound }] }

export async function fetchForecast(product, steps = 30) {
  const res = await fetch(`${BASE}/analytics/forecast`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ product, steps }),
  });
  if (!res.ok) throw new Error('Failed to fetch forecast');
  return res.json();
}