import React from 'react';
import { Store, UtensilsCrossed, Award, MapPin } from 'lucide-react';

function formatCurrency(amount) {
  if (!amount) return '₹0';
  return '₹' + Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

export default function TopRankings({ restaurants, items, loading }) {
  const topRestaurants = restaurants || [];
  const topItems = items || [];

  const maxRestRevenue = Math.max(...topRestaurants.map((r) => Number(r.qualifying_revenue || 0)), 1);
  const maxItemUnits = Math.max(...topItems.map((i) => Number(i.units_sold || 0)), 1);

  return (
    <div className="rankings-grid">
      {/* Top Restaurants Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <Store size={18} className="text-blue" />
              Top Grossing Restaurants
            </h2>
            <p className="card-subtitle">
              Ranked by qualifying revenue via fn_top_restaurants
            </p>
          </div>
          <span className="badge badge-blue">Top 5</span>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="table-loading">Loading top partners...</div>
          ) : topRestaurants.length === 0 ? (
            <div className="table-empty">No restaurant data for selected period.</div>
          ) : (
            <div className="rankings-list">
              {topRestaurants.map((rest, idx) => {
                const rev = Number(rest.qualifying_revenue || 0);
                const percent = (rev / maxRestRevenue) * 100;
                const rank = rest.revenue_rank || idx + 1;

                return (
                  <div key={rest.restaurant_id || idx} className="ranking-item">
                    <div className="ranking-rank-box">
                      <span className={`rank-badge ${rank <= 3 ? 'rank-badge-top' : ''}`}>
                        #{rank}
                      </span>
                    </div>

                    <div className="ranking-details">
                      <div className="ranking-main-row">
                        <span className="ranking-name" title={rest.restaurant_name}>
                          {rest.restaurant_name}
                        </span>
                        <span className="ranking-value">{formatCurrency(rev)}</span>
                      </div>

                      <div className="ranking-meta-row">
                        <span className="ranking-tag">
                          <MapPin size={11} /> {rest.city}
                        </span>
                        <span className="ranking-tag ranking-tag-cuisine">
                          {rest.cuisine}
                        </span>
                        <span className="ranking-tag">
                          {rest.qualifying_orders} orders
                        </span>
                      </div>

                      <div className="ranking-bar-track">
                        <div
                          className="ranking-bar-fill"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Top Menu Items Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <UtensilsCrossed size={18} className="text-blue" />
              Best-Selling Menu Items
            </h2>
            <p className="card-subtitle">
              Ranked by volume from v_q03_item_monthly_performance
            </p>
          </div>
          <span className="badge badge-blue">Top 8</span>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="table-loading">Loading top items...</div>
          ) : topItems.length === 0 ? (
            <div className="table-empty">No item data for selected period.</div>
          ) : (
            <div className="rankings-list">
              {topItems.map((item, idx) => {
                const units = Number(item.units_sold || 0);
                const percent = (units / maxItemUnits) * 100;
                const rank = idx + 1;

                return (
                  <div key={item.menu_id || idx} className="ranking-item">
                    <div className="ranking-rank-box">
                      <span className={`rank-badge ${rank <= 3 ? 'rank-badge-top' : ''}`}>
                        #{rank}
                      </span>
                    </div>

                    <div className="ranking-details">
                      <div className="ranking-main-row">
                        <span className="ranking-name" title={item.item_name}>
                          {item.item_name}
                        </span>
                        <span className="ranking-value">{units.toLocaleString('en-IN')} units</span>
                      </div>

                      <div className="ranking-meta-row">
                        <span className="ranking-tag ranking-tag-category">
                          {item.category}
                        </span>
                        <span className="ranking-tag" title={item.restaurant_name}>
                          {item.restaurant_name}
                        </span>
                        <span className="ranking-tag">
                          {formatCurrency(item.qualifying_revenue)}
                        </span>
                      </div>

                      <div className="ranking-bar-track">
                        <div
                          className="ranking-bar-fill"
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
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
