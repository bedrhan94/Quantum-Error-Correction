"""Generalised Pauli operators, stabilizer commutation, group order, code dimension, recovery."""
import numpy as np
import pytest

from epsqec.stabilizer import min_weight_transversal


def test_pauli_unitary_and_relation_exhaustive_z5(built):
    b = built("Z5_small")
    sp, R = b.space, b.ring
    I = np.eye(sp.dim)
    rng = np.random.default_rng(0)
    psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
    for u in sp.vecs:
        X = sp.sparse_X(u).toarray()
        assert np.allclose(X.conj().T @ X, I)
        for v in sp.vecs:
            lhs = sp.apply_Z(v, sp.apply_X(u, psi))
            rhs = sp.chi_pair(v, u) * sp.apply_X(u, sp.apply_Z(v, psi))
            assert np.allclose(lhs, rhs)


@pytest.mark.parametrize("key", ["Z25", "Z85"])
def test_pauli_relation_sampled(built, key):
    b = built(key)
    sp = b.space
    rng = np.random.default_rng(1)
    psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
    for _ in range(200):
        u, v = sp.vecs[rng.integers(sp.dim, size=2)]
        assert np.allclose(sp.apply_Z(v, sp.apply_X(u, psi)), sp.chi_pair(v, u) * sp.apply_X(u, sp.apply_Z(v, psi)))
        assert len(np.unique(sp.gather_X(u))) == sp.dim
        assert np.allclose(np.abs(sp.z_phase(v)), 1)


@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_stabilizers_commute_true_dual(built, key):
    assert built(key).code.commutation_exhaustive()["noncommuting_pairs"] == 0


@pytest.mark.definition_consistency
@pytest.mark.parametrize("key", ["Z25", "Z85"])
def test_theorem4_stabilizers_commute_with_definition6_dual(built, key):
    """Stabilizers of Theorem 4 built with Definition 6's dual.  NOT a counterexample to Theorem 4
    (its hypothesis C2^perpH <= C1 fails for this dual); it shows Definition 6 cannot be the dual
    the theorem and the examples use."""
    r = built(key).code_def6.commutation_exhaustive()
    assert r["noncommuting_pairs"] == 0, r


@pytest.mark.parametrize("key", ["Z5_small", "Z25", "Z85", "Z325"])
def test_code_dimension_equals_K(built, key):
    b = built(key)
    code = b.code
    K = b.C2.size // b.C1.size
    assert code.x_has_no_fixed_points()
    assert abs(code.dim_trace_formula() - K) < 1e-9
    assert code.dim_structural() == K
    if b.space.dim <= 625:
        assert code.dim_nullspace_dense() == K


@pytest.mark.parametrize("key", ["Z25", "Z85"])
def test_logical_states_orthonormal_and_stabilised(built, key):
    b = built(key)
    V = b.code.logical_states(b.eps)
    assert np.allclose(V.conj() @ V.T, np.eye(len(V)))
    for v in V:
        for u in b.code.xgens:
            assert np.allclose(b.space.apply_X(u, v), v)
        for z in b.code.zgens:
            assert np.allclose(b.space.apply_Z(z, v), v)


def test_group_order_z25(built):
    b = built("Z25")
    sp, code = b.space, b.code
    rng = np.random.default_rng(2)
    r = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
    prints = {tuple(np.round(sp.apply_X(u, sp.apply_Z(v, r)), 9)) for u in code.C1.vectors() for v in code.Zg.vectors()}
    assert len(prints) == b.C1.size * b.D_true.size


@pytest.mark.paper_claim
@pytest.mark.parametrize("key", ["Z25", "Z85", "Z325"])
def test_paper_proposition5_distinct_syndromes_for_X_errors(built, key):
    """Prop. 5, X-type reading (errors X(e), e in eps subset C2 - the reading of Def. 10 / Remark 4 /
    Example 8): distinct e_i, e_j in eps induce distinct stabilizer syndromes.  The Z-type reading
    is tested separately (tests/test_review.py)."""
    b = built(key)
    s = b.code.zsyn(b.eps)
    sx = np.zeros((len(b.eps), len(b.code.xgens)), dtype=int)  # X(e) commutes with every X(u)
    pats = {tuple(r) for r in np.concatenate([s, sx], axis=1).tolist()}
    assert len(pats) == len(b.eps), f"X-reading: {len(pats)} distinct syndrome(s) for |eps| = {len(b.eps)}"


def test_x_errors_in_C2_are_logical_operators(built):
    """Counter-example behind the failure above, checked on states: X(2+i) maps psi_0 to an
    orthogonal code state and leaves every syndrome at 0."""
    b = built("Z25")
    sp, code = b.space, b.code
    V = code.logical_states(b.eps)
    phi = sp.apply_X(np.array([[2, 1]]), V[0])
    z, x = code.measure_state_syndrome(phi)
    assert z == (0,) and x == (0,)
    assert abs(np.vdot(V[0], phi)) < 1e-12 and abs(abs(np.vdot(V[1], phi)) - 1) < 1e-12


def test_alternative_design_recovers_all_correctable_errors_z25(built):
    """ALTERNATIVE DESIGN (not the paper's): X(a)Z(b), a in T_X, b in T_Z."""
    b = built("Z25")
    sp, code, R = b.space, b.code, b.ring
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // b.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // b.C1_dual.size)
    lx = {int(k): a for k, a in zip(code.zsyn_key(TX), TX)}
    lz = {int(k): f for k, f in zip(code.xsyn_key(TZ), TZ)}
    V = code.logical_states(b.eps)
    rng = np.random.default_rng(3)
    c = rng.normal(size=5) + 1j * rng.normal(size=5)
    psi = (c / np.linalg.norm(c)) @ V
    for a in TX:
        for f in TZ:
            phi = sp.apply_X(a, sp.apply_Z(f, psi))
            zs, xs = code.measure_state_syndrome(phi)
            ka = sum(v * 25 ** j for j, v in enumerate(zs))
            kz = sum(v * 25 ** j for j, v in enumerate(xs))
            rec = sp.apply_X(R.neg(lx[ka]), sp.apply_Z(R.neg(lz[kz]), phi))
            assert abs(abs(np.vdot(psi, rec)) - 1) < 1e-9
    kl = code.knill_laflamme(V, [lambda s, a=a, f=f: sp.apply_X(a, sp.apply_Z(f, s)) for a in TX for f in TZ])
    assert kl["max_deviation"] < 1e-9
