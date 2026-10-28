from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict:
    path = path or ROOT / "config" / "project.yml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
