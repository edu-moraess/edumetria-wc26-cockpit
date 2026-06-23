"""
Synthetic Control Method (SCM)
Constrói contrafactual sintético para estimar efeito causal.

Baseado em: Abadie, Diamond & Hainmueller (2010, 2015)
"""
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from dataclasses import dataclass
from typing import List, Optional, Dict
import warnings


@dataclass
class SCResult:
    weights: Dict[str, float]
    pre_rmspe: float
    post_gap: float
    placebo_p: float
    donors_used: List[str]
    synthetic_series: pd.DataFrame
    gap_series: pd.DataFrame
    placebo_gaps: Optional[Dict[str, pd.DataFrame]] = None


class SyntheticControl:
    """
    Synthetic Control Method para análise de impacto de Copas.
    
    Uso:
        sc = SyntheticControl()
        result = sc.fit(
            treated="BRA",
            event_year=2014,
            outcome="tourism_arrivals",
            donors=["ARG", "CHL", "COL", "MEX", "PER"]
        )
    """
    
    def __init__(self, data_path: str = "data/external/world_bank"):
        self.data_path = data_path
        self.df = None
        self._load_data()
    
    def _load_data(self):
        import os
        import glob
        
        processed_path = "data/processed/world_bank.parquet"
        if os.path.exists(processed_path):
            self.df = pd.read_parquet(processed_path)
            return
        
        csv_files = glob.glob(f"{self.data_path}/*.csv")
        if csv_files:
            dfs = [pd.read_csv(f) for f in csv_files]
            self.df = pd.concat(dfs, ignore_index=True)
        else:
            self.df = self._create_mock_data()
    
    def _create_mock_data(self) -> pd.DataFrame:
        np.random.seed(42)
        countries = ["BRA", "ARG", "CHL", "COL", "MEX", "PER", "DEU", "FRA", "ZAF", "RUS"]
        years = range(2000, 2024)
        
        records = []
        for country in countries:
            base = np.random.uniform(3, 20)
            trend = np.random.uniform(0.02, 0.08)
            
            for year in years:
                treatment = 0
                if country == "BRA" and year >= 2014:
                    treatment = np.random.uniform(0.5, 1.5)
                
                value = base * (1 + trend) ** (year - 2000) + treatment + np.random.normal(0, 0.5)
                
                records.append({
                    "country_code": country,
                    "year": year,
                    "tourism_arrivals": max(0, value),
                    "gdp_per_capita": base * 1000 + np.random.normal(0, 500),
                })
        
        return pd.DataFrame(records)
    
    def fit(
        self,
        treated: str,
        event_year: int,
        outcome: str = "tourism_arrivals",
        predictors: Optional[List[str]] = None,
        donors: Optional[List[str]] = None,
        optimization_period: Optional[tuple] = None
    ) -> SCResult:
        
        df = self.df.copy()
        
        if donors is None:
            donors = df["country_code"].unique().tolist()
            donors = [d for d in donors if d != treated]
        
        if optimization_period is None:
            optimization_period = (event_year - 10, event_year - 1)
        
        pre_period = df[df["year"] <= event_year - 1]
        all_period = df.copy()
        
        pre_wide = pre_period.pivot(index="year", columns="country_code", values=outcome)
        all_wide = all_period.pivot(index="year", columns="country_code", values=outcome)
        
        y_treated = pre_wide[treated].dropna()
        y_donors = pre_wide[donors].dropna()
        
        common_years = y_treated.index.intersection(y_donors.index)
        y_treated = y_treated.loc[common_years]
        y_donors = y_donors.loc[common_years]
        
        def objective(w):
            synthetic = y_donors.values @ w
            return np.sum((y_treated.values - synthetic) ** 2)
        
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        ]
        bounds = [(0, 1) for _ in donors]
        
        w0 = np.ones(len(donors)) / len(donors)
        
        result = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-10}
        )
        
        weights = dict(zip(donors, result.x))
        weights = {k: round(v, 4) for k, v in weights.items() if v > 0.001}
        
        all_years = all_wide.index
        synthetic = all_wide[donors].fillna(method="ffill").values @ result.x
        treated_all = all_wide[treated].fillna(method="ffill").values
        
        gap = treated_all - synthetic
        
        pre_mask = all_years <= event_year - 1
        pre_rmspe = np.sqrt(np.mean(gap[pre_mask] ** 2))
        
        post_mask = all_years >= event_year
        post_gap = np.mean(gap[post_mask]) if np.any(post_mask) else 0
        
        placebo_p = self._placebo_test(
            all_wide, treated, donors, result.x, event_year, optimization_period
        )
        
        synthetic_df = pd.DataFrame({
            "year": all_years,
            "treated": treated_all,
            "synthetic": synthetic,
            "gap": gap,
            "event_year": event_year
        })
        
        gap_df = pd.DataFrame({
            "year": all_years,
            "gap": gap,
            "event_year": event_year
        })
        
        return SCResult(
            weights=weights,
            pre_rmspe=pre_rmspe,
            post_gap=post_gap,
            placebo_p=placebo_p,
            donors_used=[k for k, v in weights.items() if v > 0.001],
            synthetic_series=synthetic_df,
            gap_series=gap_df
        )
    
    def _placebo_test(self, all_wide, treated, donors, true_weights, event_year, optimization_period):
        post_gaps = []
        
        for donor in donors:
            try:
                other_donors = [d for d in donors if d != donor]
                
                pre_wide = all_wide.loc[optimization_period[0]:optimization_period[1]]
                y_donor = pre_wide[donor].dropna()
                y_others = pre_wide[other_donors].dropna()
                
                common = y_donor.index.intersection(y_others.index)
                y_donor = y_donor.loc[common]
                y_others = y_others.loc[common]
                
                def obj(w):
                    return np.sum((y_donor.values - y_others.values @ w) ** 2)
                
                w0 = np.ones(len(other_donors)) / len(other_donors)
                res = minimize(obj, w0, method="SLSQP",
                              bounds=[(0, 1)] * len(other_donors),
                              constraints=[{"type": "eq", "fun": lambda w: np.sum(w) - 1}])
                
                all_years = all_wide.index
                synthetic = all_wide[other_donors].fillna(method="ffill").values @ res.x
                donor_all = all_wide[donor].fillna(method="ffill").values
                gap = donor_all - synthetic
                
                post_mask = all_years >= event_year
                post_gap = np.mean(gap[post_mask]) if np.any(post_mask) else 0
                post_gaps.append(post_gap)
                
            except Exception:
                continue
        
        if not post_gaps:
            return 1.0
        
        true_post = np.mean((all_wide[treated].fillna(method="ffill").values - 
                             all_wide[donors].fillna(method="ffill").values @ true_weights)[all_wide.index >= event_year])
        
        p_value = np.mean([abs(g) >= abs(true_post) for g in post_gaps])
        return p_value
    
    def fit_all_world_cups(self, outcome: str = "tourism_arrivals") -> pd.DataFrame:
        from models.econometric.did import DiDAnalyzer
        
        wc_info = DiDAnalyzer.WORLD_CUPS
        results = []
        
        for country, info in wc_info.items():
            try:
                result = self.fit(
                    treated=country,
                    event_year=info["year"],
                    outcome=outcome
                )
                results.append({
                    "country": country,
                    "year": info["year"],
                    "post_gap": result.post_gap,
                    "pre_rmspe": result.pre_rmspe,
                    "placebo_p": result.placebo_p,
                    "significant": result.placebo_p < 0.05,
                    "donors": ", ".join(result.donors_used),
                    "weights": result.weights
                })
            except Exception as e:
                results.append({
                    "country": country,
                    "year": info["year"],
                    "error": str(e)
                })
        
        return pd.DataFrame(results)
