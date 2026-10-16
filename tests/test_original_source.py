"""Baseline: the authors' unchanged code (original_source/) against the independent implementation."""
import random

import numpy as np
import pytest

from epsqec.css import PAPER_EXAMPLES
from epsqec.ideals import AdditiveCode
from epsqec.original_bridge import ORIGINAL_FILE, load_appendix, load_original_module, original_code_to_indices, sha256
from epsqec.ring import GaussianRing

ORIGINAL_SHA256 = "eb593509b063c6dd1d53c5ef2222a580c7957eb64407197c92ea4f7029e1ca2e"

pytestmark = pytest.mark.original_source


@pytest.fixture(scope="module")
def orig():
    return load_original_module()


def test_original_file_unchanged():
    assert sha256(ORIGINAL_FILE) == ORIGINAL_SHA256


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_original_sets_equal_independent(orig, key):
    pe = PAPER_EXAMPLES[key]
    R = GaussianRing(pe.q)
    for alpha in (pe.alpha1, pe.alpha2):
        Co = orig.GaussianCodeN([alpha], pe.q)
        assert np.array_equal(original_code_to_indices(Co, pe.q), AdditiveCode.principal(R, alpha).indices)


def test_original_decode_example8(orig):
    q = 25
    C2, C1 = orig.GaussianCodeN([(2, 1)], q), orig.GaussianCodeN([(3, 4)], q)
    eps = [orig.GaussianVector([p], q) for p in [(0, 0), (2, 1), (4, 2), (6, 3), (8, 4)]]
    e, c = orig.decode(orig.GaussianVector([(11, 8)], q), eps, C1)
    assert repr(e) == "(8+4i)" and repr(c) == "(3+4i)"
    app = load_appendix(orig)
    e2, c2 = app.decode(orig.GaussianVector([(11, 8)], q), eps, C1, C2)
    assert (e2, c2) == (e, c)


def test_original_run_simulation_seeded_reproducible(orig):
    random.seed(1)
    a = orig.run_simulation(25, [(2, 1)], [(3, 4)], "Z25", trials=500)
    random.seed(1)
    b = orig.run_simulation(25, [(2, 1)], [(3, 4)], "Z25", trials=500)
    assert a == b and a["success"] == 500


def test_original_hermitian_dual_twice_returns_C(orig):
    """(C^perp)^perp = C over a Frobenius ring.  The authors' hermitian_dual() returns an object
    whose .generator is the zero vector, so a second call returns all of R^2 (latent bug)."""
    C = orig.GaussianCodeN([(2, 1), (1, 0)], 5)
    DD = C.hermitian_dual().hermitian_dual()
    assert DD.size() == C.size(), f"double dual has {DD.size()} elements, C has {C.size()}"
