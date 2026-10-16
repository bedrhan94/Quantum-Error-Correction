#!/usr/bin/env bash
# Linux (WSL2) environment with PennyLane lightning.gpu (cuStateVec) for the circuits that are too
# large for lightning.qubit on Windows.  Same package versions as the Windows venv, Python 3.12.
#   wsl -d Ubuntu -- bash /mnt/c/Users/<user>/Desktop/PennyLane/epsilon_qec_research/wsl/setup_wsl_gpu.sh
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$HOME/venvs/epsqec"
PY="$VENV/bin/python"

command -v uv >/dev/null || { echo "uv not found (https://docs.astral.sh/uv/)"; exit 1; }
[ -x "$PY" ] || uv venv "$VENV" --python 3.12
uv pip install --python "$PY" torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install --python "$PY" pennylane==0.45.1 pennylane-lightning==0.45.0 pennylane-lightning-gpu==0.45.0 \
    numpy==2.4.6 scipy==1.18.0 matplotlib==3.11.0 psutil==7.2.2 pypdf==6.14.2 pytest==9.1.1
uv pip install --python "$PY" -e "$PROJ"
"$PY" "$PROJ/wsl/verify_wsl_gpu.py"
