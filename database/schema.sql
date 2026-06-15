-- ============================================================
-- database/schema.sql — Edumetria WC26 Cockpit v3
-- CORREÇÃO: FKs removidas de fact_indicator_values
-- DuckDB não suporta TRUNCATE CASCADE
-- Integridade garantida pelo loader Python (KNOWN_CODES)
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_country (
    country_code  VARCHAR PRIMARY KEY,
    country_name  VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_city (
    city_id       INTEGER PRIMARY KEY,
    city_name     VARCHAR NOT NULL,
    country_code  VARCHAR,
    host_role     VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_code VARCHAR PRIMARY KEY,
    indicator_name VARCHAR NOT NULL,
    unit           VARCHAR,
    category       VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_id        INTEGER PRIMARY KEY,
    source_name      VARCHAR NOT NULL,
    source_type      VARCHAR,
    reliability_tier VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_scenario (
    scenario_code VARCHAR PRIMARY KEY,
    description   VARCHAR
);

-- FKs removidas — DELETE simples sem CASCADE
CREATE TABLE IF NOT EXISTS fact_indicator_values (
    id              BIGINT PRIMARY KEY,
    country_code    VARCHAR,
    city_id         INTEGER,
    indicator_code  VARCHAR NOT NULL,
    scenario_code   VARCHAR NOT NULL,
    source_id       INTEGER,
    period          DATE NOT NULL,
    period_type     VARCHAR NOT NULL,
    value           DOUBLE NOT NULL,
    is_forecast     BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_low  DOUBLE,
    confidence_high DOUBLE,
    ingested_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fact_wcli (
    id                   BIGINT PRIMARY KEY,
    country_code         VARCHAR,
    period               DATE NOT NULL,
    scenario_code        VARCHAR NOT NULL,
    score_pib            DOUBLE,
    score_emprego        DOUBLE,
    score_turismo        DOUBLE,
    score_fdi            DOUBLE,
    score_infraestrutura DOUBLE,
    score_esg            DOUBLE,
    wcli_total           DOUBLE NOT NULL,
    wcli_classification  VARCHAR NOT NULL,
    calculated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fact_montecarlo_runs (
    run_id        BIGINT PRIMARY KEY,
    run_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    n_simulations INTEGER NOT NULL,
    model_version VARCHAR NOT NULL,
    notes         VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_montecarlo_distribution (
    id             BIGINT PRIMARY KEY,
    run_id         BIGINT,
    country_code   VARCHAR,
    indicator_code VARCHAR,
    period         DATE NOT NULL,
    p05            DOUBLE,
    p25            DOUBLE,
    p50            DOUBLE,
    p75            DOUBLE,
    p95            DOUBLE,
    mean           DOUBLE,
    std_dev        DOUBLE
);

CREATE TABLE IF NOT EXISTS audit_fifa_projections (
    id               BIGINT PRIMARY KEY,
    indicator_code   VARCHAR,
    country_code     VARCHAR,
    fifa_value       DOUBLE,
    fifa_unit        VARCHAR,
    classification   VARCHAR,
    rationale        VARCHAR,
    comparable_event VARCHAR,
    reviewed_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO dim_country (country_code, country_name) VALUES
    ('USA', 'Estados Unidos'),
    ('CAN', 'Canadá'),
    ('MEX', 'México')
ON CONFLICT DO NOTHING;

INSERT INTO dim_scenario (scenario_code, description) VALUES
    ('base',        'Premissas centrais'),
    ('conservador', 'Demanda abaixo do esperado'),
    ('otimista',    'Alta ocupação e turismo'),
    ('estresse',    'Choques simultâneos')
ON CONFLICT DO NOTHING;