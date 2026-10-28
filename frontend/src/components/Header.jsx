import React, { useState, useEffect } from 'react';
import { Database, Calendar, RefreshCw, BarChart3, MessageSquareText, Layers, ChevronDown } from 'lucide-react';

export default function Header({
  activeTab,
  setActiveTab,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  onRefresh,
  loading,
}) {
  // Infer active year from startDate
  const getInitialYear = () => {
    if (startDate === '2022-01-01' && endDate === '2025-12-31') return 'all';
    const yr = startDate.slice(0, 4);
    if (['2022', '2023', '2024', '2025'].includes(yr)) return yr;
    return '2025';
  };

  const [selectedYear, setSelectedYear] = useState(getInitialYear);

  // Sync year state when dates change externally
  useEffect(() => {
    if (startDate === '2022-01-01' && endDate === '2025-12-31') {
      setSelectedYear('all');
    } else {
      const yr = startDate.slice(0, 4);
      if (['2022', '2023', '2024', '2025'].includes(yr)) {
        setSelectedYear(yr);
      }
    }
  }, [startDate, endDate]);

  const years = ['2025', '2024', '2023', '2022', 'all'];

  // Dynamic presets based on selected year
  const getPresets = (yr) => {
    if (yr === 'all') {
      return [
        { label: 'All Time (2022–2025)', start: '2022-01-01', end: '2025-12-31' },
        { label: 'Year 2025', start: '2025-01-01', end: '2025-12-31' },
        { label: 'Year 2024', start: '2024-01-01', end: '2024-12-31' },
        { label: 'Year 2023', start: '2023-01-01', end: '2023-12-31' },
        { label: 'Year 2022', start: '2022-01-01', end: '2022-12-31' },
      ];
    }
    return [
      { label: `Full Year ${yr}`, start: `${yr}-01-01`, end: `${yr}-12-31` },
      { label: `Q1 (Jan–Mar)`, start: `${yr}-01-01`, end: `${yr}-03-31` },
      { label: `Q2 (Apr–Jun)`, start: `${yr}-04-01`, end: `${yr}-06-30` },
      { label: `Q3 (Jul–Sep)`, start: `${yr}-07-01`, end: `${yr}-09-30` },
      { label: `Q4 (Oct–Dec)`, start: `${yr}-10-01`, end: `${yr}-12-31` },
      { label: `May ${yr}`, start: `${yr}-05-01`, end: `${yr}-05-31` },
      { label: `June ${yr}`, start: `${yr}-06-01`, end: `${yr}-06-30` },
    ];
  };

  const handleYearChange = (newYear) => {
    setSelectedYear(newYear);
    let start, end;
    if (newYear === 'all') {
      start = '2022-01-01';
      end = '2025-12-31';
    } else {
      start = `${newYear}-01-01`;
      end = `${newYear}-12-31`;
    }
    setStartDate(start);
    setEndDate(end);
    onRefresh(start, end);
  };

  const handlePreset = (start, end) => {
    setStartDate(start);
    setEndDate(end);
    onRefresh(start, end);
  };

  const presets = getPresets(selectedYear);

  return (
    <header className="header-wrapper">
      {/* Top Bar */}
      <div className="header-top">
        <div className="brand-section">
          <div className="brand-icon-box">
            <BarChart3 size={22} className="brand-icon" />
          </div>
          <div>
            <div className="brand-title-row">
              <h1 className="brand-title">FoodFlow Analytics</h1>
              <span className="badge badge-blue">
                <span className="pulse-dot"></span> Supabase Cloud
              </span>
              <span className="badge badge-outline">2.29M Records</span>
            </div>
            <p className="brand-subtitle">
              Enterprise Food Delivery Intelligence &bull; Medallion Lakehouse &bull; Safe NLQ
            </p>
          </div>
        </div>

        {/* Global Navigation Tabs */}
        <nav className="tab-nav">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'tab-btn-active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <BarChart3 size={16} />
            <span>Executive Dashboard</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'nlq' ? 'tab-btn-active' : ''}`}
            onClick={() => setActiveTab('nlq')}
          >
            <MessageSquareText size={16} />
            <span>Ask FoodFlow (NLQ)</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'architecture' ? 'tab-btn-active' : ''}`}
            onClick={() => setActiveTab('architecture')}
          >
            <Layers size={16} />
            <span>Cloud Lakehouse</span>
          </button>
        </nav>
      </div>

      {/* Date Filter & Control Toolbar */}
      {activeTab === 'overview' && (
        <div className="filter-toolbar">
          {/* Year Selector Pills & Quick Presets */}
          <div className="presets-group">
            {/* Year Switcher */}
            <div className="year-selector-wrap">
              <span className="filter-label">
                <Calendar size={14} /> Year:
              </span>
              <div className="year-pill-group">
                {years.map((yr) => (
                  <button
                    key={yr}
                    className={`year-pill-btn ${selectedYear === yr ? 'year-pill-active' : ''}`}
                    onClick={() => handleYearChange(yr)}
                  >
                    {yr === 'all' ? 'All Years' : yr}
                  </button>
                ))}
              </div>
            </div>

            <div className="toolbar-divider" />

            {/* Quick Window Presets */}
            <div className="preset-chips">
              {presets.map((p) => {
                const isActive = startDate === p.start && endDate === p.end;
                return (
                  <button
                    key={p.label}
                    onClick={() => handlePreset(p.start, p.end)}
                    className={`preset-chip ${isActive ? 'preset-chip-active' : ''}`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Date Range Controls */}
          <div className="custom-dates-group">
            <div className="date-input-wrap">
              <label>From</label>
              <input
                type="date"
                className="input-date"
                value={startDate}
                min="2022-01-01"
                max="2025-12-31"
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="date-input-wrap">
              <label>To</label>
              <input
                type="date"
                className="input-date"
                value={endDate}
                min="2022-01-01"
                max="2025-12-31"
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <button
              className="btn btn-primary"
              onClick={() => onRefresh(startDate, endDate)}
              disabled={loading}
              title="Apply date range and query Supabase views"
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>{loading ? 'Refreshing...' : 'Update'}</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
