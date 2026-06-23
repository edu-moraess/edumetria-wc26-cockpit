"""
Edumetria WC26 API
Backend desacoplado para consumo de dados e modelos.
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import io
import json
import os
import sys

# Adiciona raiz do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.montecarlo.simulation_engine import run_simulation
from models.montecarlo.risk_score_v2 import RiskScoreV2
from models.montecarlo.recession_monitor import calculate_recession_monitor
from models.montecarlo.wcli_calculator import calculate_wcli


# ─── Lifespan (startup/shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa conexões e caches no startup."""
    app.state.data_cache = {}
    app.state.last_refresh = None
    yield
    app.state.data_cache.clear()


app = FastAPI(
    title="Edumetria WC26 API",
    description="API analítica para impactos da Copa do Mundo FIFA 2026™",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS para consumo por frontend Streamlit, mobile, etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Dependências ────────────────────────────────────────────────────────────

def get_db():
    """Retorna conexão DuckDB (ou Postgres em produção)."""
    import duckdb
    db_path = os.getenv("DB_PATH", "data/wc26.duckdb")
    conn = duckdb.connect(db_path, read_only=True)
    try:
        yield conn
    finally:
        conn.close()


def load_processed_data(indicator: str) -> pd.DataFrame:
    """Carrega dados processados do cache ou disco."""
    cache = app.state.data_cache
    if indicator in cache:
        return cache[indicator]
    
    path = f"data/processed/{indicator}.parquet"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Dados '{indicator}' não encontrados. Rode o ETL.")
    
    df = pd.read_parquet(path)
    cache[indicator] = df
    return df


# ─── Endpoints de Health ───────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Verifica saúde da API e disponibilidade de dados."""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "data_sources": {}
    }
    
    for source in ["macro_usa", "markets", "tourism", "macro_can_mex"]:
        path = f"data/processed/{source}.parquet"
        status["data_sources"][source] = {
            "available": os.path.exists(path),
            "last_modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat() if os.path.exists(path) else None
        }
    
    return status


# ─── Endpoints de Dados Brutos ───────────────────────────────────────────────

@app.get("/api/v1/macro/usa", tags=["Dados"], response_model=Dict[str, Any])
async def get_macro_usa(
    series: Optional[List[str]] = Query(None, description="Séries FRED (GDP, CPIAUCSL, UNRATE, etc.)"),
    start_date: Optional[date] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Data final (YYYY-MM-DD)"),
    freq: Optional[str] = Query("Q", description="Frequência: D, M, Q, A"),
    format: str = Query("json", description="Formato: json, csv, parquet")
):
    """
    Retorna dados macroeconômicos dos EUA (FRED).
    
    Séries disponíveis: GDP, CPIAUCSL, UNRATE, FEDFUNDS, DGS10, DGS2, etc.
    """
    df = load_processed_data("macro_usa")
    
    if isinstance(df.index, pd.DatetimeIndex):
        if start_date:
            df = df[df.index >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df.index <= pd.Timestamp(end_date)]
    
    if series:
        available = [c for c in series if c in df.columns]
        df = df[available]
    
    if freq and freq != "Q":
        df = df.resample(freq).last()
    
    return _format_response(df, format, "macro_usa")


@app.get("/api/v1/macro/canada", tags=["Dados"])
async def get_macro_canada(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json"
):
    """Dados macroeconômicos do Canadá (StatCan + Bank of Canada)."""
    df = load_processed_data("macro_can_mex")
    if "country" in df.columns:
        df = df[df["country"] == "CAN"]
    
    return _format_response(df, format, "macro_canada")


@app.get("/api/v1/macro/mexico", tags=["Dados"])
async def get_macro_mexico(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json"
):
    """Dados macroeconômicos do México (Banxico + INEGI)."""
    df = load_processed_data("macro_can_mex")
    if "country" in df.columns:
        df = df[df["country"] == "MEX"]
    
    return _format_response(df, format, "macro_mexico")


