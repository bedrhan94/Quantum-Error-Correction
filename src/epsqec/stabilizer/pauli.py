"""Generalised Pauli operators over R^n, R = Z_q[i]  (paper, Definition 8) - matrix-free.

Hilbert space H = C^{|R|^n} with computational basis |x>, x in R^n, ordered by
GaussianRing.vec_index.  Operators are never stored as dense matrices:

    X(u)|x> = |x + u>             -> a permutation, stored as a gather index
    Z(v)|x> = chi(<v, x>_H)|x>    -> a diagonal phase vector,  chi(t) = exp(2 pi i Tr(t) / q)

Sparse scipy matrices are built only on request (unitarity checks on small spaces).
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from ..ring import GaussianRing


class QuditSpace:
    def __init__(self, ring: GaussianRing, n: int = 1):
        self.ring, self.n = ring, n
        self.dim = ring.size ** n
        self.vecs = ring.all_vectors(n)  # (dim, n, 2)

    # ---------------------------------------------------------------- X(u)
    def gather_X(self, u) -> np.ndarray:
        """g with (X(u) psi)[x] = psi[g[x]], i.e. g[x] = idx(x - u)."""
        u = self.ring.reduce(np.asarray(u)).reshape(self.n, 2)
        return self.ring.vec_index(self.ring.sub(self.vecs, u[None]))

    def apply_X(self, u, psi):
        return psi[..., self.gather_X(u)]

    def sparse_X(self, u) -> sp.csr_matrix:
        u = self.ring.reduce(np.asarray(u)).reshape(self.n, 2)
        rows = self.ring.vec_index(self.ring.add(self.vecs, u[None]))  # |x> -> |x+u>
        cols = np.arange(self.dim)
        return sp.csr_matrix((np.ones(self.dim, dtype=complex), (rows, cols)), shape=(self.dim, self.dim))

    # ---------------------------------------------------------------- Z(v)
    def z_exponent(self, v) -> np.ndarray:
        """Tr(<v, x>_H) mod q for every basis vector x."""
        v = self.ring.reduce(np.asarray(v)).reshape(self.n, 2)
        return self.ring.trace(self.ring.hermitian(v[None], self.vecs))

    def z_phase(self, v) -> np.ndarray:
        return np.exp(2j * np.pi * self.z_exponent(v) / self.ring.q)

    def apply_Z(self, v, psi):
        return psi * self.z_phase(v)

    def sparse_Z(self, v) -> sp.csr_matrix:
        return sp.diags(self.z_phase(v)).tocsr()

    # ---------------------------------------------------------------- helpers
    def chi_pair(self, v, u) -> complex:
        """chi(<v, u>_H), the commutation phase of Definition 8."""
        v = self.ring.reduce(np.asarray(v)).reshape(self.n, 2)
        u = self.ring.reduce(np.asarray(u)).reshape(self.n, 2)
        t = self.ring.trace(self.ring.hermitian(v[None], u[None]))[0]
        return complex(np.exp(2j * np.pi * t / self.ring.q))

    def basis_state(self, x) -> np.ndarray:
        psi = np.zeros(self.dim, dtype=complex)
        psi[int(self.ring.vec_index(self.ring.reduce(np.asarray(x)).reshape(1, self.n, 2))[0])] = 1
        return psi

    def expect_Z(self, v, psi) -> complex:
        return complex(np.vdot(psi, self.apply_Z(v, psi)) / np.vdot(psi, psi))

    def expect_X(self, u, psi) -> complex:
        return complex(np.vdot(psi, self.apply_X(u, psi)) / np.vdot(psi, psi))

    def phase_to_syndrome(self, lam: complex, tol: float = 1e-9) -> int:
        """Eigenvalue lambda = exp(2 pi i s / q) -> s; raises if |lambda| != 1 (not an eigenstate)."""
        if abs(abs(lam) - 1) > 1e-7:
            raise ValueError(f"state is not an eigenstate (|<S>| = {abs(lam):.6f})")
        s = np.angle(lam) * self.ring.q / (2 * np.pi)
        r = int(np.round(s)) % self.ring.q
        if abs(s - np.round(s)) > 1e-6:
            raise ValueError(f"eigenphase {s} is not a multiple of 2 pi / q")
        return r
