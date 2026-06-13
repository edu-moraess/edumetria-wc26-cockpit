-- ============================================================
-- DIMENSÕES
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_country (
    country_code  VARCHAR PRIMARY KEY,
    country_name  VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_city (
    city_id       INTEGER PRIMARY KEY,
    city_name     VARCHAR NOT NULL,
    country_code  VARCHAR NOT NULL REFERENCES dim_country(country_code),
    host_role     VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_code VARCHAR PRIMARY KEY,
    indicator_name VARCHAR NOT NULL,
    unit           VARCHAR,
    category       VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_source (
    source_id     INTEGER PRIMARY KEY,
    source_name   VARCHAR NOT NULL,
    source_type   VARCHAR,
    reliability_tier VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_scenario (
    scenario_code VARCHAR PRIMARY KEY,
    description   VARCHAR
);

-- ============================================================
-- FATOS — SÉRIES OBSERVADAS E PROJETADAS
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_indicator_values (
    id              BIGINT PRIMARY KEY,
    country_code    VARCHAR REFERENCES dim_country(country_code),
    city_id         INTEGER REFERENCES dim_city(city_id),
    indicator_code  VARCHAR NOT NULL REFERENCES dim_indicator(indicator_code),
    scenario_code   VARCHAR NOT NULL REFERENCES dim_scenario(scenario_code),
    source_id       INTEGER REFERENCES dim_source(source_id),
    period          DATE NOT NULL,
    period_type     VARCHAR NOT NULL,
    value           DOUBLE NOT NULL,
    is_forecast     BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_low  DOUBLE,
    confidence_high DOUBLE,
    ingested_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version         INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- WORLD CUP LEGACY INDEX (WCLI)
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_wcli (
    id              BIGINT PRIMARY KEY,
    country_code    VARCHAR REFERENCES dim_country(country_code),
    period          DATE NOT NULL,
    scenario_code   VARCHAR NOT NULL REFERENCES dim_scenario(scenario_code),
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

-- ============================================================
-- MONTE CARLO
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_montecarlo_runs (
    run_id          BIGINT PRIMARY KEY,
    run_timestamp   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    n_simulations   INTEGER NOT NULL,
    model_version   VARCHAR NOT NULL,
    notes           VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_montecarlo_distribution (
    id              BIGINT PRIMARY KEY,
    run_id          BIGINT REFERENCES fact_montecarlo_runs(run_id),
    country_code    VARCHAR REFERENCES dim_country(country_code),
    indicator_code  VARCHAR REFERENCES dim_indicator(indicator_code),
    period          DATE NOT NULL,
    p05             DOUBLE,
    p25             DOUBLE,
    p50             DOUBLE,
    p75             DOUBLE,
    p95             DOUBLE,
    mean            DOUBLE,
    std_dev         DOUBLE
);

-- ============================================================
-- AUDITORIA DAS PROJEÇÕES FIFA
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_fifa_projections (
    id              BIGINT PRIMARY KEY,
    indicator_code  VARCHAR REFERENCES dim_indicator(indicator_code),
    country_code    VARCHAR REFERENCES dim_country(country_code),
    fifa_value      DOUBLE,
    fifa_unit       VARCHAR,
    classification  VARCHAR,
    rationale       VARCHAR,
    comparable_event VARCHAR,
    reviewed_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SEEDS BÁSICOS
-- ============================================================

INSERT INTO dim_country (country_code, country_name) VALUES
    ('USA', 'Estados Unidos'),
    ('CAN', 'Canadá'),
    ('MEX', 'México')
ON CONFLICT DO NOTHING;

INSERT INTO dim_scenario (scenario_code, description) VALUES
    ('conservador', 'Demanda abaixo do esperado'),
    ('base', 'Premissas centrais'),
    ('otimista', 'Alta ocupação e turismo'),
    ('estresse', 'Choques simultâneos (recessão, petróleo, geopolítica, migração, logística)')
ON CONFLICT DO NOTHING;
