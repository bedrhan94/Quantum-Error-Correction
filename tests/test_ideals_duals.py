"""Ideal membership, sizes, Hermitian duals (both definitions), Lemma 1, Tables 1-2."""
import math

import numpy as np
import pytest

from epsqec.css import PAPER_EXAMPLES, analyze_principal_pair, analyze_z9_table_row
from epsqec.css.examples import Z9_CLAIMS
from epsqec.decoder.epsilon_decoder import membership_oracle
from epsqec.ideals import AdditiveCode, euclidean_dual, hermitian_dual, hermitian_dual_def6, orthogonal_exhaustive
from epsqec.ring import GaussianRing


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_sizes_by_enumeration_match_paper(key):
    pe = PAPER_EXAMPLES[key]
    _, rep = analyze_principal_pair(pe.q, pe.alpha1, pe.alpha2)
    assert rep["size_C1_enumerated"] == pe.claimed["size_C1"]
    assert rep["size_C2_enumerated"] == pe.claimed["size_C2"]
    assert rep["K"] == pe.claimed["K"]
    assert rep["C1_subset_C2"] and rep["C1_is_R_ideal"] and rep["C2_is_R_ideal"]


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_true_hermitian_dual_containment_and_size(key):
    pe = PAPER_EXAMPLES[key]
    pair, rep = analyze_principal_pair(pe.q, pe.alpha1, pe.alpha2)
    assert rep["size_C2_dual_true"] == pe.claimed["size_dual"]
    assert rep["dual_true_subset_C1"]
    assert rep["C2_times_dual_true_eq_R"] and rep["double_dual_equals_C2"]
    assert rep["trace_dual_equals_hermitian_dual"]


def test_membership_oracles_agree_exhaustive():
    R = GaussianRing(85)
    for alpha in [(7, 6), (2, 1), (17, 51)]:
        C = AdditiveCode.principal(R, alpha)
        tb, _ = membership_oracle("bitmap", C)
        ta, _ = membership_oracle("algebraic", C, alpha)
        ts, _ = membership_oracle("pyset", C)
        for x in R.elements():
            assert tb(x) == ta(x) == ts(x) == bool(C.mask[R.index(x)])


def test_dual_orthogonal_exhaustive_all_pairs():
    pe = PAPER_EXAMPLES["Z25"]
    pair, _ = analyze_principal_pair(pe.q, pe.alpha1, pe.alpha2)
    assert orthogonal_exhaustive(pair.C2, pair.C2_dual)


def test_euclidean_dual_is_not_contained_in_C1():
    """The conjugation matters: the plain (Euclidean) dual of <2+i> is not inside <3+4i>."""
    R = GaussianRing(25)
    C1, C2 = AdditiveCode.principal(R, (3, 4)), AdditiveCode.principal(R, (2, 1))
    assert not euclidean_dual(C2).issubset(C1)


@pytest.mark.definition_consistency
@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_definition6_dual_satisfies_examples_containment(key):
    """Examples 6-7 state C2^perpH <= C1 (computed as an annihilator).  Is that still true when
    C2^perpH is taken from Definition 6 (<sigma(alpha2)>)?  -> consistency of the paper's definitions."""
    pe = PAPER_EXAMPLES[key]
    R = GaussianRing(pe.q)
    D6 = hermitian_dual_def6(R, pe.alpha2)
    C1 = AdditiveCode.principal(R, pe.alpha1)
    assert D6.issubset(C1), f"<sigma(alpha2)> has {D6.size} elements and is not inside C1 (|C1|={C1.size})"


@pytest.mark.paper_claim
def test_paper_lemma1_property2_under_definition6():
    """Lemma 1(2): |C| |C^perpH| = |R_Q| with C^perpH = <sigma(alpha)> (Definition 6)."""
    R = GaussianRing(25)
    C = AdditiveCode.principal(R, (2, 1))
    D6 = hermitian_dual_def6(R, (2, 1))
    assert C.size * D6.size == R.size, f"{C.size} * {D6.size} != {R.size}"


@pytest.mark.definition_consistency
def test_lemma1_property1_under_true_dual():
    """Lemma 1(1) read with the orthogonal complement (the dual of Examples 6-7), not Definition 6."""
    R = GaussianRing(25)
    alpha = (0, 1)  # a unit: N = 1
    assert math.gcd(int(R.norm(R.elem(*alpha))), 25) == 1
    C = AdditiveCode.principal(R, alpha)
    D = hermitian_dual(C)
    sigD = AdditiveCode.from_indices(R, 1, R.index(R.conj(D.vectors()[:, 0, :])))
    assert sigD == C, f"sigma(C^perpH) has {sigD.size} elements, C has {C.size}"


@pytest.mark.paper_claim
def test_paper_lemma1_property1_under_definition6():
    """Lemma 1(1) literally (C^perpH = <sigma(alpha)>): sigma(C^perpH) = C when gcd(N(alpha), q) = 1."""
    R = GaussianRing(25)
    for alpha in R.elements():
        if math.gcd(int(R.norm(alpha)), 25) != 1:
            continue
        C = AdditiveCode.principal(R, alpha)
        D6 = hermitian_dual_def6(R, alpha)
        sigD = AdditiveCode.from_indices(R, 1, R.index(R.conj(D6.vectors()[:, 0, :])))
        assert sigD == C


@pytest.mark.paper_claim
def test_paper_lemma1_property3_under_definition6():
    """Lemma 1(3) literally: C1 <= C2  =>  C2^perpH <= C1^perpH with C^perpH = <sigma(alpha)>."""
    R = GaussianRing(25)
    a1, a2 = (3, 4), (2, 1)  # Example 7: C1 = <3+4i> <= C2 = <2+i>
    assert AdditiveCode.principal(R, a1).issubset(AdditiveCode.principal(R, a2))
    D1, D2 = hermitian_dual_def6(R, a1), hermitian_dual_def6(R, a2)
    assert D2.issubset(D1), f"|<sigma(alpha2)>| = {D2.size} is not inside |<sigma(alpha1)>| = {D1.size}"


# Reclassified (review A4): Z_9 has prime divisor 3 = 3 (mod 4), i.e. it lies OUTSIDE the paper's
# own hypothesis; the table row is still inconsistent, so the FAIL is kept with this class.
@pytest.mark.paper_claim
@pytest.mark.outside_hypothesis
def test_paper_table1_z9_dual_size():
    r = analyze_z9_table_row()
    assert r["size_C2_dual_true"] == Z9_CLAIMS["size_dual"], \
        f"computed {r['size_C2_dual_true']}, Table 1 says 3 (Z9: 3 = 3 mod 4, outside the hypothesis)"


@pytest.mark.paper_claim
@pytest.mark.outside_hypothesis
def test_paper_table2_z9_K_equals_theorem4_formula():
    r = analyze_z9_table_row()
    assert r["K_theorem4_formula"] == Z9_CLAIMS["K_table2"], \
        f"|C2|/|C1| = {r['K_theorem4_formula']}, Table 2 says K = 1 (Z9 outside the hypothesis)"


@pytest.mark.paper_claim
@pytest.mark.parametrize("key", ["Z25", "Z325"])
def test_paper_printed_dual_generators(key):
    pe = PAPER_EXAMPLES[key]
    R = GaussianRing(pe.q)
    assert AdditiveCode.principal(R, pe.claimed["dual_generator"]) == hermitian_dual(AdditiveCode.principal(R, pe.alpha2))
