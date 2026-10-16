"""Layout B (split coordinates) - gate-level circuits.  Dense matrices only for <= 625-dim checks."""
import numpy as np
import pytest

qml = pytest.importorskip("pennylane")

from epsqec.css.build import build  # noqa: E402
from epsqec.pl_circuits.cycle import LayoutB, cycle_program, run_native, run_segmented  # noqa: E402
from epsqec.pl_circuits.split_layout import SplitCircuits, SplitLayout, dft_matrix, shift_matrix  # noqa: E402

Z65 = {"key": "Z65", "q": 65, "alpha1": [4, 7], "alpha2": [3, 2], "eps": "multiples"}


def _state(n, body):
    dev = qml.device("lightning.qubit", wires=n)

    @qml.qnode(dev)
    def c():
        body()
        return qml.state()

    return np.asarray(c())


@pytest.mark.math
class TestMathematicalClaims:
    @pytest.mark.parametrize("spec", [{"key": "Z25"}, Z65])
    def test_split_map_is_ring_isomorphism_exhaustive(self, spec):
        b = build(spec)
        R, lay = b.ring, SplitLayout(b.ring)
        E = R.elements()
        assert len(np.unique(lay.basis_index(E))) == R.size
        assert np.array_equal(lay.from_digits(lay.digits_of(E)), E)
        for x in E[:: max(1, R.size // 80)]:
            prod = lay.split(R.mul(x[None], E))
            for B, sx, sy, sp in zip(lay.blocks, lay.split(x), lay.split(E), prod):
                assert np.array_equal(np.mod(sx[0] * sy[0], B["pe"]), sp[0])
                assert np.array_equal(np.mod(sx[1] * sy[1], B["pe"]), sp[1])

    @pytest.mark.parametrize("spec", [{"key": "Z25"}, Z65, {"key": "Z85"}])
    def test_ideals_are_digit_products_and_K(self, spec):
        b = build(spec)
        sc = SplitCircuits(b)  # asserts the product structure and K = prod(label radices)
        assert sc.K == b.C2.size // b.C1.size

    def test_conjugation_swaps_components(self):
        b = build({"key": "Z25"})
        R, lay = b.ring, SplitLayout(b.ring)
        E = R.elements()
        for (U, V), (Uc, Vc) in zip(lay.split(E), lay.split(R.conj(E))):
            assert np.array_equal(U, Vc) and np.array_equal(V, Uc)


class TestImplementation:
    def test_small_blocks_are_valid_subspace_preserving(self):
        for p, m in ((5, 3), (13, 4), (17, 5)):
            for c in range(p):
                S = shift_matrix(p, m, c)
                assert np.allclose(S.T @ S, np.eye(2 ** m)) and np.allclose(S[p:, :p], 0)
            F = dft_matrix(p, m)
            assert np.allclose(F.conj().T @ F, np.eye(2 ** m)) and np.allclose(F[p:, :p], 0)

    @pytest.mark.parametrize("conv", ["paper", "2re"])
    @pytest.mark.parametrize("spec", [{"key": "Z25"}, Z65])
    def test_X_Z_gates_match_reference_and_commutation(self, spec, conv):
        b = build({**spec, "trace_convention": conv})
        R, sp = b.ring, b.space
        sc = SplitCircuits(b)
        lay = sc.L
        rng = np.random.default_rng(2)
        psi = rng.normal(size=R.size) + 1j * rng.normal(size=R.size)
        psi /= np.linalg.norm(psi)
        init = np.kron(lay.embed(psi), np.eye(2 ** (sc.n_wires - lay.n_qubits))[0])
        for _ in range(3):
            u, v = R.elements()[rng.integers(0, R.size, 2)]
            zx = _state(sc.n_wires, lambda: (qml.StatePrep(init, wires=range(sc.n_wires)), sc.X(u), sc.Z(v)))
            xz = _state(sc.n_wires, lambda: (qml.StatePrep(init, wires=range(sc.n_wires)), sc.Z(v), sc.X(u)))
            ref = sp.apply_Z(v[None], sp.apply_X(u[None], psi))
            assert np.allclose(zx.reshape(2 ** lay.n_qubits, -1)[:, 0], lay.embed(ref))
            # Z(v) X(u) = chi(<v,u>_H) X(u) Z(v)
            assert np.allclose(zx, sp.chi_pair(v[None], u[None]) * xz)

    def test_radix_p_fourier_equals_dense_dft25(self):
        b = build({"key": "Z25"})
        sc = SplitCircuits(b)
        P = [P for P in sc.parts if P.kind == "X" and P.f == 2][0]
        w = [x for d in P.digits for x in d.wires]
        F = np.exp(2j * np.pi * np.outer(np.arange(25), np.arange(25)) / 25) / 5
        for j in (0, 1, 7, 13, 24):
            j1, j0 = divmod(j, 5)

            def body():
                for d, val in ((P.digits[1], j1), (P.digits[0], j0)):
                    for t, x in enumerate(d.wires):
                        if (val >> (d.m - 1 - t)) & 1:
                            qml.PauliX(x)
                sc.fourier_g(P)

            st = _state(sc.n_wires, body).reshape([2] * sc.n_wires)
            st = np.moveaxis(st, w, list(range(len(w)))).reshape(2 ** len(w), -1)[:, 0]
            got = np.zeros(25, dtype=complex)
            for k in range(25):
                k1, k0 = divmod(k, 5)  # output: lo holds k1, hi holds k0
                got[k] = st[(k1 << 3) | k0]
            assert np.allclose(got, F[j])

    @pytest.mark.parametrize("spec", [{"key": "Z25"}, Z65])
    def test_encoder_gate_level(self, spec):
        b = build(spec)
        sc = SplitCircuits(b)
        lay = sc.L
        for j in range(sc.K):
            st = _state(sc.n_wires, lambda: (sc.prepare_basis(j), sc.encode())).reshape(2 ** lay.n_qubits, -1)
            assert np.allclose(st[:, 1:], 0)
            ref = lay.embed(b.code.logical_states(sc.canonical_t(j).reshape(1, 1, 2))[0])
            assert abs(abs(np.vdot(ref, st[:, 0])) ** 2 - 1) < 1e-12

    def test_cycle_segmented_matches_native_and_detects_missing_correction(self):
        b = build({"key": "Z25"})
        L = LayoutB(b, reuse=True)
        a, f = L.TX[2], L.TZ[7]
        amps = np.ones(L.K) / np.sqrt(L.K)
        prog = cycle_program(L, a, f, amps, "XZ")
        ps, info = run_segmented(prog, L.n_wires, L.out_wires())
        assert abs(ps[0] - 1) < 1e-12 and info["discarded_probability"] < 1e-20
        pn = run_native(prog, L.n_wires, L.out_wires())
        assert np.allclose(ps, pn, atol=1e-10)
        bad = [it for it in prog if not (it[0] == "cond" and it[2] == ["X0"])]  # drop the Z correction
        pb, _ = run_segmented(bad, L.n_wires, L.out_wires())
        assert pb[0] < 1e-9

    def test_ancilla_keeps_measured_value_without_reset(self):
        """Without reset the measured ancilla stays in the measured basis state (not |0>)."""
        b = build({"key": "Z25"})
        L = LayoutB(b, reuse=False)
        a = L.TX[1]
        prog = [("ops", lambda: (L.prep(0), L.X(a)))] + L.round_program("Z")[:2]
        P = [P for P in L.sc.parts if P.kind == "Z"][0]
        wires = [w for d in P.digits for w in d.wires]
        probs, info = run_segmented(prog, L.n_wires, wires)
        rec = info["records"][0]["Z0"]
        assert rec != 0 and probs[rec] > 1 - 1e-12
