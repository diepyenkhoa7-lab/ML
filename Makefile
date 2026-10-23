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
