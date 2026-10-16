"""The separately kept minimal fix of the authors' hermitian_dual() (original_source_fixed/)."""
import importlib.util
from pathlib import Path

import pytest

from epsqec.original_bridge import ORIGINAL_FILE, sha256

FIXED = Path(__file__).resolve().parents[1] / "original_source_fixed" / "epsilon_codes_fixed.py"


@pytest.fixture(scope="module")
def fixed():
    spec = importlib.util.spec_from_file_location("eps_fixed", FIXED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixed_double_dual_is_C(fixed):
    C = fixed.GaussianCodeN([(2, 1), (1, 0)], 5)
    DD = C.hermitian_dual().hermitian_dual()
    assert DD.elements == C.elements


def test_original_left_untouched():
    assert sha256(ORIGINAL_FILE) == "eb593509b063c6dd1d53c5ef2222a580c7957eb64407197c92ea4f7029e1ca2e"
    assert sha256(FIXED) != sha256(ORIGINAL_FILE)
