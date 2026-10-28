# Data directory

The committed data are deliberately limited to files required for transparent reproduction without duplicating large generated outputs.

- `raw/ons/` — selected official ONS MM23 food CPI series used in the study.
- `interim/hmrc_monthly_api_core/` — six verified 151-month HMRC category-level analytical extracts.
- `processed/hmrc_monthly_core_measures_2014_2026.csv` — compact monthly HMRC measure table used by the panel-validation route.
- `processed/master_panel_core_2014_2026.csv` and `processed/analysis_sample_main_lag03.csv` are generated locally and intentionally ignored by Git.

The live HMRC extraction audit records 58,196 supplier-country-month records. The exact query/audit manifests are in `provenance/`.
