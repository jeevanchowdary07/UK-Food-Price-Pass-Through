# Technical implementation

## Analysis pipeline

1. `00_validate_environment.py` — checks the project configuration and required inputs.
2. `01_acquire_hmrc.py` — downloads HMRC data from the OTS API when a live refresh is required.
3. `02_build_panel.py` — builds and validates the monthly category panel.
4. `03_reproduce_final_analysis.py` — runs the RQ1–RQ3 models, diagnostics and robustness checks.
5. `04_make_figures.py` — recreates the eight figures used in the analysis.
6. `05_verify_reported_results.py` — checks the main reported values against the generated result tables.

## Reusable Python modules

- `features.py` — HHI, Top-3 share, log changes and trade aggregation.
- `panel.py` — ONS loading and common-period panel merge.
- `models.py` — lag construction, robust estimation and covariance-aware linear combinations.
- `quality.py` — category-level quality summaries and coverage checks.
- `hmrc.py` — HMRC API acquisition helpers.
- `plotting.py` — reusable plotting functions.

## Reproducibility

The standard offline run starts from the retained monthly HMRC analytical extracts and the ONS CPI input. The analysis reconstructs the 906-row panel and 882-row primary estimation sample, estimates the models, writes the result tables, and rebuilds the figures. The verification script then compares the headline results with the generated output files.

## Result traceability

The main outputs are stored as CSV and JSON files so that the reported coefficients, cumulative effects, diagnostics and robustness results can be checked directly. `results/tables/findings_summary.json` provides a compact summary of the principal results.
