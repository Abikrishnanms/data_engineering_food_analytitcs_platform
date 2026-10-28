import React from 'react';
import {
  Layers,
  HardDrive,
  FileSpreadsheet,
  FileCode2,
  Database,
  ShieldCheck,
  Server,
  Zap,
} from 'lucide-react';

export default function ArchitectureSection() {
  const tiers = [
    {
      id: 'bronze',
      title: 'Bronze Tier — Raw Storage',
      storage: 'Supabase Storage Bucket: foodflow-bronze',
      format: 'Raw CSV / gzip (for files > 45MB)',
      description:
        'Immutable raw data ingestion directly from production source dumps. Automatic transparent gzip compression bypasses 50MB payload limits.',
      metrics: '5 files · 16.44MB gz + 40MB raw',
      icon: HardDrive,
    },
    {
      id: 'silver',
      title: 'Silver Tier — Cleaned Parquet',
      storage: 'Supabase Storage Bucket: foodflow-silver',
      format: 'Apache Parquet (Snappy Compressed)',
      description:
        'Standardized column types, deduplicated records, and date parsing. Columnar format yields 73.1% storage reduction with high-speed random access.',
      metrics: '26.46 MB Parquet (vs 98.24 MB raw)',
      icon: FileSpreadsheet,
    },
    {
      id: 'gold',
      title: 'Gold Tier — Analytical Data Marts',
      storage: 'Supabase Storage Bucket: foodflow-gold',
      format: 'Pre-computed Parquet Marts (DuckDB)',
      description:
        'Business aggregate data marts built using in-process vectorized DuckDB. Contains kpi_daily.parquet, restaurant_monthly.parquet, and cuisine_performance.parquet.',
      metrics: 'DuckDB vectorized transformations',
      icon: FileCode2,
    },
    {
      id: 'database',
      title: 'Cloud Serving Tier — Supabase PostgreSQL',
      storage: 'PostgreSQL 17.6 on AWS Tokyo (ap-northeast-1)',
      format: 'Relational Schema + 14 B-Tree Indexes',
      description:
        'Loaded with 2,294,057 verified records. Serves analytical views (v_kpi_daily, v_kpi_monthly) and non-additive stored procedures (fn_kpi_summary, fn_top_restaurants).',
      metrics: '2,294,057 rows · 16/16 tests passing',
      icon: Database,
    },
  ];

  const contractRules = [
    {
      rule: 'Analytics Contract & Non-Additive Ratios',
      desc: 'Cancellation rates and Average Order Values (AOV) are mathematically non-additive. The backend forbids averaging daily rates; all window aggregations invoke fn_kpi_summary(start, end).',
    },
    {
      rule: 'Zero Raw Table Queries in Frontend',
      desc: 'All analytical metrics are exposed strictly through validated analytical views and parameterized stored functions. Raw transaction tables are never scanned directly.',
    },
    {
      rule: 'AST-Validated Safe NLQ Execution',
      desc: 'User queries in plain English pass through an Abstract Syntax Tree (AST) parser that enforces read-only operations, table allowlists, and execution statement timeouts.',
    },
    {
      rule: 'High Performance Columnar Lakehouse',
      desc: 'Data pipeline integrates DuckDB and PyArrow for ultra-fast Parquet transformations on cloud object storage, pairing cloud data lake efficiency with transactional relational guarantees.',
    },
  ];

  return (
    <div className="arch-container">
      {/* Title Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <Layers size={18} className="text-blue" />
              Medallion Cloud Lakehouse & Analytical Pipeline
            </h2>
            <p className="card-subtitle">
              Enterprise architecture pairing Supabase Storage Object Lake with Cloud PostgreSQL & FastAPI
            </p>
          </div>
          <span className="badge badge-blue">
            <Zap size={12} /> Active Cloud Pipeline
          </span>
        </div>

        <div className="card-body">
          {/* Lakehouse Tiers Grid */}
          <div className="tiers-grid">
            {tiers.map((t, idx) => {
              const IconComp = t.icon;
              return (
                <div key={t.id} className="tier-card">
                  <div className="tier-header">
                    <div className="tier-icon-wrap">
                      <IconComp size={18} className="tier-icon" />
                    </div>
                    <span className="tier-step">Step {idx + 1}</span>
                  </div>

                  <h3 className="tier-title">{t.title}</h3>
                  <div className="tier-storage">{t.storage}</div>
                  <p className="tier-desc">{t.desc || t.description}</p>

                  <div className="tier-footer">
                    <span className="badge badge-blue">{t.format}</span>
                    <span className="tier-metric">{t.metrics}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Analytics Contract & Security Card */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <ShieldCheck size={18} className="text-blue" />
              Analytics Governance & Data Integrity Standards
            </h2>
            <p className="card-subtitle">
              Guaranteed consistency, safety, and correctness across analytical layers
            </p>
          </div>
          <span className="badge badge-outline">16/16 Automated Tests Passed</span>
        </div>

        <div className="card-body">
          <div className="contracts-grid">
            {contractRules.map((c, idx) => (
              <div key={idx} className="contract-item">
                <div className="contract-bullet" />
                <div>
                  <h4 className="contract-title">{c.rule}</h4>
                  <p className="contract-desc">{c.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
