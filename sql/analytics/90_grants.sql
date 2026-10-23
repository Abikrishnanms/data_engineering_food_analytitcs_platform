-- =============================================================================
-- FoodFlow Analytics - Read-only grants on the analytics contract
-- File: sql/analytics/90_grants.sql
-- Owner: Swetha (agree with Lekshmi Priya, who owns the role)
-- Run LAST, as a privileged user. Safe to re-run.
--
-- Goal: the NLQ/dashboard role can read ONLY the approved views/functions,
-- not the raw tables.
-- =============================================================================
DO $$
DECLARE v text;
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'foodflow_analytics') THEN
        -- Remove the broad table access first (see docs/database_setup.md section 6)
        REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM foodflow_analytics;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM foodflow_analytics;

        FOR v IN
            SELECT table_name FROM information_schema.views
            WHERE table_schema = 'public'
              AND (table_name LIKE 'v\_kpi\_%' OR table_name LIKE 'v\_q%'
                   OR table_name IN ('v_orders_enriched', 'v_order_items_enriched'))
        LOOP
            EXECUTE format('GRANT SELECT ON public.%I TO foodflow_analytics', v);
        END LOOP;
        GRANT EXECUTE ON FUNCTION fn_kpi_summary(date, date),
                                  fn_top_restaurants(date, date, int),
                                  fn_top_items(date, date, int)
              TO foodflow_analytics;
    ELSE
        RAISE NOTICE 'Role foodflow_analytics not found - create it first (docs/database_setup.md).';
    END IF;
END $$;
