# Data provenance

## ONS
Official MM23 monthly CPI indices. CDIDs: Meat D7D6; Fish D7D7; Milk, cheese & eggs D7D8; Oils & fats D7D9; Fruit D7DA; Vegetables D7DB.

## HMRC UK Trade Info
Overseas Trade Statistics monthly import records. Core fields used by the acquisition pipeline include month, supplier country, suppression indicator, import value and net mass. Country of Dispatch is used for historical consistency.

## Extraction audit
The audited live extraction returned 58,196 supplier-country-month records across the six categories. Query metadata and audit evidence are retained under `provenance/`.

## Classification alignment
A frozen HS-to-CPI concordance is stored in `config/concordance/`. Butter (HS0405) is assigned to Oils & fats to align with the consumer-price classification. Mapping uncertainty is treated as a construct-validity limitation.

## Methodological breaks
HMRC changes around May 2016 and January 2022 are explicitly recognised and tested through restricted-sample robustness specifications. ONS's February–July 2026 lower-level classification issue is handled through a dedicated exclusion sensitivity test.
