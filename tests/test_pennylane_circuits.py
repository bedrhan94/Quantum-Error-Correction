"""PennyLane gate-level checks (Z_25[i], 10 data qubits)."""
import numpy as np
import pytest

qml = pytest.importorskip("pennylane")
pytestmark = pytest.mark.pennylane

from epsqec.pl_circuits import RingCircuits  # noqa: E402


def _state(nw, body, dev="lightning.qubit"):
    d = qml.device(dev, wires=nw)

    @qml.qnode(d)
    def c():
        body()
        return qml.state()

    return np.asarray(c())


def test_adder_valid_subspace_no_leakage():
    q, m = 25, 5
    wires, work = list(range(m)), [m, m + 1]
    for k in (1, 7, 24):
        U = qml.matrix(qml.Adder(k, wires, mod=q, work_wires=work), wire_order=wires + work)
        for x in range(q):
            out = int(np.argmax(np.abs(U[:, x << 2])))
            assert out >> 2 == (x + k) % q and out & 3 == 0


def test_X_and_Z_gates_match_reference(built):
    b = built("Z25")
    sp = b.space
    rc = RingCircuits(25)
    rng = np.random.default_rng(0)
    for u in [np.array([3, 4]), np.array([1, 18]), np.array([10, 5]), np.array([24, 1])]:
        psi = rng.normal(size=sp.dim) + 1j * rng.normal(size=sp.dim)
        psi /= np.linalg.norm(psi)
        init = np.zeros(2 ** rc.L.n_wires, dtype=complex)
        init.reshape(2 ** 10, 4)[:, 0] = rc.embed_ring_state(psi)
        st = _state(rc.L.n_wires, lambda: (qml.StatePrep(init, wires=range(rc.L.n_wires)), rc.X(u)))
        out, leak = rc.extract_ring_state(st.reshape(2 ** 10, 4)[:, 0])
        assert leak < 1e-12 and np.allclose(out, sp.apply_X(u[None], psi))
        st = _state(rc.L.n_wires, lambda: (qml.StatePrep(init, wires=range(rc.L.n_wires)), rc.Z(u)))
        out, _ = rc.extract_ring_state(st.reshape(2 ** 10, 4)[:, 0])
        assert np.allclose(out, sp.apply_Z(u[None], psi))


def test_z_syndrome_circuit_matches_algebra(built):
    b = built("Z25")
    code = b.code
    rc = RingCircuits(25, zgens=code.zgens)
    nw = rc.L.n_wires
    for a in [np.array([1, 0]), np.array([0, 1]), np.array([2, 1]), np.array([3, 3])]:
        init = np.zeros(2 ** nw, dtype=complex)
        init.reshape(2 ** 10, -1)[:, 0] = rc.embed_ring_state(b.space.basis_state(a[None]))
        st = _state(nw, lambda: (qml.StatePrep(init, wires=range(nw)), rc.z_syndrome(0)))
        M = st.reshape(2 ** 10, -1)
        j = int(np.argmax((np.abs(M) ** 2).sum(0)))
        rest = nw - 10
        bits = [(j >> (rest - 1 - (w - 10))) & 1 for w in rc.L.z_anc[0]]
        sprime = int("".join(map(str, bits)), 2)
        assert rc.z_syndrome_value(0, sprime) == int(code.zsyn(a[None, None])[0, 0])