@app.get("/api/v1/markets", tags=["Dados"])
async def get_markets(
    tickers: Optional[List[str]] = Query(None, description="Tickers (GSPC, IXIC, VIX, WTI, etc.)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json"
):
    """
    Dados de mercado financeiro (yfinance).
    
    Tickers: ^GSPC (S&P500), ^IXIC (Nasdaq), ^VIX, CL=F (WTI), BZ=F (Brent), etc.
    """
    df = load_processed_data("markets")
    
    if tickers:
        cols = [c for c in df.columns if any(t in c for t in tickers)]
        df = df[cols]
    
    return _format_response(df, format, "markets")


@app.get("/api/v1/tourism", tags=["Dados"])
async def get_tourism(
    country: Optional[str] = Query(None, description="CAN, MEX, ou deixe vazio para todos"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json"
):
    """Dados de turismo (chegadas internacionais)."""
    df = load_processed_data("tourism")
    
    if country and "country" in df.columns:
        df = df[df["country"] == country.upper()]
    
    return _format_response(df, format, "tourism")


# ─── Endpoints de Modelos ────────────────────────────────────────────────────

@app.get("/api/v1/risk-score", tags=["Modelos"])
async def get_risk_score(
    as_of: Optional[date] = Query(None, description="Data de cálculo (padrão: último disponível)")
):
    """
    Retorna o World Cup Risk Score 2.0 (0-100) com decomposição por dimensão.
    
    Dimensões: Financeira (35%), Energética (25%), Macroeconômica (25%), Geopolítica (15%).
    """
    try:
        risk_engine = RiskScoreV2()
        score = risk_engine.calculate(as_of=as_of)
        return {
            "risk_score": score.total,
            "as_of": score.date.isoformat() if score.date else None,
            "components": {
                "financial": {"score": score.financial, "weight": 0.35},
                "energy": {"score": score.energy, "weight": 0.25},
                "macro": {"score": score.macro, "weight": 0.25},
                "geopolitical": {"score": score.geopolitical, "weight": 0.15, "note": "GPR Index pendente"}
            },
            "interpretation": _interpret_risk(score.total),
            "methodology": "Caldara & Iacoviello (2022) adaptado para eventos esportivos"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no cálculo do Risk Score: {str(e)}")


@app.get("/api/v1/recession-monitor", tags=["Modelos"])
async def get_recession_monitor():
    """
    Retorna o Recession Monitor com probabilidade composta de recessão (0-100).
    
    Indicadores: Sahm Rule, Yield Spreads (10Y-2Y, 10Y-3M), Leading Index, Fed NY Probit.
    """
    try:
        result = calculate_recession_monitor()
        return {
            "recession_probability": result["recession_score"],
            "classification": result["classification"],
            "completeness_pct": result["completeness_pct"],
            "components": {
                name: {
                    "probability": comp["data"]["prob"],
                    "signal": comp["data"].get("signal", "—"),
                    "weight": comp["weight"]
                }
                for name, comp in result["components"].items()
            },
            "interpretation": _interpret_recession(result["recession_score"] or 0),
            "references": ["Sahm (2019)", "Estrella & Mishkin (1998)", "Fed NY (2024)"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no Recession Monitor: {str(e)}")


@app.get("/api/v1/forecast/monte-carlo", tags=["Modelos"])
async def get_monte_carlo_forecast(
    indicator: str = Query(..., description="Indicador a projetar (GDP_NOMINAL, CPI, etc.)"),
    country: str = Query("USA", description="País (USA, CAN, MEX)"),
    horizon_years: int = Query(5, ge=1, le=10, description="Horizonte de projeção (anos)"),
    simulations: int = Query(20000, ge=1000, le=50000, description="Número de simulações"),
    distribution: str = Query("student-t", description="student-t ou normal"),
    percentiles: List[float] = Query([0.05, 0.25, 0.50, 0.75, 0.95], description="Percentis de saída")
):
    """
    Executa simulação Monte Carlo 2.0 para projeção de indicadores.
    
    Distribuição Student-t (caudas gordas) via MLE, com fallback para Normal.
    """
    try:
        result = run_simulation(
            indicator_code=indicator,
            country_code=country,
            n_simulations=simulations,
            use_student_t=(distribution == "student-t")
        )
        
        if result is None:
            raise HTTPException(status_code=400, detail=f"Dados insuficientes para {indicator} ({country})")
        
        return {
            "indicator": indicator,
            "country": country,
            "horizon_years": horizon_years,
            "simulations": simulations,
            "distribution": result["distribution"],
            "df_t": result["df_t"],
            "percentiles": {
                str(p): result["percentiles"][y] 
                for p in percentiles 
                for y in result["forecast_years"][:horizon_years]
            },
            "point_forecast": result["percentiles"][result["forecast_years"][horizon_years-1]]["p50"],
            "confidence_intervals": {
                "p05_p95": (
                    result["percentiles"][result["forecast_years"][horizon_years-1]]["p05"],
                    result["percentiles"][result["forecast_years"][horizon_years-1]]["p95"]
                ),
            },
            "methodology": "MLE Student-t (McNeil et al., 2015) com fallback Normal"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na simulação Monte Carlo: {str(e)}")


@app.get("/api/v1/wcli", tags=["Modelos"])
async def get_wcli(
    country: str = Query(..., description="CAN, MEX, USA"),
    scenario: str = Query("baseline", description="baseline, optimistic, pessimistic")
):
    """
    World Cup Legacy Index (WCLI) — índice composto de impacto legado (0-100).
    
    Componentes: PIB (25%), Emprego (20%), Turismo (20%), FDI (15%), Infraestrutura (10%), ESG (10%).
    """
    try:
        result = calculate_wcli(country_code=country)
        
        return {
            "country": country,
            "scenario": scenario,
            "wcli_score": result["wcli_total"],
            "completeness": result["completeness_pct"],
            "components": {
                "gdp": {"score": result["scores"]["pib"], "weight": 0.25, "available": result["scores"]["pib"] is not None},
                "employment": {"score": result["scores"]["emprego"], "weight": 0.20, "available": result["scores"]["emprego"] is not None},
                "tourism": {"score": result["scores"]["turismo"], "weight": 0.20, "available": result["scores"]["turismo"] is not None},
                "fdi": {"score": result["scores"]["fdi"], "weight": 0.15, "available": result["scores"]["fdi"] is not None},
                "infrastructure": {"score": result["scores"]["infraestrutura"], "weight": 0.10, "available": result["scores"]["infraestrutura"] is not None},
                "esg": {"score": result["scores"]["esg"], "weight": 0.10, "available": result["scores"]["esg"] is not None, "note": "Placeholder — dados de aviação pendentes"}
            },
            "horizon": "2026-2035"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no WCLI: {str(e)}")


# ─── Endpoints de DiD / Synthetic Control (fase pós-MVP) ───────────────────

@app.get("/api/v1/econometrics/did", tags=["Econometria"])
async def get_did_analysis(
    event_country: str = Query(..., description="País que sediou (BRA, RUS, QAT, etc.)"),
    event_year: int = Query(..., description="Ano do evento"),
    outcome_var: str = Query("tourism_arrivals", description="Variável de resultado"),
    control_countries: Optional[List[str]] = Query(None, description="Países controle (padrão: automático)")
):
    """
    Difference-in-Differences (DiD) — estima efeito causal do evento.
    
    Compara trajetória do país-sede vs. países controle pré/pós evento.
    """
    from models.econometric.did import DiDAnalyzer
    
    try:
        analyzer = DiDAnalyzer()
        result = analyzer.run(
            treated_country=event_country,
            event_year=event_year,
            outcome=outcome_var,
            controls=control_countries
        )
        
        return {
            "treated_country": event_country,
            "event_year": event_year,
            "outcome_variable": outcome_var,
            "att": result.att,
            "att_ci_95": result.att_ci,
            "p_value": result.p_value,
            "significant": result.significant,
            "pre_trend_parallel": result.parallel_trends_passed,
            "model": result.model_spec,
            "r_squared": result.r_squared,
            "n_observations": result.n_obs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no DiD: {str(e)}")


@app.get("/api/v1/econometrics/synthetic-control", tags=["Econometria"])
async def get_synthetic_control(
    treated_country: str = Query(..., description="País tratado (ex: BRA)"),
    event_year: int = Query(..., description="Ano do evento"),
    outcome_var: str = Query("gdp_per_capita", description="Variável de resultado"),
    donor_pool: Optional[List[str]] = Query(None, description="Pool de doadores")
):
    """
    Synthetic Control Method — constrói contrafactual sintético.
    
    Retorna pesos dos doadores, gap pré/pós e teste de placebo.
    """
    from models.econometric.synthetic_control import SyntheticControl
    
    try:
        sc = SyntheticControl()
        result = sc.fit(
            treated=treated_country,
            event_year=event_year,
            outcome=outcome_var,
            donors=donor_pool
        )
        
        return {
            "treated_country": treated_country,
            "synthetic_weights": result.weights,
            "pre_rmspe": result.pre_rmspe,
            "post_gap": result.post_gap,
            "placebo_p_value": result.placebo_p,
            "significant": result.placebo_p < 0.05,
            "donor_pool_size": len(result.donors_used)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no Synthetic Control: {str(e)}")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _format_response(df: pd.DataFrame, format: str, filename: str):
    """Formata resposta em JSON, CSV ou Parquet."""
    if format == "json":
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
        if "date" in df.columns:
            df["date"] = df["date"].astype(str)
        return JSONResponse(content=df.to_dict(orient="records"))
    
    elif format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=True)
        buffer.seek(0)
        return StreamingResponse(
            io.BytesIO(buffer.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    
    elif format == "parquet":
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=True)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}.parquet"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Formato deve ser: json, csv, parquet")


def _interpret_risk(score: float) -> str:
    if score < 25:
        return "Baixo risco — ambiente favorável para o evento"
    elif score < 50:
        return "Risco moderado — monitoramento recomendado"
    elif score < 75:
        return "Risco elevado — contingências necessárias"
    else:
        return "Risco crítico — revisão estratégica urgente"


def _interpret_recession(prob: float) -> str:
    if prob < 20:
        return "Expansão — baixa probabilidade de recessão"
    elif prob < 40:
        return "Atenção — sinais mistos, monitorar"
    elif prob < 60:
        return "Alerta — risco elevado, preparar contingências"
    else:
        return "Recessão provável — ações defensivas recomendadas"


# ─── Run (desenvolvimento) ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
 