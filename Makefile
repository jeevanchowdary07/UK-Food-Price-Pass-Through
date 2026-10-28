.PHONY: validate test reproduce figures verify all live

validate:
	python scripts/00_validate_environment.py

test:
	pytest -q

reproduce:
	python scripts/03_reproduce_final_analysis.py

figures:
	python scripts/04_make_figures.py

verify:
	python scripts/05_verify_reported_results.py

all: validate reproduce figures verify test

live:
	python scripts/01_acquire_hmrc.py
	python scripts/02_build_panel.py
	python scripts/03_reproduce_final_analysis.py
	python scripts/04_make_figures.py
	python scripts/05_verify_reported_results.py
