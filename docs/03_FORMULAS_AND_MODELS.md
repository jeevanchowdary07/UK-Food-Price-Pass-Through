# Formulas and statistical models

Notation: `c` = food category, `t` = month, `j` = supplier country, `k` = lag.

## 1. Supplier share and HHI

\[
s_{jct}=\frac{V_{jct}}{\sum_jV_{jct}}
\]

\[
HHI_{ct}=\sum_js_{jct}^2
\]

Implemented in `src/food_price_pass_through/features.py::hhi_from_values`.

A simple audit example with supplier shares 0.50, 0.30 and 0.20 gives:

\[
0.50^2+0.30^2+0.20^2=0.38.
\]

## 2. Top-3 supplier share

\[
Top3_{ct}=\sum_{j=1}^{3}s_{(j)ct}
\]

Implemented in `features.py::top_n_share`.

## 3. Import unit value

\[
UV_{ct}=\frac{\sum_j V^{usable}_{jct}}{\sum_jM^{usable}_{jct}}
\]

where `V` is import value and `M` is usable net mass. Unit values are treated as cost proxies, not pure prices.

## 4. Log changes

\[
\Delta Cost_{ct}=100[\ln(UV_{ct})-\ln(UV_{c,t-1})]
\]

\[
\Delta CPI_{ct}=100[\ln(CPI_{ct})-\ln(CPI_{c,t-1})]
\]

Implemented through `features.py::safe_log_change` and the final analysis script.

## 5. RQ1 — distributed-lag pass-through

\[
\Delta CPI_{ct}=\alpha_c+\lambda_m+\delta t+\sum_{k=0}^{3}\beta_k\Delta Cost_{c,t-k}+\varepsilon_{ct}
\]

Cumulative 0–3 month pass-through:

\[
PT_{0-3}=\sum_{k=0}^{3}\beta_k.
\]

The final coefficients sum to approximately:

\[
0.0331+0.0284+0.0323+0.0315=0.1253.
\]

## 6. RQ2 — HHI moderation

\[
\Delta CPI_{ct}=BaseModel+\gamma HHI_{c,t-1}+\sum_{k=0}^{3}\theta_k(\Delta Cost_{c,t-k}\times HHI_{c,t-1})+\varepsilon_{ct}
\]

Marginal cumulative pass-through at HHI level `h`:

\[
PT(h)=\sum_{k=0}^{3}(\beta_k+\theta_k h).
\]

The hypothesis test of systematic HHI moderation is based on `Σθ_k`.

## 7. RQ3 — disruption regime and triple interaction

Let `D_t=1` for January 2020–December 2023 and `0` otherwise.

\[
\Delta CPI_{ct}=BaseModel+\rho D_t+\psi(HHI_{c,t-1}D_t)+\sum_{k=0}^{3}\eta_k(\Delta Cost_{c,t-k}D_t)+\sum_{k=0}^{3}\kappa_k(\Delta Cost_{c,t-k}HHI_{c,t-1}D_t)+\varepsilon_{ct}.
\]

`Σκ_k` is the concentration-specific incremental moderation during disruption. Regime-specific cumulative pass-through is computed with linear combinations of the fitted coefficients and their full robust covariance matrix.

## 8. Inference

Point estimates are OLS conditional on category effects, calendar-month controls and trend. Inference uses statsmodels `hac-groupsum`, described here as a **Driscoll–Kraay-type cross-section/time HAC covariance estimator**, with primary bandwidth four months. The wording deliberately distinguishes the implementation from a claim that the estimator establishes causality.

## 9. Linear combinations

Cumulative effects are not obtained by adding standard errors. If coefficient vector is `b`, covariance matrix is `Σ`, and linear-combination weights are `w`, then:

\[
\widehat{L}=w'b,\qquad SE(\widehat{L})=\sqrt{w'\Sigma w}.
\]

Implemented in `src/food_price_pass_through/models.py::lincomb` and the final analysis script.
