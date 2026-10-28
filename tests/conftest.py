from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def pytest_sessionstart(session):
    """Ensure generated analytical datasets exist before integrity tests run.

    A fresh clone intentionally omits the large generated master/analysis CSVs.
    The canonical offline analysis script recreates them from the committed
    verified HMRC monthly extracts and ONS input.
    """
    required = [
        ROOT / 'data' / 'processed' / 'master_panel_core_2014_2026.csv',
        ROOT / 'data' / 'processed' / 'analysis_sample_main_lag03.csv',
    ]
    if not all(p.exists() for p in required):
        subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / '03_reproduce_final_analysis.py')],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
