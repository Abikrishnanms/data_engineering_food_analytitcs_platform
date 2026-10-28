import React, { useState, useMemo } from 'react';
import { TrendingUp, BarChart2, IndianRupee, Calendar } from 'lucide-react';

export default function DailyTrendChart({ dailyData, loading }) {
  const [metricMode, setMetricMode] = useState('orders'); // 'orders' | 'revenue'
  const [hoverIndex, setHoverIndex] = useState(null);

  const series = dailyData || [];

  // Computed summary metrics
  const summary = useMemo(() => {
    if (!series.length) return null;
    let maxOrders = 0;
    let maxOrderDate = '';
    let totalRev = 0;
    let totalOrd = 0;

    series.forEach((d) => {
      const orders = Number(d.total_orders || 0);
      const rev = Number(d.qualifying_revenue || 0);
      totalOrd += orders;
      totalRev += rev;
      if (orders > maxOrders) {
        maxOrders = orders;
        maxOrderDate = d.order_date;
      }
    });

    const avgOrders = Math.round(totalOrd / series.length);
    return {
      peakOrders: maxOrders,
      peakDate: maxOrderDate,
      totalOrders: totalOrd,
      totalRevenue: totalRev,
      avgDailyOrders: avgOrders,
    };
  }, [series]);

  // Chart Dimensions & Scales
  const width = 1000;
  const height = 280;
  const padding = { top: 30, right: 30, bottom: 40, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const points = useMemo(() => {
    if (!series.length) return [];

    const values = series.map((d) =>
      metricMode === 'orders'
        ? Number(d.total_orders || 0)
        : Number(d.qualifying_revenue || 0)
    );

    const minVal = 0;
    const maxVal = Math.max(...values, 1) * 1.1; // 10% headroom

    return series.map((d, i) => {
      const val =
        metricMode === 'orders'
          ? Number(d.total_orders || 0)
          : Number(d.qualifying_revenue || 0);
      const x = padding.left + (i / Math.max(series.length - 1, 1)) * chartWidth;
      const y = padding.top + chartHeight - (val / maxVal) * chartHeight;
      return { x, y, val, raw: d };
    });
  }, [series, metricMode, chartWidth, chartHeight, padding.left, padding.top]);

  // Generate SVG Path
  const { linePath, areaPath } = useMemo(() => {
    if (points.length === 0) return { linePath: '', areaPath: '' };

    let line = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      // Smooth cubic bezier or straight lines
      line += ` L ${points[i].x} ${points[i].y}`;
    }

    const area = `${line} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`;

    return { linePath: line, areaPath: area };
  }, [points, chartHeight, padding.top]);

  // Sampled X-axis labels
  const xLabels = useMemo(() => {
    if (!series.length) return [];
    const step = Math.ceil(series.length / 7);
    return series
      .map((d, i) => ({ date: d.order_date, index: i }))
      .filter((_, i) => i % step === 0 || i === series.length - 1);
  }, [series]);

  const activePoint = hoverIndex !== null && points[hoverIndex] ? points[hoverIndex] : null;

  return (
    <div className="card chart-card">
      <div className="card-header chart-header-row">
        <div>
          <h2 className="card-title">
            <TrendingUp size={18} className="text-blue" />
            Daily Operational Trends
          </h2>
          <p className="card-subtitle">
            Time series tracking daily volume & qualifying revenue from v_kpi_daily
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="chart-mode-toggle">
          <button
            className={`btn-toggle ${metricMode === 'orders' ? 'btn-toggle-active' : ''}`}
            onClick={() => setMetricMode('orders')}
          >
            <BarChart2 size={13} /> Order Volume
          </button>
          <button
            className={`btn-toggle ${metricMode === 'revenue' ? 'btn-toggle-active' : ''}`}
            onClick={() => setMetricMode('revenue')}
          >
            <IndianRupee size={13} /> Revenue (₹)
          </button>
        </div>
      </div>

      {/* Summary Stat Highlights */}
      {summary && (
        <div className="chart-summary-bar">
          <div className="summary-item">
            <span className="summary-label">Average Daily Volume</span>
            <span className="summary-value">
              {summary.avgDailyOrders.toLocaleString('en-IN')} orders/day
            </span>
          </div>
          <div className="summary-divider" />
          <div className="summary-item">
            <span className="summary-label">Peak Volume Date</span>
            <span className="summary-value">
              {summary.peakDate} ({summary.peakOrders.toLocaleString('en-IN')} orders)
            </span>
          </div>
          <div className="summary-divider" />
          <div className="summary-item">
            <span className="summary-label">Period Active Days</span>
            <span className="summary-value">{series.length} Calendar Days</span>
          </div>
        </div>
      )}

      {/* SVG Chart Area */}
      <div className="svg-chart-container">
        {loading ? (
          <div className="chart-loading">
            <div className="pulse-dot"></div>
            <span>Loading time series from Supabase PostgreSQL...</span>
          </div>
        ) : series.length === 0 ? (
          <div className="chart-empty">No trend data found for selected period.</div>
        ) : (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            className="trend-svg"
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0.01" />
              </linearGradient>
            </defs>

            {/* Gridlines */}
            {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
              const y = padding.top + chartHeight * pct;
              return (
                <line
                  key={idx}
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />
              );
            })}

            {/* Area Fill */}
            <path d={areaPath} fill="url(#blueGradient)" />

            {/* Main Trend Line */}
            <path
              d={linePath}
              fill="none"
              stroke="#2563eb"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Interactive hover line and cursor */}
            {activePoint && (
              <g>
                <line
                  x1={activePoint.x}
                  y1={padding.top}
                  x2={activePoint.x}
                  y2={padding.top + chartHeight}
                  stroke="#1d4ed8"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />
                <circle
                  cx={activePoint.x}
                  cy={activePoint.y}
                  r="5"
                  fill="#ffffff"
                  stroke="#1d4ed8"
                  strokeWidth="3"
                />
              </g>
            )}

            {/* Invisible hover zones */}
            {points.map((p, idx) => {
              const stepW = chartWidth / points.length;
              return (
                <rect
                  key={idx}
                  x={p.x - stepW / 2}
                  y={padding.top}
                  width={stepW}
                  height={chartHeight}
                  fill="transparent"
                  onMouseEnter={() => setHoverIndex(idx)}
                  style={{ cursor: 'crosshair' }}
                />
              );
            })}

            {/* X-axis labels */}
            {xLabels.map((item, idx) => {
              const pt = points[item.index];
              if (!pt) return null;
              return (
                <text
                  key={idx}
                  x={pt.x}
                  y={height - 12}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#64748b"
                  fontFamily="Inter, sans-serif"
                >
                  {item.date.slice(5)}
                </text>
              );
            })}
          </svg>
        )}

        {/* Hover Tooltip Overlay */}
        {activePoint && (
          <div
            className="chart-tooltip"
            style={{
              left: `${(activePoint.x / width) * 100}%`,
              top: '40px',
            }}
          >
            <div className="tooltip-date">
              <Calendar size={11} /> {activePoint.raw.order_date}
            </div>
            <div className="tooltip-row">
              <span>Orders:</span>
              <strong>{Number(activePoint.raw.total_orders).toLocaleString('en-IN')}</strong>
            </div>
            <div className="tooltip-row">
              <span>Revenue:</span>
              <strong>
                ₹{Number(activePoint.raw.qualifying_revenue).toLocaleString('en-IN', {
                  maximumFractionDigits: 0,
                })}
              </strong>
            </div>
            <div className="tooltip-row">
              <span>Cancellation:</span>
              <strong>{(Number(activePoint.raw.cancellation_rate) * 100).toFixed(1)}%</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
