# HMRC data provenance

The project uses the official HMRC UK Trade Info OTS API. The audited extraction covered **58,196 supplier-country-month records** across the six primary food categories and 151 months from January 2014 to July 2026.

To keep the repository focused on reproducible analysis, the full supplier-country response table is not committed. The following evidence is retained:

1. `provenance/HMRC_QUERY_MANIFEST.csv` — the exact API query for each category;
2. `provenance/LIVE_EXTRACTION_AUDIT.csv` — extraction row counts and quality checks;
3. `data/interim/hmrc_monthly_api_core/` — the six monthly analytical extracts used by the main analysis;
4. `scripts/01_acquire_hmrc.py` — the script used to reproduce the full supplier-country extraction;
5. `scripts/03_reproduce_final_analysis.py` — the script that rebuilds the analytical panel and final statistical outputs.

Official sources:

- OTS API: https://api.uktradeinfo.com/OTS
- Country dimension: https://api.uktradeinfo.com/Country
- Commodity dimension: https://api.uktradeinfo.com/Commodity
