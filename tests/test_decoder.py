"""Coset partition and exhaustive epsilon-decoding tests (independent implementation)."""
import numpy as np
import pytest

from epsqec.css import PAPER_EXAMPLES
from epsqec.decoder import EpsilonDecoder, check_transversal, greedy_transversal, multiples_transversal
from epsqec.decoder.direct import DirectCosetDecoder
from epsqec.ideals import AdditiveCode
from epsqec.ring import GaussianRing


def _pair(key):
    pe = PAPER_EXAMPLES[key]
    R = GaussianRing(pe.q)
    return pe, R, AdditiveCode.principal(R, pe.alpha1), AdditiveCode.principal(R, pe.alpha2)


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_coset_partition_all_transversals(key):
    pe, R, C1, C2 = _pair(key)
    sets = [greedy_transversal(C2, C1), multiples_transversal(R, pe.alpha2, C2.size // C1.size)]
    sets += [R.reduce(np.array(v))[:, None, :] for v in pe.eps_sets.values()]
    for eps in sets:
        rep = check_transversal(eps, C2, C1)
        assert rep.valid, rep.as_dict()


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_exhaustive_decoding_every_word(key):
    pe, R, C1, C2 = _pair(key)
    eps = multiples_transversal(R, pe.alpha2, C2.size // C1.size)
    dec = EpsilonDecoder(C2, C1, eps)
    Y = R.all_vectors(1)
    M = dec.candidate_matrix(Y)
    n = M.sum(axis=1)
    assert np.all(n[C2.mask] == 1), "every y in C2 has exactly one representative"
    assert np.all(n[~C2.mask] == 0), "no y outside C2 is decoded"
    k = M[C2.mask].argmax(axis=1)
    assert C1.contains(R.sub(Y[C2.mask], dec.eps[k])).all()


def test_example8_y_11_8i():
    pe, R, C1, C2 = _pair("Z25")
    dec = EpsilonDecoder(C2, C1, np.array(pe.eps_sets["paper_example7"])[:, None, :])
    r = dec.decode(np.array([[11, 8]]))
    assert r.status == "ok"
    assert R.fmt(r.e[0]) == "8+4i" and R.fmt(r.c[0]) == "3+4i"
    assert r.n_membership_tests == 1 + 5


def test_example5_y_2_i():
    pe, R, C1, C2 = _pair("Z25")
    dec = EpsilonDecoder(C2, C1, np.array(pe.eps_sets["paper_example4"])[:, None, :])
    r = dec.decode(np.array([[2, 1]]))
    assert R.fmt(r.e[0]) == "0+15i" and R.fmt(r.c[0]) == "2+11i"


def test_invalid_word_rejected_with_one_test():
    pe, R, C1, C2 = _pair("Z25")
    dec = EpsilonDecoder(C2, C1, multiples_transversal(R, pe.alpha2, 5))
    r = dec.decode(np.array([[1, 0]]))
    assert r.status == "not_in_C2" and r.n_membership_tests == 1


def test_non_unique_detected_for_bad_eps():
    pe, R, C1, C2 = _pair("Z25")
    bad = R.reduce(np.array([[0, 0], [2, 1], [5, 10], [6, 3], [8, 4]]))[:, None, :]  # 5+10i in C1
    assert not check_transversal(bad, C2, C1).valid
    dec = EpsilonDecoder(C2, C1, bad)
    statuses = {dec.decode(y).status for y in C2.vectors()}
    assert "non_unique" in statuses


@pytest.mark.parametrize("oracle", ["bitmap", "pyset", "algebraic"])
def test_oracles_give_identical_decodes(oracle):
    pe, R, C1, C2 = _pair("Z85")
    eps = multiples_transversal(R, pe.alpha2, 17)
    ref = EpsilonDecoder(C2, C1, eps, oracle="bitmap", alpha1=pe.alpha1, alpha2=pe.alpha2)
    d = EpsilonDecoder(C2, C1, eps, oracle=oracle, alpha1=pe.alpha1, alpha2=pe.alpha2)
    for y in C2.vectors()[::7]:
        a, b = ref.decode(y), d.decode(y)
        assert a.status == b.status and np.array_equal(a.e, b.e)


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_direct_quotient_decoder_agrees(key):
    pe, R, C1, C2 = _pair(key)
    eps = multiples_transversal(R, pe.alpha2, C2.size // C1.size)
    dd = DirectCosetDecoder(pe.q, pe.alpha1, pe.alpha2, eps)
    dec = EpsilonDecoder(C2, C1, eps)
    for y in C2.vectors()[:: max(1, C2.size // 500)]:
        e, _ = dd.decode(y[0])
        assert np.array_equal(np.asarray(e).reshape(1, 2), dec.decode(y).e)
