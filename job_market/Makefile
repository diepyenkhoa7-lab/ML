PYTHON ?= python3
export PYTHONPATH := src

.PHONY: check lint test run sources preview
check: lint test

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

test:
	$(PYTHON) -m pytest tests -q

run:
	$(PYTHON) -m streamlit run app.py

sources:
	$(PYTHON) -m career_market sources

preview:
	$(PYTHON) -m career_market preview jobs-2023 --limit 5
