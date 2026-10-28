# HMRC raw-data note

The study uses the official HMRC UK Trade Info Overseas Trade Statistics (OTS) API for the six food categories over January 2014 to July 2026. The audited extraction covered **58,196 supplier-country-month records** in total.

The full supplier-country response table is not stored in this repository. Instead, the repository keeps the information needed to reproduce and check the extraction:

- `provenance/HMRC_QUERY_MANIFEST.csv` records the exact API query used for each category;
- `provenance/LIVE_EXTRACTION_AUDIT.csv` records the observed row counts and basic completeness checks;
- `data/interim/hmrc_monthly_api_core/*.json` contains the six 151-month category-level analytical extracts used by the main models;
- `scripts/01_acquire_hmrc.py` can download and save the full supplier-country-month extracts on an internet-enabled machine;
- the analysis scripts reconstruct the monthly panel and statistical outputs from the retained analytical extracts.

The extraction audit recorded no null supplier-country identifiers and no non-zero suppression-index rows in the grouped API responses. A small number of country-month rows had missing or non-positive net mass, but their import-value share was zero or negligible in the audited extraction. This does not remove the wider limitation that HMRC suppression and quantity definitions can affect trade statistics, so that limitation is retained in the dissertation and technical documentation.
