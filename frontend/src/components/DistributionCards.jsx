import React from 'react';
import { PieChart, CreditCard, Clock } from 'lucide-react';

function formatCurrency(amount) {
  if (!amount) return '₹0';
  return '₹' + Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

export default function DistributionCards({ cuisines, payments, hourly, loading }) {
  const cuisineList = cuisines || [];
  const paymentList = payments || [];
  const hourlyList = hourly || [];

  const totalCuisineRev = cuisineList.reduce((acc, c) => acc + Number(c.total_revenue || 0), 0) || 1;
  const totalPaymentOrders = paymentList.reduce((acc, p) => acc + Number(p.total_orders || 0), 0) || 1;
  const maxHourlyOrders = Math.max(...hourlyList.map((h) => Number(h.total_orders || 0)), 1);

  return (
    <div className="distributions-grid">
      {/* Cuisine Revenue Mix */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <PieChart size={18} className="text-blue" />
              Cuisine Revenue Share
            </h2>
            <p className="card-subtitle">
              Aggregate revenue contribution across cuisines (v_q07)
            </p>
          </div>
          <span className="badge badge-blue">Top 8</span>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="table-loading">Loading cuisine mix...</div>
          ) : (
            <div className="dist-list">
              {cuisineList.map((c, idx) => {
                const rev = Number(c.total_revenue || 0);
                const pct = (rev / totalCuisineRev) * 100;

                return (
                  <div key={c.cuisine || idx} className="dist-item">
                    <div className="dist-row">
                      <span className="dist-name">{c.cuisine}</span>
                      <div className="dist-nums">
                        <span className="dist-pct">{pct.toFixed(1)}%</span>
                        <span className="dist-val">{formatCurrency(rev)}</span>
                      </div>
                    </div>
                    <div className="dist-bar-track">
                      <div
                        className="dist-bar-fill"
                        style={{ width: `${pct}%`, opacity: 0.5 + (idx % 2 === 0 ? 0.5 : 0.25) }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Payment Methods Share */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <CreditCard size={18} className="text-blue" />
              Payment Methods
            </h2>
            <p className="card-subtitle">
              Transaction channel distribution (v_q08)
            </p>
          </div>
          <span className="badge badge-blue">All Channels</span>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="table-loading">Loading payment methods...</div>
          ) : (
            <div className="dist-list">
              {paymentList.map((p, idx) => {
                const ord = Number(p.total_orders || 0);
                const pct = (ord / totalPaymentOrders) * 100;

                return (
                  <div key={p.payment_method || idx} className="dist-item">
                    <div className="dist-row">
                      <span className="dist-name">{p.payment_method}</span>
                      <div className="dist-nums">
                        <span className="dist-pct">{pct.toFixed(1)}%</span>
                        <span className="dist-val">{ord.toLocaleString('en-IN')} orders</span>
                      </div>
                    </div>
                    <div className="dist-bar-track">
                      <div
                        className="dist-bar-fill"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 24-Hour Order Traffic */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <Clock size={18} className="text-blue" />
              24-Hour Traffic Pattern
            </h2>
            <p className="card-subtitle">
              Hourly volume based on order timestamp (v_q09)
            </p>
          </div>
          <span className="badge badge-blue">Hourly</span>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="table-loading">Loading hourly traffic...</div>
          ) : (
            <div className="hourly-bars-container">
              {hourlyList.map((h, idx) => {
                const ord = Number(h.total_orders || 0);
                const pct = (ord / maxHourlyOrders) * 100;
                const hourNum = Number(h.recorded_hour);
                const hourFormatted = `${hourNum.toString().padStart(2, '0')}:00`;

                return (
                  <div key={idx} className="hourly-col" title={`${hourFormatted} — ${ord.toLocaleString('en-IN')} orders`}>
                    <div className="hourly-bar-track">
                      <div
                        className="hourly-bar-fill"
                        style={{ height: `${pct}%` }}
                      />
                    </div>
                    <span className="hourly-label">
                      {hourNum % 4 === 0 ? hourFormatted : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
