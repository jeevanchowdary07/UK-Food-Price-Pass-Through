# Quick start

## Reproduce the main analysis

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-lock.txt
python scripts/00_validate_environment.py
python scripts/03_reproduce_final_analysis.py
python scripts/04_make_figures.py
python scripts/05_verify_reported_results.py
pytest -q
```

A successful run should recreate the 906-row master panel, the 882-row primary estimation sample, all eight figures, and a verification report with an overall `PASS` status.

## Refresh the HMRC data

A live refresh is optional and requires internet access:

```bash
python scripts/01_acquire_hmrc.py
python scripts/02_build_panel.py
python scripts/03_reproduce_final_analysis.py
python scripts/04_make_figures.py
python scripts/05_verify_reported_results.py
```

For the model equations and implementation details, see `docs/03_FORMULAS_AND_MODELS.md` and `docs/04_TECHNICAL_IMPLEMENTATION.md`.
