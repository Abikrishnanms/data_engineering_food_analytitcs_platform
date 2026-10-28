import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import KpiCards from './components/KpiCards';
import DailyTrendChart from './components/DailyTrendChart';
import TopRankings from './components/TopRankings';
import DistributionCards from './components/DistributionCards';
import NlqSection from './components/NlqSection';
import ArchitectureSection from './components/ArchitectureSection';
import Footer from './components/Footer';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'nlq' | 'architecture'
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-12-31');

  // Analytical State
  const [kpis, setKpis] = useState(null);
  const [dailyTrends, setDailyTrends] = useState([]);
  const [topRestaurants, setTopRestaurants] = useState([]);
  const [topItems, setTopItems] = useState([]);
  const [cuisines, setCuisines] = useState([]);
  const [payments, setPayments] = useState([]);
  const [hourly, setHourly] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all analytical data
  const fetchData = useCallback(async (start = startDate, end = endDate) => {
    setLoading(true);
    setError(null);

    try {
      const [
        kpiRes,
        trendsRes,
        restaurantsRes,
        itemsRes,
        cuisinesRes,
        paymentsRes,
        hourlyRes,
      ] = await Promise.all([
        fetch(`/api/kpis?start_date=${start}&end_date=${end}`),
        fetch(`/api/trends/daily?start_date=${start}&end_date=${end}`),
        fetch(`/api/restaurants/top?start_date=${start}&end_date=${end}&limit=5`),
        fetch(`/api/menu/top?start_date=${start}&end_date=${end}&limit=8`),
        fetch('/api/cuisines/mix'),
        fetch('/api/payments/mix'),
        fetch('/api/hourly'),
      ]);

      if (kpiRes.ok) setKpis(await kpiRes.json());
      if (trendsRes.ok) setDailyTrends(await trendsRes.json());
      if (restaurantsRes.ok) setTopRestaurants(await restaurantsRes.json());
      if (itemsRes.ok) setTopItems(await itemsRes.json());
      if (cuisinesRes.ok) setCuisines(await cuisinesRes.json());
      if (paymentsRes.ok) setPayments(await paymentsRes.json());
      if (hourlyRes.ok) setHourly(await hourlyRes.json());
    } catch (err) {
      console.error('Failed to load analytical metrics:', err);
      setError('Unable to connect to FastAPI backend on port 8000.');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="app-container">
      {/* Top Header & Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        startDate={startDate}
        setStartDate={setStartDate}
        endDate={endDate}
        setEndDate={setEndDate}
        onRefresh={(s, e) => fetchData(s, e)}
        loading={loading}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {error && (
          <div className="card" style={{ marginBottom: 20, borderColor: '#bfdbfe', backgroundColor: '#eff6ff', padding: '14px 20px' }}>
            <span style={{ color: '#1e3a8a', fontWeight: 500, fontSize: 13 }}>
              Notice: {error} Make sure the FastAPI service is running (`uvicorn backend.main:app --port 8000`).
            </span>
          </div>
        )}

        {/* Tab 1: Executive Dashboard Overview */}
        {activeTab === 'overview' && (
          <>
            {/* KPI Summary Cards (8-grid) */}
            <KpiCards kpis={kpis} loading={loading} />

            {/* Daily Operational Trends SVG Area Chart */}
            <DailyTrendChart dailyData={dailyTrends} loading={loading} />

            {/* Top Partner Restaurants & Menu Items */}
            <TopRankings
              restaurants={topRestaurants}
              items={topItems}
              loading={loading}
            />

            {/* Cuisine, Payment, & Hourly Distributions */}
            <DistributionCards
              cuisines={cuisines}
              payments={payments}
              hourly={hourly}
              loading={loading}
            />
          </>
        )}

        {/* Tab 2: Natural Language Query (NLQ) */}
        {activeTab === 'nlq' && <NlqSection />}

        {/* Tab 3: Cloud Lakehouse Architecture */}
        {activeTab === 'architecture' && <ArchitectureSection />}
      </main>

      {/* Enterprise Footer */}
      <Footer />
    </div>
  );
}
