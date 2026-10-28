# Diagnostics and robustness

## Residual diagnostics

| Diagnostic | Statistic | p-value | Interpretation |
|---|---:|---:|---|
| Breusch–Pagan LM | 172.879 | 7.15e-26 | Strong heteroskedasticity evidence |
| Pesaran CD | 4.543 | 5.55e-06 | Cross-category residual dependence |

Category-level Ljung–Box and ADF outputs are stored in `results/tables/diagnostic_ljung_box_by_category.csv` and `diagnostic_adf_by_category.csv`.

These diagnostics motivate robust covariance rather than conventional homoskedastic OLS standard errors.

## RQ1 sensitivity analysis

| Specification | Cumulative estimate | 95% CI | p-value |
|---|---:|---:|---:|
| Main 0–3 months | 0.1253 | [0.0620, 0.1887] | <0.001 |
| 0–6 months | 0.1973 | [0.0663, 0.3283] | 0.0032 |
| Winsorised 1–99% | 0.1295 | [0.0648, 0.1942] | <0.001 |
| Exclude ONS Feb–Jul 2026 flag | 0.1229 | [0.0579, 0.1879] | <0.001 |
| Post-May-2016 | 0.1349 | [0.0683, 0.2014] | <0.001 |
| Post-Jan-2022 | 0.1357 | [0.0852, 0.1863] | <0.001 |
| Full month-year fixed effects | 0.1105 | [0.0607, 0.1602] | <0.001 |

The sign and confidence-interval stability across all principal RQ1 sensitivity models strengthens the conclusion that positive short-run pass-through is not dependent on one preferred specification.

## Concentration robustness

Replacing HHI with Top-3 supplier share produces a statistically insignificant moderation slope (`p≈0.634`). A pre-2020 average-HHI moderator is also insignificant (`p≈0.237`). These checks reduce the likelihood that the RQ2 null result is simply an artefact of one concentration metric.
