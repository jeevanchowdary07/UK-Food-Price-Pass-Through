# Data card

## Scope
Monthly UK food data, January 2014–July 2026, for six CPI-aligned categories: Meat; Fish; Milk, cheese & eggs; Oils & fats; Fruit; Vegetables.

## Outcome
ONS MM23 category CPI, transformed as `100 × Δln(CPI)` for the primary models.

## Explanatory cost proxy
HMRC import unit value: usable import value divided by usable net mass, transformed as `100 × Δln(unit value)`.

## Concentration
Value-share HHI by supplier country; Top-3 supplier share is an alternative measure.

## Unit of analysis
Food-category month. The balanced master panel has 906 rows (6 categories × 151 months). The main 0–3 lag model has 882 rows.

## Known limitations
Unit values are composition-sensitive; HS and COICOP classifications are not identical; supplier-country HHI does not observe firm contracts or buyer bargaining power; HMRC has methodological breaks around May 2016 and January 2022; a lower-level ONS classification issue affects part of 2026 and is tested through sensitivity analysis.
