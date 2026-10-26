PYTHON := .venv-tf/bin/python
.PHONY: check prepare train-baseline train-llm test
check:
	$(PYTHON) -m pip check
prepare:
	$(PYTHON) -m career_ai prepare
train-baseline:
	$(PYTHON) -m career_ai train-baseline
train-llm:
	$(PYTHON) -m career_ai train-llm
test:
	$(PYTHON) -m unittest discover -s tests -v

.PHONY: status pipeline-background
status:
	$(PYTHON) scripts/status.py
pipeline-background:
	$(PYTHON) scripts/start_background.py

.PHONY: auto-tick
auto-tick:
	$(PYTHON) -m career_auto.coordinator

.PHONY: web web-build
web-build:
	npm --prefix frontend run build
web: web-build
	MPLCONFIGDIR=$(CURDIR)/.cache/matplotlib $(PYTHON) -m uvicorn career_web.app:app --host 127.0.0.1 --port 8000 --workers 1
