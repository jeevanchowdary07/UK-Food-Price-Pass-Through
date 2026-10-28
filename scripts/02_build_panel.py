"""Build/validate the 906-row category-month master panel.

If full country-month raw HMRC data have been downloaded, this script rebuilds
monthly HHI/unit-value measures from them. Otherwise it uses the bundled
retained category-month analytical extract used for the main analysis.
"""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from food_price_pass_through.features import aggregate_trade  # noqa:E402
from food_price_pass_through.panel import load_ons, merge_core_panel  # noqa:E402

raw_country = ROOT / "data" / "interim" / "hmrc_core_country_month_all_categories.csv"
monthly_bundled = ROOT / "data" / "processed" / "hmrc_monthly_core_measures_2014_2026.csv"
ons_path = ROOT / "data" / "raw" / "ons" / "ONS_MM23_selected_food_CPI_2014_Aug2026.csv"

if raw_country.exists():
    raw = pd.read_csv(raw_country)
    country_path = ROOT / "data" / "raw" / "hmrc" / "country_month" / "country_dimension.csv"
    country = pd.read_csv(country_path) if country_path.exists() else None
    trade = aggregate_trade(raw, country)
    # align bundled naming
    trade = trade.rename(columns={"import_value":"import_value_gbp","usable_net_mass":"net_mass_kg"})
else:
    trade = pd.read_csv(monthly_bundled, parse_dates=["month"])

ons = load_ons(ons_path)
panel = merge_core_panel(ons, trade, "2020-01-01", "2023-12-01")
if len(panel) != 906 or panel["category"].nunique() != 6:
    raise RuntimeError(f"Unexpected panel shape: {panel.shape}")
(ROOT / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
panel.to_csv(ROOT / 'data' / 'processed' / 'master_panel_rebuilt.csv', index=False)
print(f"Master panel validated: {len(panel)} rows, {panel['category'].nunique()} categories, through {panel['month'].max():%Y-%m}.")
