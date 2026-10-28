import React from 'react';
import {
  ShoppingBag,
  CheckCircle2,
  XCircle,
  Percent,
  IndianRupee,
  TrendingUp,
  Store,
  Users,
} from 'lucide-react';

function formatCurrency(amount) {
  if (amount === undefined || amount === null) return '₹0';
  const num = Number(amount);
  return '₹' + num.toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 0 });
}

function formatNumber(num) {
  if (num === undefined || num === null) return '0';
  return Number(num).toLocaleString('en-IN');
}

export default function KpiCards({ kpis, loading }) {
  const data = kpis || {};

  const cards = [
    {
      id: 'gross_orders',
      title: 'Gross Orders',
      value: formatNumber(data.total_orders),
      subtext: 'Total placed in period',
      icon: ShoppingBag,
    },
    {
      id: 'delivered_orders',
      title: 'Delivered Orders',
      value: formatNumber(data.qualifying_orders),
      subtext: 'Revenue-qualifying',
      icon: CheckCircle2,
    },
    {
      id: 'cancelled_orders',
      title: 'Cancelled Orders',
      value: formatNumber(data.cancelled_orders),
      subtext: 'Zero revenue impact',
      icon: XCircle,
    },
    {
      id: 'cancellation_rate',
      title: 'Cancellation Rate',
      value: data.cancellation_rate !== undefined ? `${(Number(data.cancellation_rate) * 100).toFixed(2)}%` : '0.00%',
      subtext: 'Non-additive ratio metric',
      icon: Percent,
      progress: data.cancellation_rate ? Number(data.cancellation_rate) * 100 : 0,
    },
    {
      id: 'qualifying_revenue',
      title: 'Qualifying Revenue',
      value: formatCurrency(data.qualifying_revenue),
      subtext: 'Analytics Contract compliant',
      icon: IndianRupee,
    },
    {
      id: 'avg_order_value',
      title: 'Avg Order Value (AOV)',
      value: formatCurrency(data.avg_order_value),
      subtext: 'Revenue per delivered order',
      icon: TrendingUp,
    },
    {
      id: 'active_restaurants',
      title: 'Active Restaurants',
      value: formatNumber(data.active_restaurants),
      subtext: 'Fulfilling partner venues',
      icon: Store,
    },
    {
      id: 'active_customers',
      title: 'Active Customers',
      value: formatNumber(data.active_customers),
      subtext: 'Ordering consumer base',
      icon: Users,
    },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((card) => {
        const IconComponent = card.icon;
        return (
          <div key={card.id} className="kpi-card">
            <div className="kpi-header">
              <span className="kpi-title">{card.title}</span>
              <div className="kpi-icon-wrap">
                <IconComponent size={18} className="kpi-icon" />
              </div>
            </div>

            <div className="kpi-value-row">
              <span className={`kpi-value ${loading ? 'kpi-loading' : ''}`}>
                {loading ? '—' : card.value}
              </span>
            </div>

            <div className="kpi-footer">
              <span className="kpi-subtext">{card.subtext}</span>
            </div>

            {card.progress !== undefined && (
              <div className="kpi-progress-track">
                <div
                  className="kpi-progress-bar"
                  style={{ width: `${Math.min(card.progress * 5, 100)}%` }}
                  title={`${card.progress.toFixed(2)}%`}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
