"""The stabilizer code of Theorem 4, built from enumerated codes and checked numerically.

    S = < X(u) : u in C1 >  x  < Z(v) : v in D >,   D = C2^{perp_H}  (or Definition 6's <sigma(alpha2)>)

Conventions for syndromes (all values mod q):
  * X(e)-type error, measured with the Z-generators v_j:   Z(v)X(e)|psi> = chi(<v,e>) X(e)|psi>
        -> s_j = Tr<v_j, e>_H
  * Z(f)-type error, measured with the X-generators u_j:   X(u)Z(f)|psi> = chi(-<f,u>) Z(f)|psi>
        -> t_j = -Tr<f, u_j>_H
Both are also extracted *from states* (expectation values of the actual operators), which is
the numerical check that does not rely on the algebra above.
"""
from __future__ import annotations

import numpy as np

from ..ideals import AdditiveCode
from .pauli import QuditSpace


def lee_weight(ring, x) -> np.ndarray:
    """Sum over components of |a| + |b| with a, b taken in (-q/2, q/2]."""
    x = np.asarray(x)
    c = np.where(x > ring.q // 2, ring.q - x, x)
    return c.sum(axis=(-1, -2)) if x.ndim >= 2 else c.sum(axis=-1)


def min_weight_transversal(space: QuditSpace, key_fn, n_classes: int) -> np.ndarray:
    """One minimum-Lee-weight representative per class of key_fn over R^n (ties: lowest index)."""
    V = space.vecs
    w = lee_weight(space.ring, V)
    order = np.lexsort((np.arange(len(V)), w))
    keys = key_fn(V[order])
    _, first = np.unique(keys, return_index=True)
    if len(first) != n_classes:
        raise AssertionError(f"found {len(first)} classes, expected {n_classes}")
    reps = V[order][np.sort(first)]
    return reps


class RingCSSCode:
    def __init__(self, space: QuditSpace, C1: AdditiveCode, C2: AdditiveCode, Zgroup: AdditiveCode, name=""):
        self.space, self.C1, self.C2, self.Zg, self.name = space, C1, C2, Zgroup, name
        self.ring = space.ring
        self.xgens = [np.asarray(g) for g in C1.additive_generators()]
        self.zgens = [np.asarray(g) for g in Zgroup.additive_generators()]
        self.K_formula = C2.size / C1.size

    # ------------------------------------------------------------ syndromes (algebraic)
    def _keys(self, s: np.ndarray) -> np.ndarray:
        w = np.array([self.ring.q ** j for j in range(s.shape[1])], dtype=np.int64)
        assert self.ring.q ** s.shape[1] < 2**62, "syndrome key overflow"
        return (s.astype(np.int64) * w).sum(axis=1)

    def zsyn(self, E) -> np.ndarray:
        """Syndrome of X(e) errors, E shape (m, n, 2) -> (m, #zgens)."""
        E = self.ring.reduce(np.asarray(E))
        cols = [self.ring.trace(self.ring.hermitian(v[None], E)) for v in self.zgens]
        return np.stack(cols, axis=1) if cols else np.zeros((len(E), 0), np.int64)

    def xsyn(self, F) -> np.ndarray:
        """Syndrome of Z(f) errors, F shape (m, n, 2) -> (m, #xgens)."""
        F = self.ring.reduce(np.asarray(F))
        cols = [np.mod(-self.ring.trace(self.ring.hermitian(F, u[None])), self.ring.q) for u in self.xgens]
        return np.stack(cols, axis=1) if cols else np.zeros((len(F), 0), np.int64)

    def zsyn_key(self, E):
        return self._keys(self.zsyn(E))

    def xsyn_key(self, F):
        return self._keys(self.xsyn(F))

    # ------------------------------------------------------------ syndromes (from states)
    def measure_state_syndrome(self, phi) -> tuple[tuple, tuple]:
        sp = self.space
        z = tuple(sp.phase_to_syndrome(sp.expect_Z(v, phi)) for v in self.zgens)
        x = tuple(sp.phase_to_syndrome(sp.expect_X(u, phi)) for u in self.xgens)
        return z, x

    # ------------------------------------------------------------ commutation
    def commutation_exhaustive(self) -> dict:
        """Tr<v, u>_H over ALL pairs (u in C1, v in Zgroup)."""
        U = self.C1.vectors()
        Vv = self.Zg.vectors()
        bad = 0
        first = None
        for s in range(0, len(Vv), max(1, 4_000_000 // max(1, len(U)))):
            blk = Vv[s:s + max(1, 4_000_000 // max(1, len(U)))]
            tr = self.ring.trace(self.ring.hermitian(blk[:, None], U[None]))
            nz = np.argwhere(tr != 0)
            bad += len(nz)
            if first is None and len(nz):
                i, j = nz[0]
                first = {"v": self.ring.fmt(blk[i]), "u": self.ring.fmt(U[j]), "Tr<v,u>": int(tr[i, j])}
        return {"pairs": len(U) * len(Vv), "noncommuting_pairs": int(bad), "first_noncommuting": first}

    # ------------------------------------------------------------ projectors
    def pz_diag(self) -> np.ndarray:
        """Diagonal of P_Z = (1/|D|) sum_{v in D} Z(v), summed over ALL elements of D."""
        acc = np.zeros(self.space.dim, dtype=complex)
        for v in self.Zg.vectors():
            acc += self.space.z_phase(v)
        return acc / self.Zg.size

    def apply_PX(self, psi) -> np.ndarray:
        out = np.zeros_like(psi, dtype=complex)
        for u in self.C1.vectors():
            out += self.space.apply_X(u, psi)
        return out / self.C1.size

    def apply_P(self, psi, pz=None) -> np.ndarray:
        pz = self.pz_diag() if pz is None else pz
        return self.apply_PX(pz * psi)

    def x_has_no_fixed_points(self) -> bool:
        """diag X(u) = 0 for every u != 0 in C1 (used by the trace formula)."""
        idx = np.arange(self.space.dim)
        for u in self.C1.vectors()[1:]:
            if np.any(self.space.gather_X(u) == idx):
                return False
        return True

    def dim_trace_formula(self, pz=None) -> float:
        """Tr P = Tr(P_X P_Z) = sum_x pz(x) * (1/|C1|)  (diag of P_X is 1/|C1|)."""
        pz = self.pz_diag() if pz is None else pz
        return float(np.real(pz.sum()) / self.C1.size)

    def dim_structural(self) -> int:
        """Number of C1-cosets of R^n contained entirely in {x : Tr<v,x> = 0 for all v in D}.
        Valid even when the generators do not commute (dimension of the joint +1 eigenspace)."""
        ok = np.ones(self.space.dim, dtype=bool)
        for v in self.zgens:
            ok &= self.space.z_exponent(v) == 0
        seen = np.zeros(self.space.dim, dtype=bool)
        c1 = self.C1.vectors()
        count = 0
        for x in np.flatnonzero(ok):
            if seen[x]:
                continue
            orbit = self.ring.vec_index(self.ring.add(self.space.vecs[x][None], c1))
            seen[orbit] = True
            if ok[orbit].all():
                count += 1
        return count

    def dim_nullspace_dense(self) -> int:
        """Independent count: nullity of the stacked (S_j - I) over all generators (small dims)."""
        d = self.space.dim
        blocks = []
        for u in self.xgens:
            blocks.append(self.space.sparse_X(u).toarray() - np.eye(d))
        for v in self.zgens:
            blocks.append(np.diag(self.space.z_phase(v)) - np.eye(d))
        A = np.vstack(blocks)
        s = np.linalg.svd(A, compute_uv=False)
        return int(np.sum(s < 1e-9 * max(1.0, s.max())))

    # ------------------------------------------------------------ logical states / operators
    def logical_states(self, eps) -> np.ndarray:
        """|psi_e> = |C1|^{-1/2} sum_{u in C1} |e + u>,  one row per e in eps."""
        eps = self.ring.reduce(np.asarray(eps)).reshape(-1, self.space.n, 2)
        c1 = self.C1.vectors()
        V = np.zeros((len(eps), self.space.dim), dtype=complex)
        for k, e in enumerate(eps):
            V[k, self.ring.vec_index(self.ring.add(c1, e[None]))] = 1 / np.sqrt(self.C1.size)
        return V

    def logical_matrix(self, V, op) -> tuple[np.ndarray, float]:
        """L = V^dag op V (K x K) and leakage ||(I - V^T V^*) op V|| (0 iff op preserves the code)."""
        W = np.stack([op(v) for v in V])  # (K, dim)
        L = V.conj() @ W.T
        resid = W - (L.T @ V)
        return L, float(np.linalg.norm(resid))

    def knill_laflamme(self, V, error_ops) -> dict:
        """max_{a,b} || V^dag E_a^dag E_b V - c_ab I ||  over the given error operators."""
        Ws = [np.stack([E(v) for v in V]) for E in error_ops]  # each (K, dim)
        K = V.shape[0]
        worst, arg = 0.0, None
        for a, Wa in enumerate(Ws):
            for b, Wb in enumerate(Ws):
                M = Wa.conj() @ Wb.T
                c = np.trace(M) / K
                dev = float(np.linalg.norm(M - c * np.eye(K)))
                if dev > worst:
                    worst, arg = dev, (a, b)
        return {"max_deviation": worst, "worst_pair": arg, "n_errors": len(error_ops)}
