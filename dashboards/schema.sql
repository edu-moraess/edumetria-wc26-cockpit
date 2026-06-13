-- Schema DDL para o Data Warehouse do Projeto FIFA 2026

CREATE TABLE IF NOT EXISTS dim_location (
    location_id SERIAL PRIMARY KEY,
    location_code VARCHAR(10) UNIQUE NOT NULL, -- ex: 'USA', 'MEX', 'CAN', 'GLOBAL'
    location_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL -- 'Country', 'City', 'Region'
);

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_id SERIAL PRIMARY KEY,
    indicator_code VARCHAR(50) UNIQUE NOT NULL, -- ex: 'WTI_BRENT_SPREAD', 'US_FED_RATE'
    indicator_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Macro', 'Finance', 'Tourism', 'Geopolitics'
    unit VARCHAR(50) NOT NULL, -- 'USD', '%', 'Index'
    frequency VARCHAR(20) -- 'Daily', 'Monthly', 'Annual'
);

CREATE TABLE IF NOT EXISTS fact_indicator_values (
    fact_id SERIAL PRIMARY KEY,
    date_ref DATE NOT NULL,
    indicator_id INTEGER REFERENCES dim_indicator(indicator_id),
    location_id INTEGER REFERENCES dim_location(location_id),
    value NUMERIC(18, 6) NOT NULL,
    source VARCHAR(100) NOT NULL, -- ex: 'FRED', 'YFinance'
    is_forecast BOOLEAN DEFAULT FALSE,
    scenario VARCHAR(50) DEFAULT 'Baseline', -- 'Baseline', 'Stress', 'Optimistic'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(date_ref, indicator_id, location_id, scenario)
);
