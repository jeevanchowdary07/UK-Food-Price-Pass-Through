from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from food_price_pass_through.config import load_config  # noqa:E402

cfg = load_config()
print("Project:", cfg["project"]["title"])
print("Categories:", ", ".join(cfg["categories"].keys()))
print("Environment OK")
