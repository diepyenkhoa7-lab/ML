#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PIP_CACHE_DIR="$PWD/.cache/pip"
export HF_HOME="$PWD/.cache/huggingface"
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
export JUPYTER_DATA_DIR="$PWD/.cache/jupyter"
export JUPYTER_RUNTIME_DIR="$PWD/.cache/jupyter/runtime"
export IPYTHONDIR="$PWD/.cache/ipython"
mkdir -p "$PIP_CACHE_DIR" "$HF_HOME" "$MPLCONFIGDIR" "$JUPYTER_RUNTIME_DIR" "$IPYTHONDIR"
if [[ ! -x .venv/bin/python ]]; then
  "${PYTHON:-python3.11}" -m venv .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info >= (3, 11), "Can Python >=3.11"'
if [[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]]; then
  requirements_file=requirements-mlx.txt
  if [[ -f requirements-lock-macos-arm64.txt ]]; then
    requirements_file=requirements-lock-macos-arm64.txt
  fi
else
  requirements_file=requirements-dev.txt
fi
if command -v uv >/dev/null 2>&1; then
  uv pip install --python .venv/bin/python --cache-dir "$PWD/.cache/uv" -r "$requirements_file"
else
  .venv/bin/python -m pip install -r "$requirements_file"
fi
.venv/bin/python -m ipykernel install --prefix "$PWD/.venv" \
  --name it-career-insight --display-name 'Python (IT Career Insight)'
.venv/bin/python -m pip check
.venv/bin/python scripts/check_env.py
