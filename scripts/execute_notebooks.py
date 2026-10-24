"""Execute all demo notebooks in fresh TensorFlow kernels; training flags stay explicit."""

import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
os.environ["JUPYTER_PATH"] = str(root / ".venv-tf/share/jupyter")
os.environ["JUPYTER_RUNTIME_DIR"] = str(root / ".cache/jupyter")
os.environ["IPYTHONDIR"] = str(root / ".cache/ipython")
for path in sorted((root / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(
        notebook,
        timeout=600,
        kernel_name="career-ai-tf",
        resources={"metadata": {"path": str(root)}},
    ).execute()
    nbformat.write(notebook, path)
    print("Executed", path.name, flush=True)
