"""Download the full HMRC country-month extracts from the official OTS API.

This is the online reproducibility path. It is intentionally sequential because
large parallel API requests were less reliable during the live acquisition.
"""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from food_price_pass_through.config import load_config  # noqa:E402
from food_price_pass_through.hmrc import acquire_all  # noqa:E402

cfg = load_config()
raw_dir = ROOT / "data" / "raw" / "hmrc" / "country_month"
raw, log = acquire_all(cfg, mapping_version="core", output_dir=raw_dir)
interim = ROOT / "data" / "interim"
interim.mkdir(parents=True, exist_ok=True)
raw.to_csv(interim / "hmrc_core_country_month_all_categories.csv", index=False)
log.to_csv(interim / "hmrc_query_log_live.csv", index=False)
print(log.to_string(index=False))
print(f"Total country-month records downloaded: {len(raw):,}")
