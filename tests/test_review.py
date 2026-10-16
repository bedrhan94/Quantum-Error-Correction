"""Tests added for the second-author review (A1, A3, B4, C1, C2).  Mathematical facts are in
TestMathematicalClaims (marker `math`), checks of this project's code in TestImplementation."""
import numpy as np
import pytest

from epsqec.css import PAPER_EXAMPLES
from epsqec.css.build import build
from epsqec.decoder import greedy_transversal
from epsqec.ideals import (AdditiveCode, hermitian_dual, hermitian_dual_closed_form, hermitian_dual_def6,
                           trace_dual)
from epsqec.ring import GaussianRing, factorize, zi
from epsqec.stabilizer import QuditSpace, RingCSSCode

Z5N4 = {"key": "Z5n4", "q": 5, "eps": "greedy",
        "C2_generators": [[[3, 4], [3, 1], [1, 2], [0, 2]], [[0, 1], [0, 3], [3, 4], [4, 4]], [[3, 1], [1, 2], [4, 1], [2, 1]]],
        "C1_generators": [[[4, 3], [1, 3], [3, 0], [0, 1]], [[3, 1], [2, 1], [1, 0], [0, 2]], [[2, 4], [3, 4], [4, 0], [0, 3]],
                          [[1, 2], [4, 2], [2, 0], [0, 4]], [[0, 3], [0, 0], [0, 0], [2, 1]]]}


def divisors(q):
    out = [(1, 0)]
    for p, e in factorize(q).items():
        pi = zi.gaussian_prime_above(p)
        pib = zi.conj(pi)
        new = []
        for d in out:
            for i in range(e + 1):
                for j in range(e + 1):
                    x = d
                    for _ in range(i):
                        x = zi.mul(x, pi)
                    for _ in range(j):
                        x = zi.mul(x, pib)
                    new.append(x)
        out = new
    return out


def ideals(q):
    R = GaussianRing(q)
    seen = {}
    for d in divisors(q):
        C = AdditiveCode.principal(R, d)
        seen.setdefault(C.mask.tobytes(), (d, C))
    return R, list(seen.values())


