from __future__ import annotations

import math
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm


def add_lags(panel: pd.DataFrame, max_lag: int = 6) -> pd.DataFrame:
    x = panel.sort_values(["category", "month"]).copy()
    for k in range(max_lag + 1):
        x[f"cost_l{k}"] = x.groupby("category")["import_cost_change_pct"].shift(k)
    x["hhi_l1"] = x.groupby("category")["hhi"].shift(1)
    x["top3_l1"] = x.groupby("category")["top3_share"].shift(1)
    return x


def fit_dk(formula: str, data: pd.DataFrame, maxlags: int = 4):
    """OLS point estimates with category/time controls and HAC-groupsum covariance.

    Statsmodels' hac-groupsum covariance is used as a Driscoll-Kraay-type
    cross-section/time HAC estimator. Data must be sorted by month then category.
    """
    d = data.sort_values(["month", "category"]).copy()
    d["time_seq"] = pd.Categorical(d["month"], ordered=True).codes
    model = smf.ols(formula, data=d).fit()
    try:
        robust = model.get_robustcov_results(
            cov_type="hac-groupsum", time=d["time_seq"].to_numpy(),
            maxlags=maxlags, use_correction="hac"
        )
        cov_name = f"hac-groupsum (Driscoll-Kraay-type), maxlags={maxlags}"
    except Exception as exc:
        warnings.warn(f"hac-groupsum failed ({exc}); falling back to HAC")
        robust = model.get_robustcov_results(cov_type="HAC", maxlags=maxlags, use_correction=True)
        cov_name = f"HAC fallback, maxlags={maxlags}"
    return model, robust, cov_name


def coefficient_table(model, robust) -> pd.DataFrame:
    names = model.model.exog_names
    coef = np.asarray(robust.params, dtype=float)
    se = np.asarray(robust.bse, dtype=float)
    t = np.divide(coef, se, out=np.full_like(coef, np.nan), where=se > 0)
    p = 2 * (1 - norm.cdf(np.abs(t)))
    return pd.DataFrame({
        "term": names, "coef": coef, "std_error": se, "t": t,
        "p_value": p, "ci_low": coef - 1.96 * se, "ci_high": coef + 1.96 * se,
    })


def lincomb(model, robust, weights: dict[str, float]) -> dict[str, float]:
    names = model.model.exog_names
    b = np.asarray(robust.params, dtype=float)
    cov = np.asarray(robust.cov_params(), dtype=float)
    w = np.array([weights.get(name, 0.0) for name in names], dtype=float)
    estimate = float(w @ b)
    variance = float(w @ cov @ w)
    se = math.sqrt(max(variance, 0.0))
    z = estimate / se if se > 0 else np.nan
    p = float(2 * (1 - norm.cdf(abs(z)))) if np.isfinite(z) else np.nan
    return {
        "estimate": estimate, "std_error": se,
        "ci_low": estimate - 1.96 * se, "ci_high": estimate + 1.96 * se,
        "p_value": p,
    }
