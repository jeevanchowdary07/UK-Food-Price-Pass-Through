# Technical demonstration guide

## Recommended live sequence

```bash
python scripts/00_validate_environment.py
python scripts/03_reproduce_final_analysis.py
python scripts/04_make_figures.py
python scripts/05_verify_reported_results.py
pytest -q
```

## What to show

1. `config/concordance/frozen_hs_coicop_concordance_v1.csv` — frozen category mapping.
2. `docs/03_FORMULAS_AND_MODELS.md` — exact HHI, unit-value and RQ1–RQ3 formulas.
3. `src/food_price_pass_through/features.py` — formula implementation.
4. `scripts/03_reproduce_final_analysis.py` — main estimation pipeline.
5. `results/tables/cumulative_effects_rq1_rq3.csv` — numerical RQ1–RQ3 outputs.
6. `results/tables/diagnostic_global_tests.csv` — evidence motivating robust inference.
7. `results/tables/robustness_cumulative_effects.csv` — sensitivity analysis.
8. Figures 05–08 — category heterogeneity, RQ2, RQ3 and robustness.
9. `results/reports/REPRODUCIBILITY_REPORT.md` — verification summary.

## Short technical explanation

The project combines official monthly HMRC import and ONS CPI series into six aligned food categories. Supplier-country import-value shares generate HHI and Top-3 concentration. Import value divided by usable net mass generates a category unit-value cost proxy. Monthly log changes are used in distributed-lag fixed-effects models over lags 0–3. RQ2 interacts the cost lags with lagged HHI; RQ3 adds the 2020–2023 disruption regime and triple interactions. Diagnostics show heteroskedasticity and cross-category dependence, so the primary inference uses a Driscoll–Kraay-type HAC covariance. The headline RQ1 association is positive and robust; HHI moderation is statistically unsupported; disruption strengthens pass-through but not through a statistically supported HHI-specific mechanism.
