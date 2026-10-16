"""Codes embedded into a qubit register, each with its ideal recovery written as isometries.

For a stabilizer code with K logical levels the ideal (syndrome-measure + Pauli-correct)
recovery followed by decoding is  rho_L = sum_s B_s^dag rho B_s  with
    B_s = E_s V      (D x K),  V = encoded logical basis, E_s = correction-class representative.
The B_s for all syndromes s span the valid subspace; population outside it (leakage out of the
embedded computational subspace) is lost and counted as an error.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..stabilizer import min_weight_transversal


@dataclass
class EmbeddedCode:
    name: str
    n_qubits: int
    K: int
    V: np.ndarray  # (K, 2^n) encoded logical basis
    B: np.ndarray  # (S, 2^n, K) recovery isometries
    valid: np.ndarray  # (2^n,) bool, embedded computational subspace
    info: dict = field(default_factory=dict)

    def completeness_error(self) -> float:
        """|| sum_s B_s B_s^dag - P_valid ||  (0 iff the B_s tile the valid subspace exactly)."""
        P = np.einsum("sdk,sek->de", self.B, self.B.conj())
        return float(np.abs(P - np.diag(self.valid.astype(float))).max())


def _ring_index_to_qubits(q: int) -> tuple[np.ndarray, int]:
    m = int(np.ceil(np.log2(q)))
    a, b = np.divmod(np.arange(q * q), q)
    return (a << m) | b, 2 * m


def ring_code_embedded(built) -> EmbeddedCode:
    """Z_q[i] ring code (n = 1), split register embedding (Section 6 of ring_circuits)."""
    sp, code, R = built.space, built.code, built.ring
    assert sp.n == 1
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // built.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // built.C1_dual.size)
    V = code.logical_states(built.eps)
    emb, nq = _ring_index_to_qubits(R.q)
    D = 2 ** nq
    Bs = []
    for a in TX:
        for f in TZ:
            W = np.stack([sp.apply_X(a, sp.apply_Z(f, v)) for v in V], axis=1)  # (q^2, K)
            Bq = np.zeros((D, len(V)), dtype=complex)
            Bq[emb] = W
            Bs.append(Bq)
    Vq = np.zeros((len(V), D), dtype=complex)
    Vq[:, emb] = V
    valid = np.zeros(D, dtype=bool)
    valid[emb] = True
    return EmbeddedCode(f"ring Z_{R.q}[i]", nq, len(V), Vq, np.array(Bs), valid,
                        {"|T_X|": len(TX), "|T_Z|": len(TZ), "hilbert_dim": sp.dim})


def modular_code_embedded(N: int = 625, K: int = 5, s: int = 5) -> EmbeddedCode:
    """Standard qudit CSS code over Z_N (Euclidean form): C1 = sK Z_N <= C2 = s Z_N,
    C2^perp = (N/s) Z_N <= C1.  Logical |j> = M^{-1/2} sum_k |s j + s K k>, M = N/(sK).
    Corrects X^a for a in {-(s-1)/2..(s-1)/2} and Z^t for t in a transversal of Z_N/(N/(sK)) Z_N."""
    M = N // (s * K)
    x = np.arange(N)
    omega = np.exp(2j * np.pi / N)
    V = np.zeros((K, N), dtype=complex)
    for j in range(K):
        V[j, (s * j + s * K * np.arange(M)) % N] = 1 / np.sqrt(M)
    TX = [a for a in range(-(s // 2), s // 2 + 1)]
    nZ = s * K  # |Z_N / C1^perp| with C1^perp = M Z_N  -> N / (N/M)... = s K classes
    TZ = [t for t in range(-(nZ // 2), nZ - nZ // 2)]
    nq = int(np.ceil(np.log2(N)))
    D = 2 ** nq
    Bs = []
    for a in TX:
        for t in TZ:
            W = np.roll(V * omega ** (t * x)[None, :], a, axis=1).T  # X^a Z^t V
            Bq = np.zeros((D, K), dtype=complex)
            Bq[:N] = W
            Bs.append(Bq)
    Vq = np.zeros((K, D), dtype=complex)
    Vq[:, :N] = V
    valid = np.zeros(D, dtype=bool)
    valid[:N] = True
    return EmbeddedCode(f"modular Z_{N} (standard qudit CSS)", nq, K, Vq, np.array(Bs), valid,
                        {"|T_X|": len(TX), "|T_Z|": len(TZ), "hilbert_dim": N})


def unencoded_embedded(K: int = 5) -> EmbeddedCode:
    nq = int(np.ceil(np.log2(K)))
    D = 2 ** nq
    V = np.zeros((K, D), dtype=complex)
    V[np.arange(K), np.arange(K)] = 1
    valid = np.zeros(D, dtype=bool)
    valid[:K] = True
    return EmbeddedCode(f"no QEC ({K} levels in {nq} qubits)", nq, K, V, V.T[None].copy(), valid, {"hilbert_dim": K})


def five_qubit_code() -> EmbeddedCode:
    """[[5,1,3]] perfect code; stabilizers XZZXI and cyclic shifts; corrects any 1-qubit Pauli."""
    from functools import reduce

    P = {"I": np.eye(2), "X": np.array([[0, 1], [1, 0]]), "Y": np.array([[0, -1j], [1j, 0]]),
         "Z": np.array([[1, 0], [0, -1]])}
    op = lambda s: reduce(np.kron, [P[c] for c in s]).astype(complex)
    gens = ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"]
    S = [op(g) for g in gens]
    Pc = reduce(lambda A, B: A @ B, [(np.eye(32) + s) / 2 for s in S])
    ZL, XL = op("ZZZZZ"), op("XXXXX")
    w, U = np.linalg.eigh(Pc @ ZL @ Pc)
    v0 = U[:, np.argmax(w)]
    v0 = v0 / np.linalg.norm(v0)
    v1 = XL @ v0
    V = np.stack([v0, v1])
    errs = ["IIIII"] + [("I" * i + c + "I" * (4 - i)) for i in range(5) for c in "XYZ"]
    Bs = [op(e) @ V.T for e in errs]
    return EmbeddedCode("[[5,1,3]]", 5, 2, V, np.array(Bs), np.ones(32, dtype=bool), {"syndromes": len(errs)})


# ----------------------------------------------------------------------------- layout B and references
def ring_code_embedded_split(built) -> EmbeddedCode:
    """Same ring code, embedded in layout B (split-coordinate base-p digits, ceil(log2 p) qubits each)."""
    from ..pl_circuits.split_layout import SplitCircuits

    sp, code = built.space, built.code
    sc = SplitCircuits(built)
    lay = sc.L
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // built.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // built.C1_dual.size)
    T = np.array([sc.canonical_t(j) for j in range(sc.K)]).reshape(-1, 1, 2)
    V = code.logical_states(T)
    D = 2 ** lay.n_qubits
    emb = lay.basis_index(built.ring.elements())
    Bs = []
    for a in TX:
        for f in TZ:
            W = np.stack([sp.apply_X(a, sp.apply_Z(f, v)) for v in V], axis=1)
            Bq = np.zeros((D, len(V)), dtype=complex)
            Bq[emb] = W
            Bs.append(Bq)
    Vq = np.zeros((len(V), D), dtype=complex)
    Vq[:, emb] = V
    return EmbeddedCode(f"ring Z_{built.ring.q}[i] (layout B)", lay.n_qubits, len(V), Vq, np.array(Bs),
                        lay.valid_mask(), {"|T_X|": len(TX), "|T_Z|": len(TZ), "hilbert_dim": sp.dim})


def uncoded_same_embedding(built, layout: str) -> EmbeddedCode:
    """NO QEC, same register and qubit count as the ring code: logical j stored as the single basis
    state |t_j> (canonical transversal); decoding = projection onto span{|t_j>} (strict: any change
    of the register is an error)."""
    from ..pl_circuits.ring_circuits import RingCircuits
    from ..pl_circuits.split_layout import SplitCircuits

    sc = SplitCircuits(built)
    T = np.array([sc.canonical_t(j) for j in range(sc.K)]).reshape(-1, 2)
    R = built.ring
    if layout == "B":
        lay = sc.L
        idx, nq, valid = lay.basis_index(T), lay.n_qubits, lay.valid_mask()
    else:
        rc = RingCircuits(R.q)
        m = rc.L.m
        idx, nq = (T[:, 0] << m) | T[:, 1], 2 * m
        a, b = np.divmod(np.arange(R.size), R.q)
        valid = np.zeros(2 ** nq, dtype=bool)
        valid[(a << m) | b] = True
    V = np.zeros((len(T), 2 ** nq), dtype=complex)
    V[np.arange(len(T)), idx] = 1
    return EmbeddedCode(f"no QEC, same register (layout {layout}, strict)", nq, len(T), V, V.T[None].copy(), valid)


def uncoded_label_only(built) -> EmbeddedCode:
    """NO QEC, layout B register (same qubit count); the decoder reads ONLY the label digit(s) and
    ignores the other qubits (they are idle at |0> and may be hit by noise without effect)."""
    from ..pl_circuits.split_layout import SplitCircuits

    sc = SplitCircuits(built)
    lay = sc.L
    label_q = [w for d, r in zip(lay.digits, sc.roles) if r == "label" for w in d.wires]
    other_q = [w for w in range(lay.n_qubits) if w not in label_q]
    n = lay.n_qubits
    K = sc.K

    def full_index(lab_val, other_val):
        idx = 0
        for w in range(n):
            if w in label_q:
                bit = (lab_val >> (len(label_q) - 1 - label_q.index(w))) & 1
            else:
                bit = (other_val >> (len(other_q) - 1 - other_q.index(w))) & 1
            idx = (idx << 1) | bit
        return idx

    lab_vals = []
    for j in range(K):
        v = 0
        for d, val in zip(sc.logical, sc.label_values(j)):
            v = (v << d.m) | val
        lab_vals.append(v)
    V = np.zeros((K, 2 ** n), dtype=complex)
    for j, lv in enumerate(lab_vals):
        V[j, full_index(lv, 0)] = 1
    Bs = np.zeros((2 ** len(other_q), 2 ** n, K), dtype=complex)
    for o in range(2 ** len(other_q)):
        for j, lv in enumerate(lab_vals):
            Bs[o, full_index(lv, o), j] = 1
    valid = np.zeros(2 ** n, dtype=bool)
    for o in range(2 ** len(other_q)):
        for lv in lab_vals:
            valid[full_index(lv, o)] = True
    return EmbeddedCode("no QEC, layout B register, label digit only", n, K, V, Bs, valid,
                        {"label_qubits": len(label_q), "idle_qubits": len(other_q)})
