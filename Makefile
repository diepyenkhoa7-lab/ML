PYTHON := .venv/bin/python
GEMMA_ADAPTER ?= adapters/gemma-jobs/20261017T105728Z
EPOCHS ?= 1
APP_PORT ?= 8000
export PIP_CACHE_DIR := $(CURDIR)/.cache/pip
export HF_HOME := $(CURDIR)/.cache/huggingface
export MPLCONFIGDIR := $(CURDIR)/.cache/matplotlib
export JUPYTER_DATA_DIR := $(CURDIR)/.cache/jupyter
export JUPYTER_RUNTIME_DIR := $(CURDIR)/.cache/jupyter/runtime
export IPYTHONDIR := $(CURDIR)/.cache/ipython

.PHONY: help setup check check-mlx lint api lab validate-example validate-sft gemma-download gemma-base gemma-smoke gemma-adapter gemma-plan-full gemma-infer-adapter gemma-train data-fetch data-profile data-clean test-data data-split data-verify salary-train

help:
	@echo "app: build Vue + serve local app | frontend-setup | frontend-build | app-test"
	@echo "setup | check | check-mlx | lint | api | lab"
	@echo "validate-example | validate-sft | gemma-download | gemma-base | gemma-smoke | gemma-adapter | gemma-train"
	@echo "gemma-adapter: TRAIN all train JSONL, EPOCHS=1 by default | gemma-plan-full | gemma-infer-adapter"
	@echo "gemma-reviewed-plan: no training | gemma-reviewed-train: real frozen 501-step reviewed-data trial"
	@echo "gemma-corrected-plan: no training | gemma-corrected-train: real 501-step corrected-label trial"
	@echo "salary-train | data-fetch | data-profile | data-clean | test-data | data-split | data-verify"

setup:
	bash scripts/setup.sh

check:
	$(PYTHON) -m pip check
	$(PYTHON) scripts/check_env.py

check-mlx:
	$(PYTHON) scripts/check_env.py --mlx

lint:
	$(PYTHON) -m ruff check scripts backend tests
	$(PYTHON) -m ruff format --check scripts backend tests

api:
	$(PYTHON) -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

.PHONY: app frontend-setup frontend-build app-test
frontend-setup:
	npm ci --prefix frontend --cache $(CURDIR)/.cache/npm

frontend-build:
	npm --prefix frontend run build

app: frontend-build
	$(PYTHON) -m uvicorn backend.app.main:app --host 127.0.0.1 --port $(APP_PORT)

app-test:
	$(PYTHON) -m unittest discover -s tests -v

lab:
	@mkdir -p "$(JUPYTER_RUNTIME_DIR)" "$(IPYTHONDIR)"
	$(PYTHON) -m jupyterlab --notebook-dir=notebooks --no-browser

validate-example:
	$(PYTHON) scripts/validate_sft.py --data data/examples/finetune

validate-sft:
	$(PYTHON) scripts/validate_sft.py --data data/finetune --strict-extraction

gemma-download:
	$(PYTHON) scripts/download_gemma.py --convert

gemma-base:
	$(PYTHON) scripts/gemma_infer.py

gemma-smoke: validate-example
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_smoke.yaml

gemma-adapter: validate-sft
	$(PYTHON) scripts/gemma_full_train.py --epochs $(EPOCHS) --confirm-training

gemma-plan-full:
	$(PYTHON) scripts/gemma_full_train.py --epochs $(EPOCHS)

gemma-infer-adapter:
	$(PYTHON) scripts/gemma_infer.py --adapter $(GEMMA_ADAPTER) --output outputs/environment/gemma_adapter.json

.PHONY: gemma-reviewed-plan gemma-reviewed-train
gemma-reviewed-plan:
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_reviewed.yaml

# Real training on the frozen reviewed corpus; one candidate under its locked protocol.
gemma-reviewed-train:
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_reviewed.yaml --confirm-training --summarize

.PHONY: gemma-corrected-plan gemma-corrected-train
gemma-corrected-plan:
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_corrected.yaml

gemma-corrected-train:
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_corrected.yaml --confirm-training --summarize

gemma-train: validate-sft
	$(PYTHON) scripts/gemma_train.py --config configs/gemma_train.yaml

# Salary training is authorized independently of the Gemma confirmation gate.
salary-train:
	$(PYTHON) scripts/run_salary_notebooks.py

# Experimental strict-label salary training; never switches the web model automatically.
.PHONY: salary-v3-collect salary-v3-prepare salary-v3-train salary-v31-prepare salary-v31-train
salary-v3-collect:
	$(PYTHON) scripts/collect_salary_v3.py --source joboko

salary-v3-prepare:
	$(PYTHON) scripts/prepare_salary_v3.py

salary-v3-train:
	$(PYTHON) scripts/train_salary_v3.py

salary-v31-prepare:
	$(PYTHON) scripts/prepare_salary_v31.py

salary-v31-train:
	$(PYTHON) scripts/train_salary_v31.py

data-fetch:
	$(PYTHON) scripts/fetch_salary_sources.py

data-profile:
	$(PYTHON) scripts/profile_salary_sources.py

data-clean:
	$(PYTHON) scripts/clean_data.py

test-data:
	$(PYTHON) -m unittest discover -s tests -v

data-split:
	$(PYTHON) scripts/prepare_salary_splits.py --freeze

data-verify:
	$(PYTHON) scripts/verify_salary_splits.py
