"""Gate-level circuits for one R_Q-qudit (n = 1) embedded in qubits.

Embedding ("split" layout): x = a + b i  ->  |a>_re |b>_im, each register m = ceil(log2 q)
qubits, big-endian (wire 0 of a register is its most significant bit), so the computational
index of |a>|b> is  a * 2^m + b.  Valid states: a, b < q.  For q = 25, 85, 325 this uses
10, 14, 18 data qubits (the dense layout a*q + b would need 10, 13, 17 but turns X(u) into a
non-separable modular addition; it is not used here).

Gates (no dense unitaries on the data register):
  X(u), u = c + d i   ->  qml.Adder(c, re, mod=q) ; qml.Adder(d, im, mod=q)   (2 work wires)
  Z(v), v = c + d i   ->  phase exp(2 pi i [(c+d) a + (d-c) b] / q)
                          = product of single-qubit PhaseShift gates (one per data qubit)
Syndrome extraction:
  Z-type generator v  -> s = Tr<v, x>_H = (c+d) a + (d-c) b  (mod q) takes values in a subgroup
                         of order N = q / gcd(c+d, d-c, q); it is accumulated into an ancilla
                         register mod N with controlled Adders (one per data qubit).
  X-type generator u  -> phase estimation of X(u) (order N = additive order of u):
                         DFT_N on an ancilla register, controlled X(2^w u) from each ancilla bit,
                         DFT_N again, measure.  DFT_N for N != 2^k is a small custom
                         QubitUnitary (2^k x 2^k, k = ceil(log2 N)) acting on ancillas only -
                         PennyLane has no built-in Z_N Fourier transform for N != 2^k.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pennylane as qml


def nbits(N: int) -> int:
    return max(1, math.ceil(math.log2(N)))


def dft_embedded(N: int) -> np.ndarray:
    """F|k> = N^{-1/2} sum_j exp(2 pi i jk/N)|j> on the first N basis states, identity elsewhere."""
    k = nbits(N)
    U = np.eye(2 ** k, dtype=complex)
    j = np.arange(N)
    U[:N, :N] = np.exp(2j * np.pi * np.outer(j, j) / N) / np.sqrt(N)
    return U


@dataclass
class RingRegisterLayout:
    q: int
    z_anc_orders: list[int] = field(default_factory=list)
    x_anc_orders: list[int] = field(default_factory=list)

    def __post_init__(self):
        self.m = nbits(self.q)
        w = 0
        self.re = list(range(w, w + self.m)); w += self.m
        self.im = list(range(w, w + self.m)); w += self.m
        self.data = self.re + self.im
        self.z_anc = []
        for N in self.z_anc_orders:
            self.z_anc.append(list(range(w, w + nbits(N)))); w += nbits(N)
        self.x_anc = []
        for N in self.x_anc_orders:
            self.x_anc.append(list(range(w, w + nbits(N)))); w += nbits(N)
        self.work = [w, w + 1]; w += 2
        self.n_wires = w

    def data_index(self, a: int, b: int) -> int:
        return (a << self.m) | b


class RingCircuits:
    """Builds the gate sequences; all methods must be called inside a QNode / queuing context."""

    def __init__(self, q: int, zgens=(), xgens=()):
        self.q = q
        self.zgens = [tuple(int(t) for t in np.asarray(v).reshape(2)) for v in zgens]
        self.xgens = [tuple(int(t) for t in np.asarray(u).reshape(2)) for u in xgens]
        self.z_orders = [self.z_value_order(v) for v in self.zgens]
        self.x_orders = [self.additive_order(u) for u in self.xgens]
        self.L = RingRegisterLayout(q, self.z_orders, self.x_orders)

    # ------------------------------------------------------------------ helpers
    def additive_order(self, u) -> int:
        g = math.gcd(math.gcd(u[0] % self.q, u[1] % self.q), self.q)
        return self.q // g

    def z_coeffs(self, v):
        c, d = v
        return (c + d) % self.q, (d - c) % self.q

    def z_value_order(self, v) -> int:
        ca, cb = self.z_coeffs(v)
        return self.q // math.gcd(math.gcd(ca, cb), self.q)

    def embed_ring_state(self, psi_ring: np.ndarray) -> np.ndarray:
        """Ring state (index a*q + b) -> data-register statevector (index a*2^m + b)."""
        q, m = self.q, self.L.m
        out = np.zeros(2 ** (2 * m), dtype=complex)
        a, b = np.divmod(np.arange(q * q), q)
        out[(a << m) | b] = psi_ring
        return out

    def extract_ring_state(self, psi_data: np.ndarray) -> tuple[np.ndarray, float]:
        """Data-register statevector -> (ring state, probability outside the valid subspace)."""
        q, m = self.q, self.L.m
        a, b = np.divmod(np.arange(q * q), q)
        valid = psi_data[(a << m) | b]
        leak = float(max(0.0, 1.0 - np.vdot(valid, valid).real))
        return valid, leak

    # ------------------------------------------------------------------ gates
    def X(self, u, control=None, control_values=None):
        c, d = (int(u[0]) % self.q, int(u[1]) % self.q)
        for k, reg in ((c, self.L.re), (d, self.L.im)):
            if k == 0:
                continue
            # build without queuing, then queue exactly once (creating an Operator inside a QNode
            # queues it automatically; qml.apply on it would apply the adder twice)
            with qml.QueuingManager.stop_recording():
                op = qml.Adder(k, reg, mod=self.q, work_wires=self.L.work)
            if control is None:
                qml.apply(op)
            else:
                qml.ctrl(op, control=control, control_values=control_values)

    def Z(self, v, control=None, control_values=None):
        ca, cb = self.z_coeffs((int(v[0]), int(v[1])))
        m = self.L.m
        for coef, reg in ((ca, self.L.re), (cb, self.L.im)):
            if coef == 0:
                continue
            for j, wire in enumerate(reg):
                w = 1 << (m - 1 - j)
                ang = 2 * np.pi * ((coef * w) % self.q) / self.q
                if not ang:
                    continue
                if control is None:
                    qml.PhaseShift(ang, wires=wire)
                else:
                    with qml.QueuingManager.stop_recording():
                        op = qml.PhaseShift(ang, wires=wire)
                    qml.ctrl(op, control=control, control_values=control_values)

    # ------------------------------------------------------------------ syndromes
    def z_syndrome(self, k: int):
        """Accumulate s' = Tr<v_k, x>/(q/N) mod N into ancilla register z_anc[k]."""
        v = self.zgens[k]
        N = self.z_orders[k]
        scale = self.q // N
        ca, cb = self.z_coeffs(v)
        ca, cb = (ca // scale) % N, (cb // scale) % N
        anc = self.L.z_anc[k]
        m = self.L.m
        for coef, reg in ((ca, self.L.re), (cb, self.L.im)):
            if coef == 0:
                continue
            for j, wire in enumerate(reg):
                add = (coef * (1 << (m - 1 - j))) % N
                if add:
                    qml.ctrl(qml.Adder(add, anc, mod=N, work_wires=self.L.work), control=wire)

    def x_syndrome(self, k: int):
        """Phase estimation of X(u_k): ancilla holds lambda with X(u)|phi> = exp(-2 pi i lambda/N)|phi>."""
        u = self.xgens[k]
        N = self.x_orders[k]
        anc = self.L.x_anc[k]
        F = dft_embedded(N)
        qml.QubitUnitary(F, wires=anc)
        nb = len(anc)
        for i, wire in enumerate(anc):
            w = 1 << (nb - 1 - i)
            uw = ((u[0] * w) % self.q, (u[1] * w) % self.q)
            self.X(uw, control=wire)
        qml.QubitUnitary(F, wires=anc)

    # syndrome conversions to the conventions of RingCSSCode (values mod q)
    def z_syndrome_value(self, k: int, sprime: int) -> int:
        return (sprime * (self.q // self.z_orders[k])) % self.q

    def x_syndrome_value(self, k: int, lam: int) -> int:
        """measured lambda -> t = -Tr<f, u>  (RingCSSCode.xsyn convention)."""
        N = self.x_orders[k]
        # X(u) eigenvalue is chi(-<f,u>) = exp(-2 pi i Tr<f,u>/q) = exp(-2 pi i lambda/N)
        # => Tr<f,u> = lambda q/N  => t = -lambda q/N
        return (-lam * (self.q // N)) % self.q
