"""Syndrome-extraction circuits of the baseline codes, used only for resource counts.

* ModularCircuits: standard qudit CSS code over Z_N (N = 625, K = 5) in ONE m-qubit register:
    Z-stabilizer Z^(N/s): eigenvalue exp(2 pi i x / s) -> accumulate x mod s into an ancilla;
    X-stabilizer X^(sK) (order M = N/(sK)): phase estimation with a DFT_M ancilla register.
* five_qubit_syndrome: textbook [[5,1,3]] extraction, 4 ancillas, controlled Paulis.
"""
from __future__ import annotations

import numpy as np
import pennylane as qml

from .ring_circuits import dft_embedded, nbits


class ModularCircuits:
    def __init__(self, N=625, K=5, s=5):
        self.N, self.K, self.s = N, K, s
        self.M = N // (s * K)
        self.m = nbits(N)
        w = 0
        self.reg = list(range(w, w + self.m)); w += self.m
        self.z_anc = list(range(w, w + nbits(s))); w += nbits(s)
        self.x_anc = list(range(w, w + nbits(self.M))); w += nbits(self.M)
        self.work = [w, w + 1]; w += 2
        self.n_wires = w

    def _adder(self, k, wires, mod, control=None):
        with qml.QueuingManager.stop_recording():
            op = qml.Adder(int(k), wires, mod=mod, work_wires=self.work)
        if control is None:
            qml.apply(op)
        else:
            qml.ctrl(op, control=control)

    def X(self, a):
        if a % self.N:
            self._adder(a % self.N, self.reg, self.N)

    def Z(self, t):
        for j, wire in enumerate(self.reg):
            ang = 2 * np.pi * ((t * (1 << (self.m - 1 - j))) % self.N) / self.N
            if ang:
                qml.PhaseShift(ang, wires=wire)

    def z_syndrome(self):
        for j, wire in enumerate(self.reg):
            add = (1 << (self.m - 1 - j)) % self.s
            if add:
                self._adder(add, self.z_anc, self.s, control=wire)

    def x_syndrome(self):
        F = dft_embedded(self.M)
        qml.QubitUnitary(F, wires=self.x_anc)
        nb = len(self.x_anc)
        for i, wire in enumerate(self.x_anc):
            self._adder((self.s * self.K * (1 << (nb - 1 - i))) % self.N, self.reg, self.N, control=wire)
        qml.QubitUnitary(F, wires=self.x_anc)


def five_qubit_syndrome(data=(0, 1, 2, 3, 4), anc=(5, 6, 7, 8)):
    gens = ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"]
    for g, a in zip(gens, anc):
        qml.Hadamard(a)
        for qb, c in zip(data, g):
            if c == "X":
                qml.CNOT([a, qb])
            elif c == "Z":
                qml.CZ([a, qb])
            elif c == "Y":
                qml.CY([a, qb])
        qml.Hadamard(a)
