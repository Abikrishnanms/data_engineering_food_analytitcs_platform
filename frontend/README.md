# FoodFlow Analytics — React Frontend

This directory contains the **React 19** executive dashboard application for the FoodFlow Analytics Platform.

## Features
- **Blue & White Theme**: Professional, distraction-free SaaS design system built with custom CSS and Lucide React icons.
- **Executive Dashboard**: 8 non-additive KPI cards, interactive SVG 365-day trend area charts, ranking bars, and distribution metrics.
- **Ask FoodFlow (NLQ)**: Conversational business intelligence interface with AST-validated read-only SQL inspection and data tables.
- **Vite Proxy**: Configured to seamlessly reverse-proxy `/api` requests to the FastAPI backend (`http://127.0.0.1:8000`).

## Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

For full system architecture, ETL pipeline, Supabase Cloud configuration, and data scale documentation, refer to the [Root README](../README.md).
