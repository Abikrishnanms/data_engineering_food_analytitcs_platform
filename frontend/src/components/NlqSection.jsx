import React, { useState } from 'react';
import {
  MessageSquareText,
  Send,
  Code2,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
  Database,
  Timer,
} from 'lucide-react';

export default function NlqSection() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showSql, setShowSql] = useState(true);
  const [copied, setCopied] = useState(false);

  const suggestedQueries = [
    'Top 5 restaurants in June 2025',
    'What is the average order value in 2025?',
    'Which cuisine generates the most revenue?',
    'Top 5 best selling menu items',
    'Total orders and revenue in May 2025',
    'How many orders were cancelled in 2025?',
  ];

  const handleQuery = async (qText) => {
    const q = qText || question;
    if (!q || !q.trim()) return;

    setQuestion(q);
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('/api/nlq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q.trim() }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }

      const json = await response.json();
      setResult(json);
    } catch (err) {
      setResult({
        status: 'error',
        answer: `Failed to execute query: ${err.message}`,
        sql: null,
        columns: [],
        data: [],
        duration_ms: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopySql = () => {
    if (result && result.sql) {
      navigator.clipboard.writeText(result.sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatCellValue = (val, colName) => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'number') {
      const lower = colName.toLowerCase();

      // 1. Ranks, IDs, and positions: NEVER display as currency
      if (
        lower.includes('rank') ||
        lower.endsWith('_id') ||
        lower === 'id' ||
        lower.includes('position') ||
        lower.includes('row_num')
      ) {
        return String(val);
      }

      // 2. Percentage and rate columns
      if (
        lower.includes('rate') ||
        lower.includes('percentage') ||
        lower.includes('pct') ||
        lower.includes('ratio')
      ) {
        return (val * 100).toFixed(2) + '%';
      }

      // 3. Monetary / Currency columns (Revenue, Price, AOV, Spend, Sales, Amount)
      // Must NOT be a rank or count
      if (
        (lower.includes('revenue') ||
          lower.includes('aov') ||
          lower.includes('price') ||
          lower.includes('amount') ||
          lower.includes('sales') ||
          lower.includes('spend') ||
          lower.includes('cost') ||
          lower.includes('avg_order_value')) &&
        !lower.includes('rank') &&
        !lower.includes('count') &&
        !lower.includes('orders')
      ) {
        return '₹' + val.toLocaleString('en-IN', { maximumFractionDigits: 2 });
      }

      // 4. Counts, units, volume
      return val.toLocaleString('en-IN');
    }
    return String(val);
  };


  return (
    <div className="nlq-container">
      {/* Intro Header Card */}
      <div className="card nlq-hero-card">
        <div className="card-header">
          <div>
            <h2 className="card-title">
              <Sparkles size={18} className="text-blue" />
              Ask FoodFlow — Natural Language Intelligence
            </h2>
            <p className="card-subtitle">
              Ask any business question in plain English. The rule-based AST engine compiles safe, read-only SQL and executes it directly against Supabase Cloud PostgreSQL.
            </p>
          </div>
          <span className="badge badge-blue">
            <Database size={12} /> Supabase PostgreSQL
          </span>
        </div>

        <div className="card-body">
          {/* Query Input Box */}
          <form
            className="nlq-input-form"
            onSubmit={(e) => {
              e.preventDefault();
              handleQuery();
            }}
          >
            <div className="nlq-input-wrap">
              <MessageSquareText size={18} className="nlq-input-icon" />
              <input
                type="text"
                className="nlq-text-input"
                placeholder="Ask a question (e.g., 'Top 3 restaurants in June 2025' or 'Which cuisine makes the most money?')"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="btn btn-primary nlq-submit-btn"
                disabled={loading || !question.trim()}
              >
                <Send size={15} />
                <span>{loading ? 'Compiling...' : 'Ask'}</span>
              </button>
            </div>
          </form>

          {/* Quick Suggested Chips */}
          <div className="nlq-suggestions">
            <span className="nlq-suggestions-label">Try asking:</span>
            <div className="nlq-chips-row">
              {suggestedQueries.map((prompt, idx) => (
                <button
                  key={idx}
                  className="nlq-chip"
                  onClick={() => handleQuery(prompt)}
                  disabled={loading}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Query Loading State */}
      {loading && (
        <div className="card nlq-loading-card">
          <div className="pulse-dot"></div>
          <span>Parsing intent &bull; Validating read-only AST &bull; Querying Supabase Cloud...</span>
        </div>
      )}

      {/* Query Results Display */}
      {result && !loading && (
        <div className="nlq-results-wrapper">
          {/* Answer Status Banner */}
          <div className="card nlq-answer-card">
            <div className="nlq-answer-header">
              <div className="nlq-answer-title-group">
                {result.status === 'ok' ? (
                  <CheckCircle2 size={18} className="text-blue" />
                ) : (
                  <AlertCircle size={18} className="text-blue" />
                )}
                <span className="nlq-answer-text">{result.answer}</span>
              </div>

              <div className="nlq-meta-badges">
                {result.duration_ms !== undefined && (
                  <span className="badge badge-outline">
                    <Timer size={12} /> {result.duration_ms} ms
                  </span>
                )}
                <span className="badge badge-blue">
                  {result.data?.length || 0} Record(s)
                </span>
                {result.sql && (
                  <button
                    className="btn btn-subtle btn-sm"
                    onClick={() => setShowSql(!showSql)}
                  >
                    <Code2 size={13} />
                    <span>{showSql ? 'Hide SQL' : 'View SQL'}</span>
                  </button>
                )}
              </div>
            </div>

            {/* Generated SQL Viewer */}
            {result.sql && showSql && (
              <div className="nlq-sql-box">
                <div className="nlq-sql-header">
                  <span className="nlq-sql-title">
                    <Code2 size={13} /> Safe Read-Only SQL Query (AST Validated)
                  </span>
                  <button
                    className="btn-copy-sql"
                    onClick={handleCopySql}
                    title="Copy SQL to clipboard"
                  >
                    {copied ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <pre className="nlq-sql-code">
                  <code>{result.sql}</code>
                </pre>
              </div>
            )}
          </div>

          {/* Results Table */}
          {result.data && result.data.length > 0 && (
            <div className="card nlq-table-card">
              <div className="card-header">
                <h3 className="card-title">
                  <Database size={16} className="text-blue" /> Query Output Records
                </h3>
                <span className="badge badge-outline">
                  {result.data.length} row{result.data.length > 1 ? 's' : ''} returned
                </span>
              </div>

              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {result.columns.map((col, idx) => (
                        <th key={idx}>
                          {col.replace(/_/g, ' ').toUpperCase()}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.map((row, rIdx) => (
                      <tr key={rIdx}>
                        {result.columns.map((col, cIdx) => (
                          <td
                            key={cIdx}
                            className={
                              typeof row[col] === 'number' && !col.toLowerCase().includes('rank')
                                ? 'text-right'
                                : col.toLowerCase().includes('rank')
                                ? 'text-center font-semibold'
                                : ''
                            }
                          >
                            {formatCellValue(row[col], col)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
