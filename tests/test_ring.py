"""Ring operation tests for R_Q = Z_q[i] (exhaustive on small rings)."""
import math

import numpy as np
import pytest

from epsqec.ring import GaussianRing, zi


@pytest.mark.parametrize("q", [5, 13, 25])
def test_ring_axioms_exhaustive_pairs(q):
    R = GaussianRing(q)
    E = R.elements()
    X, Y = E[:, None], E[None, :]
    xy = R.mul(X, Y)
    assert np.array_equal(xy, R.mul(Y, X))
    assert np.array_equal(R.add(X, Y), R.add(Y, X))
    assert np.array_equal(R.conj(xy), R.mul(R.conj(X), R.conj(Y)))  # sigma multiplicative
    assert np.array_equal(R.norm(xy), np.mod(R.norm(X) * R.norm(Y), q))
    assert np.array_equal(R.conj(R.conj(E)), E)


@pytest.mark.parametrize("q", [5, 25])
def test_associativity_distributivity_exhaustive(q):
    R = GaussianRing(q)
    E = R.elements()
    for x in E[:: max(1, len(E) // 60)]:
        a = R.mul(R.mul(x[None, None], E[:, None]), E[None, :])
        b = R.mul(x[None, None], R.mul(E[:, None], E[None, :]))
        assert np.array_equal(a, b)
        l = R.mul(x[None, None], R.add(E[:, None], E[None, :]))
        r = R.add(R.mul(x[None, None], E[:, None]), R.mul(x[None, None], E[None, :]))
        assert np.array_equal(l, r)


def test_i_squared_and_norm():
    R = GaussianRing(25)
    assert np.array_equal(R.mul(R.elem(0, 1), R.elem(0, 1)), R.elem(-1, 0))
    assert int(R.norm(R.elem(3, 4))) == 0 and int(R.norm(R.elem(2, 1))) == 5


@pytest.mark.parametrize("q", [5, 13, 25, 65])
def test_units_norm_criterion_matches_brute_force(q):
    R = GaussianRing(q)
    E = R.elements()
    one = R.index(R.elem(1, 0))
    brute = np.array([(R.index(R.mul(x[None], E)) == one).any() for x in E])
    crit = np.array([math.gcd(int(n), q) == 1 for n in R.norm(E)])
    assert np.array_equal(brute, crit)


def test_trace_pairing_nondegenerate():
    R = GaussianRing(25)
    E = R.elements()
    tr = R.trace(R.mul(E[:, None], E[None, :]))
    assert np.all(np.any(tr[1:] != 0, axis=1))


def test_rejects_non_split_modulus():
    with pytest.raises(ValueError):
        GaussianRing(9)
    with pytest.raises(ValueError):
        GaussianRing(15)


def test_zi_gcd_and_division():
    assert zi.norm(zi.gcd((3, 4), (25, 0))) == 25
    assert zi.mul((2, 1), (2, 1)) == (3, 4)
    assert zi.divides((2, 1), (10, 5)) and not zi.divides((3, 4), (10, 0))
    assert zi.ideal_index_in_Zq((2, 1), 25) == 5 and zi.ideal_index_in_Zq((4, 7), 325) == 65