@pytest.mark.math
class TestMathematicalClaims:
    @pytest.mark.parametrize("q", [25, 65, 85, 125, 325])
    def test_closed_form_dual_equals_annihilator_all_ideals(self, q):
        """C^perpH = Ann(sigma(alpha)) = <sigma(q / gcd(alpha, q))>  for every ideal of Z_q[i]."""
        R, ids = ideals(q)
        for d, C in ids:
            assert hermitian_dual_closed_form(R, d) == hermitian_dual(C), (q, d)

    def test_closed_form_random_generators(self):
        R = GaussianRing(85)
        rng = np.random.default_rng(3)
        for x in R.elements()[rng.integers(0, R.size, 150)]:
            assert hermitian_dual_closed_form(R, x) == hermitian_dual(AdditiveCode.principal(R, x))

    def test_definition6_coincides_only_for_5_in_Z25(self):
        """<sigma(alpha)> = C^perpH  <=>  Ann(alpha) = <alpha>; among the ideals of Z_25[i] only <5>."""
        R, ids = ideals(25)
        hits = [d for d, C in ids if hermitian_dual_def6(R, d) == hermitian_dual(C)]
        assert [AdditiveCode.principal(R, d) for d in hits] == [AdditiveCode.principal(R, (5, 0))]

    @pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
    def test_definition6_fails_for_both_example_generators(self, key):
        pe = PAPER_EXAMPLES[key]
        R = GaussianRing(pe.q)
        for a in (pe.alpha1, pe.alpha2):
            assert hermitian_dual_def6(R, a) != hermitian_dual(AdditiveCode.principal(R, a)), (key, a)

    @pytest.mark.parametrize("key,a2", [("Z25", (2, 1)), ("Z325", (3, 2))])
    def test_printed_condition_with_conjugate_is_the_true_dual(self, key, a2):
        """Examples 6-7 print {z : z * conj(alpha2) = 0 (mod q)} (bar visible in the PDF) - correct."""
        q = PAPER_EXAMPLES[key].q
        R = GaussianRing(q)
        E = R.elements()
        printed = AdditiveCode.from_indices(R, 1, R.index(E[R.is_zero(R.mul(E, R.conj(R.elem(*a2))))]))
        no_bar = AdditiveCode.from_indices(R, 1, R.index(E[R.is_zero(R.mul(E, R.elem(*a2)))]))
        true = hermitian_dual(AdditiveCode.principal(R, a2))
        assert printed == true and no_bar != true

    def test_additive_non_module_code_breaks_hermitian_cardinality(self):
        """B4: for C = Z_q * 1 (additive, not an R-module) |C||C^perpH| != |R| but |C||C^perpTr| = |R|."""
        R = GaussianRing(25)
        C = AdditiveCode.zq_span(R, 1, [np.array([[1, 0]])])
        assert not C.is_R_module()
        assert hermitian_dual(C).size == 1 and trace_dual(C).size == 25
        assert C.size * trace_dual(C).size == R.size != C.size * hermitian_dual(C).size

    def test_additive_pair_needs_left_trace_dual_for_K(self):
        """Additive pair C1 = Z_q*1 < C2 = Z_q*1 + Z_q*5i: Hermitian dual gives dim 25 != K = 5;
        the LEFT trace dual {v : Tr<v,c>_H = 0} gives a commuting group with dim K; the right trace
        dual does not commute (the paper's Tr(a+bi) = a+b is not sigma-invariant)."""
        R = GaussianRing(25)
        C1 = AdditiveCode.zq_span(R, 1, [np.array([[1, 0]])])
        C2 = AdditiveCode.zq_span(R, 1, [np.array([[1, 0]]), np.array([[0, 5]])])
        sp = QuditSpace(R, 1)
        assert RingCSSCode(sp, C1, C2, hermitian_dual(C2)).dim_structural() == 25  # != K
        good = RingCSSCode(sp, C1, C2, trace_dual(C2, side="left"))
        assert good.commutation_exhaustive()["noncommuting_pairs"] == 0
        assert good.dim_structural() == C2.size // C1.size == 5
        right = RingCSSCode(sp, C1, C2, trace_dual(C2, side="right"))
        assert right.commutation_exhaustive()["noncommuting_pairs"] > 0

    def test_trace_sides_agree_for_ideals(self):
        R, ids = ideals(25)
        for d, C in ids:
            assert trace_dual(C, "left") == trace_dual(C, "right") == hermitian_dual(C)

    @pytest.mark.parametrize("q", [25, 65, 85])
    def test_zreading_equivalence_all_valid_pairs(self, q):
        """(eps - eps) /\\ C1^perpH = {0}  <=>  Z(eps) gives |eps| distinct syndromes (greedy eps)."""
        R, ids = ideals(q)
        sp = QuditSpace(R, 1)
        duals = [hermitian_dual(C) for _, C in ids]
        n = 0
        for i1, (d1, C1) in enumerate(ids):
            for i2, (d2, C2) in enumerate(ids):
                if i1 == i2 or not C1.issubset(C2) or C1.size == C2.size or not duals[i2].issubset(C1):
                    continue
                eps = greedy_transversal(C2, C1)
                diffs = R.sub(eps[:, None], eps[None, :]).reshape(-1, 1, 2)
                nz = ~np.all(diffs.reshape(-1, 2) == 0, axis=1)
                cond = not bool(duals[i1].contains(diffs[nz]).any())
                syn = RingCSSCode(sp, C1, C2, duals[i2]).xsyn(eps)
                distinct = len({tuple(r) for r in syn.tolist()})
                assert cond == (distinct == len(eps)), (q, d1, d2)
                n += 1
        assert n > 0

    @pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
    def test_zreading_holds_for_paper_examples(self, built, key):
        b = built(key)
        assert len({tuple(r) for r in b.code.xsyn(b.eps).tolist()}) == len(b.eps)

    def test_zreading_fails_for_Z5n4_greedy(self):
        """Counter-example to a general Z-reading: Z_5[i]^4, greedy eps (25 representatives)."""
        b = build(Z5N4)
        distinct = len({tuple(r) for r in b.code.xsyn(b.eps).tolist()})
        assert distinct < len(b.eps)

    @pytest.mark.parametrize("key", ["Z25", "Z85"])
    def test_convention_2re_gives_same_structure(self, key):
        """C2: with Tr = 2a (chi = omega^(2 Re)) the duals, K, commutation and Prop. 5 results agree."""
        a, c = build({"key": key}), build({"key": key, "trace_convention": "2re"})
        assert trace_dual(c.C2) == c.D_true == a.D_true
        assert c.code.commutation_exhaustive()["noncommuting_pairs"] == 0
        assert c.code.dim_structural() == a.code.dim_structural()
        assert not np.any(c.code.zsyn(c.C2.vectors()))  # X-reading still all-zero


class TestImplementation:
    def test_trace_conventions(self):
        R1, R2 = GaussianRing(25), GaussianRing(25, trace_convention="2re")
        x = np.array([3, 7])
        assert int(R1.trace(x)) == 10 and int(R2.trace(x)) == 6
        with pytest.raises(ValueError):
            GaussianRing(25, trace_convention="x")

    @pytest.mark.parametrize("conv", ["paper", "2re"])
    def test_pauli_relation_under_both_conventions(self, conv):
        b = build({"key": "Z25", "trace_convention": conv})
        sp = b.space
        rng = np.random.default_rng(1)
        psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
        for _ in range(50):
            u, v = sp.vecs[rng.integers(sp.dim, size=2)]
            assert np.allclose(sp.apply_Z(v, sp.apply_X(u, psi)), sp.chi_pair(v, u) * sp.apply_X(u, sp.apply_Z(v, psi)))
