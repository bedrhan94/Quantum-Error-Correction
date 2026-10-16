"""Load the authors' code from original_source/ WITHOUT modifying it.

The file name contains a space ("epsilon codes.py"), so it is loaded with importlib from its
path.  ``load_appendix`` executes the hand transcription of Appendix A in a namespace that
contains the authors' classes (the listing depends on them).
"""
from __future__ import annotations

import hashlib
import importlib.util
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_FILE = ROOT / "original_source" / "epsilon codes.py"
APPENDIX_FILE = ROOT / "original_source" / "paper" / "appendix_A_transcribed.py"
PAPER_FILE = ROOT / "original_source" / "paper" / "1-s2.0-S1071579726000924-main.pdf"


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_original_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("epsilon_codes_original", ORIGINAL_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # the file guards its demo with  if __name__ == "__main__"
    return mod


def load_appendix(orig: types.ModuleType) -> types.SimpleNamespace:
    ns: dict = {"GaussianVector": orig.GaussianVector, "GaussianCodeN": orig.GaussianCodeN}
    code = compile(APPENDIX_FILE.read_text(encoding="utf-8"), str(APPENDIX_FILE), "exec")
    exec(code, ns)
    return types.SimpleNamespace(**{k: ns[k] for k in ("find_epsilon", "decode", "gaussian_modulo")})


def original_code_to_indices(code, q: int) -> np.ndarray:
    """Indices (our encoding) of the elements of an original GaussianCodeN."""
    out = []
    n = code.n
    for v in code.elements:
        idx = 0
        for j, c in enumerate(v.components):
            idx += (c.real * q + c.imag) * (q * q) ** j
        out.append(idx)
    return np.array(sorted(out), dtype=np.int64)


def original_vec_to_array(v) -> np.ndarray:
    return np.array([[c.real, c.imag] for c in v.components], dtype=np.int64)
