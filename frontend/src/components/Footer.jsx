import React from 'react';
import { Database, ShieldCheck, Cpu } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="footer-wrapper">
      <div className="footer-content">
        <div className="footer-left">
          <span className="footer-brand">FoodFlow Analytics Enterprise</span>
          <span className="footer-divider">&bull;</span>
          <span className="footer-text">Production Cloud Lakehouse & NLQ</span>
        </div>

        <div className="footer-right">
          <div className="footer-pill">
            <Database size={13} className="text-blue" />
            <span>Supabase Cloud (AWS ap-northeast-1)</span>
          </div>
          <div className="footer-pill">
            <Cpu size={13} className="text-blue" />
            <span>FastAPI Backend 2.0</span>
          </div>
          <div className="footer-pill">
            <ShieldCheck size={13} className="text-blue" />
            <span>Analytics Contract Verified</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
