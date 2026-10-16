"""Layout B ("split coordinates") and gate-level circuits for n = 1 ring codes over Z_q[i].

Coordinates
-----------
CRT + split:  Z_q[i]  ~=  prod_b  Z_{p_b^e_b}[i]  ~=  prod_b  Z_{p_b^e_b} x Z_{p_b^e_b},
    a + b i  ->  ( U_b, V_b ) = ( a + s_b b ,  a - s_b b )  (mod p_b^e_b),   s_b^2 = -1 (mod p_b^e_b).
This is a RING isomorphism (componentwise multiplication), so every ideal is a product of
p-power ideals in each component and conjugation sigma simply swaps U and V.
Each component is written in base-p digits d_0 (least significant) .. d_{e-1}; each digit is
stored in m = ceil(log2 p) qubits (big-endian), levels p .. 2^m - 1 are INVALID.

Code states (canonical transversal)
-----------------------------------
For C1 <= C2 (ideals) and a component with valuations v2 = v_p(C2) <= v1 = v_p(C1):
    digit pos <  v2         : DEAD   (always 0)
    v2 <= pos < v1          : LABEL  (carries the logical digit)
    pos >= v1               : FREE   (uniform over all p values)
|psi_t> = |C1|^{-1/2} sum_{c in C1} |c + t>  is then a PRODUCT state over digits, so the encoder is
  FREE  -> DFT_p (3- or 4-qubit block on that digit only)
  LABEL -> "move" the logical digit in:  CSHIFT(L -> label), CSHIFT^{-1}(label -> L)  (L returns to |0>)
  DEAD  -> nothing.
All small blocks are QubitUnitary on ONE digit (m qubits), optionally controlled; they act as the
identity on invalid levels, so they never leak.

Character / syndromes
---------------------
Every phase uses ``ring.trace`` (the single place where chi is fixed, see GaussianRing).
  Z(v): phase omega_q^{Tr<v,x>_H} = prod_digits omega_q^{w_d * digit},  w_d = Tr<v, e_d>_H  (PhaseShift per qubit)
  Z-syndrome of generator v (value group of order N): s' = Tr<v,x>/(q/N) mod N accumulated into base-p
      digit ancillas with controlled constant adders (one per data qubit).
  X-syndrome of generator u (additive order N): for every prime power p^f || N, phase estimation of
      X(u'), u' = (N/p^f) u, with an f-digit ancilla: DFT_p on each digit, controlled X(c p^pos u'),
      then the radix-p Fourier transform G (f = 1: DFT_p; f = 2: DFT_p, twiddle, DFT_p).
      Measured s = Tr<f,u'>_H / (q/p^f) mod p^f for a Z(f) error  (kernel omega^{+jk}, eigenvalue
      chi(-<f,u'>)); the decoder LUT is computed with the same ring.trace, so the convention is
      consistent by construction.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pennylane as qml

from ..ring import GaussianRing, factorize


def nbits(N: int) -> int:
    return max(1, math.ceil(math.log2(N)))


def sqrt_minus_one(pe: int) -> int:
    for s in range(1, pe):
        if (s * s + 1) % pe == 0:
            return s
    raise ValueError(f"-1 is not a square mod {pe}")


@lru_cache(maxsize=None)
def shift_matrix(p: int, m: int, c: int) -> np.ndarray:
    """|k> -> |k + c mod p> for k < p; identity on invalid levels k >= p."""
    D = 2 ** m
    U = np.zeros((D, D))
    for k in range(D):
        U[(k + c) % p if k < p else k, k] = 1.0
    return U


@lru_cache(maxsize=None)
def dft_matrix(p: int, m: int, inverse: bool = False) -> np.ndarray:
    """DFT_p (kernel omega_p^{+jk}, or ^{-jk} if inverse) on levels < p; identity on invalid levels."""
    D = 2 ** m
    U = np.eye(D, dtype=complex)
    j = np.arange(p)
    sgn = -1 if inverse else 1
    U[:p, :p] = np.exp(sgn * 2j * np.pi * np.outer(j, j) / p) / np.sqrt(p)
    return U


@dataclass
class Digit:
    name: str
    block: int
    comp: str  # 'U' | 'V' | 'L' | 'A'
    pos: int  # 0 = least significant
    p: int
    wires: list = field(default_factory=list)

    @property
    def m(self) -> int:
        return nbits(self.p)


class SplitLayout:
    """Coordinates and data-register indexing (no circuits)."""

    def __init__(self, ring: GaussianRing):
        self.ring = ring
        q = ring.q
        self.blocks = []
        for p, e in sorted(factorize(q).items()):
            pe = p ** e
            s = sqrt_minus_one(pe)
            M = q // pe
            self.blocks.append({"p": p, "e": e, "pe": pe, "s": s, "inv2": pow(2, -1, pe),
                                "inv2s": pow(2 * s % pe, -1, pe), "crt": (M * pow(M, -1, pe)) % q})
        self.digits: list[Digit] = []
        for bi, B in enumerate(self.blocks):
            for comp in ("U", "V"):
                for pos in reversed(range(B["e"])):
                    self.digits.append(Digit(f"{comp}{B['p']}d{pos}", bi, comp, pos, B["p"]))
        w = 0
        for d in self.digits:
            d.wires = list(range(w, w + d.m))
            w += d.m
        self.n_qubits = w

    # ------------------------------------------------------------------ coordinates
    def split(self, x) -> list[tuple[np.ndarray, np.ndarray]]:
        x = np.asarray(x, dtype=np.int64)
        a, b = x[..., 0], x[..., 1]
        return [(np.mod(a + B["s"] * b, B["pe"]), np.mod(a - B["s"] * b, B["pe"])) for B in self.blocks]

    def digits_of(self, x) -> np.ndarray:
        """(..., 2) ring elements -> (..., n_digits) digit values (self.digits order)."""
        sp = self.split(x)
        cols = []
        for d in self.digits:
            U, V = sp[d.block]
            val = U if d.comp == "U" else V
            cols.append((val // (d.p ** d.pos)) % d.p)
        return np.stack(cols, axis=-1)

    def from_digits(self, D) -> np.ndarray:
        D = np.asarray(D, dtype=np.int64)
        q = self.ring.q
        a = np.zeros(D.shape[:-1], dtype=np.int64)
        b = np.zeros(D.shape[:-1], dtype=np.int64)
        for bi, B in enumerate(self.blocks):
            U = np.zeros(D.shape[:-1], dtype=np.int64)
            V = np.zeros(D.shape[:-1], dtype=np.int64)
            for k, d in enumerate(self.digits):
                if d.block != bi:
                    continue
                if d.comp == "U":
                    U = U + D[..., k] * d.p ** d.pos
                else:
                    V = V + D[..., k] * d.p ** d.pos
            ab = np.mod((U + V) * B["inv2"], B["pe"])
            bb = np.mod((U - V) * B["inv2s"], B["pe"])
            a = a + ab * B["crt"]
            b = b + bb * B["crt"]
        return np.stack([np.mod(a, q), np.mod(b, q)], axis=-1)

    def unit_element(self, k: int) -> np.ndarray:
        D = np.zeros(len(self.digits), dtype=np.int64)
        D[k] = 1
        return self.from_digits(D)

    def basis_index(self, x) -> np.ndarray:
        """Computational-basis index of ring element(s) in the data register (big-endian wires)."""
        D = self.digits_of(x)
        idx = np.zeros(D.shape[:-1], dtype=np.int64)
        for k, d in enumerate(self.digits):
            idx = (idx << d.m) | D[..., k]
        return idx

    def valid_mask(self) -> np.ndarray:
        """bool over 2^n_qubits: True iff every digit holds a valid level (< p)."""
        idx = np.arange(2 ** self.n_qubits, dtype=np.int64)
        ok = np.ones_like(idx, dtype=bool)
        shift = 0
        for d in reversed(self.digits):
            ok &= ((idx >> shift) & ((1 << d.m) - 1)) < d.p
            shift += d.m
        return ok

    def embed(self, psi_ring: np.ndarray) -> np.ndarray:
        out = np.zeros(2 ** self.n_qubits, dtype=complex)
        out[self.basis_index(self.ring.elements())] = psi_ring
        return out

    # ------------------------------------------------------------------ ideals
    def valuations(self, code) -> dict:
        """{digit-component (block, comp): v_p} for an ideal (n = 1); checks the product structure."""
        sp = self.split(code.vectors()[:, 0, :])
        val, size = {}, 1
        for bi, B in enumerate(self.blocks):
            for ci, comp in enumerate(("U", "V")):
                vals = sp[bi][ci]
                v = B["e"]
                for x in np.unique(vals):
                    if x == 0:
                        continue
                    k = 0
                    while x % B["p"] == 0:
                        x //= B["p"]
                        k += 1
                    v = min(v, k)
                val[(bi, comp)] = v
                size *= B["p"] ** (B["e"] - v)
        if size != code.size:
            raise AssertionError("code is not a product of p-power ideals in split coordinates")
        return val


@dataclass
class SyndromePart:
    kind: str  # 'Z' (Z-type stabilizer, detects X errors) or 'X'
    gen_index: int
    p: int
    f: int
    scale: int  # Z: q/N ; X: N/p^f (u' = scale * u)
    generator: np.ndarray
    digits: list = field(default_factory=list)  # ancilla digits, pos order 0..f-1


class SplitCircuits:
    """Gate-level circuits for one code pair in layout B.  Call methods inside a QNode."""

    def __init__(self, built, reuse_ancilla: bool = True):
        self.b = built
        self.ring = built.ring
        self.L = SplitLayout(self.ring)
        lay = self.L
        v1, v2 = lay.valuations(built.C1), lay.valuations(built.C2)
        self.roles = []
        for d in lay.digits:
            lo, hi = v2[(d.block, d.comp)], v1[(d.block, d.comp)]
            self.roles.append("dead" if d.pos < lo else ("label" if d.pos < hi else "free"))
        self.K = int(np.prod([d.p for d, r in zip(lay.digits, self.roles) if r == "label"] or [1]))
        assert self.K == built.C2.size // built.C1.size, "digit roles do not reproduce K"
        w = lay.n_qubits
        # logical register: one digit per label digit
        self.logical: list[Digit] = []
        for d, r in zip(lay.digits, self.roles):
            if r == "label":
                ld = Digit("L" + d.name, d.block, "L", d.pos, d.p, list(range(w, w + d.m)))
                w += d.m
                self.logical.append(ld)
        self.data_wires = list(range(lay.n_qubits))
        self.logical_wires = [x for d in self.logical for x in d.wires]
        # syndrome parts
        q = self.ring.q
        self.parts: list[SyndromePart] = []
        for k, v in enumerate(built.code.zgens):
            wts = [self.z_weights(v)]
            g = q
            for wd in wts[0]:
                g = math.gcd(g, int(wd))
            N = q // g
            for p, f in sorted(factorize(N).items()) if N > 1 else []:
                self.parts.append(SyndromePart("Z", k, p, f, q // N, np.asarray(v).reshape(2)))
        for k, u in enumerate(built.code.xgens):
            u = np.asarray(u).reshape(2)
            N = q // math.gcd(math.gcd(int(u[0]), int(u[1])), q)
            for p, f in sorted(factorize(N).items()) if N > 1 else []:
                if f > 2:
                    raise NotImplementedError("radix-p Fourier transform implemented for f <= 2")
                self.parts.append(SyndromePart("X", k, p, f, N // p ** f, u))
        # ancilla allocation
        self.reuse = reuse_ancilla
        if reuse_ancilla:
            pool = max(nbits(P.p) * P.f for P in self.parts)
            pool_wires = list(range(w, w + pool))
            w += pool
            for P in self.parts:
                m = nbits(P.p)
                P.digits = [Digit(f"A{P.kind}{P.gen_index}p{P.p}d{pos}", -1, "A", pos, P.p,
                                  pool_wires[pos * m:(pos + 1) * m]) for pos in range(P.f)]
            self.anc_wires = pool_wires
        else:
            self.anc_wires = []
            for P in self.parts:
                m = nbits(P.p)
                P.digits = []
                for pos in range(P.f):
                    P.digits.append(Digit(f"A{P.kind}{P.gen_index}p{P.p}d{pos}", -1, "A", pos, P.p,
                                          list(range(w, w + m))))
                    self.anc_wires += list(range(w, w + m))
                    w += m
        self.n_wires = w
        self.unit = [lay.unit_element(k) for k in range(len(lay.digits))]

    # ------------------------------------------------------------------ primitives
    @staticmethod
    def _ctrl(controls):
        cw, cv = [], []
        for wires, value in controls:
            bits = [(value >> (len(wires) - 1 - t)) & 1 for t in range(len(wires))]
            cw += list(wires)
            cv += bits
        return cw, cv

    def _unitary(self, U, wires, controls=()):
        with qml.QueuingManager.stop_recording():
            op = qml.QubitUnitary(U, wires=wires)
        if controls:
            cw, cv = self._ctrl(controls)
            qml.ctrl(op, control=cw, control_values=cv)
        else:
            qml.apply(op)

    def shift(self, d: Digit, c: int, controls=()):
        c %= d.p
        if c:
            self._unitary(shift_matrix(d.p, d.m, c), d.wires, controls)

    def add_const(self, regs: list[Digit], k: int, controls=()):
        """regs = digits of one component in pos order 0..e-1 (same p); adds k mod p^e with carries."""
        p = regs[0].p

        def add_at(pos, c, ctl):
            c %= p
            if c == 0:
                return
            if pos + 1 < len(regs):
                for v in range(p - c, p):  # carry out of pos iff d_pos + c >= p (old value)
                    add_at(pos + 1, 1, list(ctl) + [(regs[pos].wires, v)])
            self.shift(regs[pos], c, ctl)

        for pos in range(len(regs)):
            add_at(pos, (k // p ** pos) % p, list(controls))

    def component_regs(self, block: int, comp: str) -> list[Digit]:
        return sorted([d for d in self.L.digits if d.block == block and d.comp == comp], key=lambda d: d.pos)

    # ------------------------------------------------------------------ Paulis
    def X(self, u, controls=()):
        sp = self.L.split(np.asarray(u).reshape(2))
        for bi in range(len(self.L.blocks)):
            for ci, comp in enumerate(("U", "V")):
                self.add_const(self.component_regs(bi, comp), int(sp[bi][ci]), controls)

    def z_weights(self, v) -> list[int]:
        R = self.ring
        v = R.reduce(np.asarray(v).reshape(1, 2))
        return [int(R.trace(R.hermitian(v[None], e.reshape(1, 1, 2)))[0]) for e in
                (self.L.unit_element(k) for k in range(len(self.L.digits)))]

    def Z(self, v, controls=()):
        q = self.ring.q
        for d, wd in zip(self.L.digits, self.z_weights(v)):
            for t, wire in enumerate(d.wires):
                ang = 2 * np.pi * ((wd * (1 << (d.m - 1 - t))) % q) / q
                if not ang:
                    continue
                if controls:
                    with qml.QueuingManager.stop_recording():
                        op = qml.PhaseShift(ang, wires=wire)
                    cw, cv = self._ctrl(controls)
                    qml.ctrl(op, control=cw, control_values=cv)
                else:
                    qml.PhaseShift(ang, wires=wire)

    # ------------------------------------------------------------------ encoder
    def _move(self, src: Digit, dst: Digit):
        for c in range(1, src.p):
            self.shift(dst, c, [(src.wires, c)])  # dst += src
        for c in range(1, src.p):
            self.shift(src, -c, [(dst.wires, c)])  # src -= dst  -> 0

    def encode(self):
        li = 0
        for d, r in zip(self.L.digits, self.roles):
            if r == "free":
                self._unitary(dft_matrix(d.p, d.m), d.wires)
            elif r == "label":
                self._move(self.logical[li], d)
                li += 1

    def decode(self):
        qml.adjoint(self.encode)()

    # logical index j  <->  label digit values (mixed radix, first label digit most significant)
    def label_values(self, j: int) -> list[int]:
        vals = []
        for d in reversed(self.logical):
            vals.append(j % d.p)
            j //= d.p
        return list(reversed(vals))

    def canonical_t(self, j: int) -> np.ndarray:
        D = np.zeros(len(self.L.digits), dtype=np.int64)
        lv = iter(self.label_values(j))
        for k, r in enumerate(self.roles):
            if r == "label":
                D[k] = next(lv)
        return self.L.from_digits(D)

    def logical_vector(self, amps) -> np.ndarray:
        """Embed K logical amplitudes into the logical register (zeros on invalid levels)."""
        nq = len(self.logical_wires)
        out = np.zeros(2 ** nq, dtype=complex)
        for j, a in enumerate(amps):
            idx = 0
            for d, v in zip(self.logical, self.label_values(j)):
                idx = (idx << d.m) | v
            out[idx] = a
        return out

    def prepare_logical(self, amps):
        qml.MottonenStatePreparation(self.logical_vector(amps), wires=self.logical_wires)

    def unprepare_logical(self, amps):
        qml.adjoint(qml.MottonenStatePreparation)(self.logical_vector(amps), wires=self.logical_wires)

    def prepare_basis(self, j: int):
        for d, v in zip(self.logical, self.label_values(j)):
            for t, wire in enumerate(d.wires):
                if (v >> (d.m - 1 - t)) & 1:
                    qml.PauliX(wire)

    # ------------------------------------------------------------------ syndromes
    def z_part_increment(self, P: SyndromePart, wd: int, t: int, m: int) -> int:
        q = self.ring.q
        w = (wd * (1 << (m - 1 - t))) % q
        assert w % P.scale == 0, "Tr<v, x> must lie in (q/N) Z_q"
        return (w // P.scale) % (P.p ** P.f)

    def z_syndrome(self, P: SyndromePart):
        wts = self.z_weights(P.generator)
        for d, wd in zip(self.L.digits, wts):
            for t, wire in enumerate(d.wires):
                c = self.z_part_increment(P, wd, t, d.m)
                if c:
                    self.add_const(P.digits, c, [([wire], 1)])

    def fourier_g(self, P: SyndromePart):
        """Final transform of the phase estimation (kernel omega^{+jk})."""
        if P.f == 1:
            d = P.digits[0]
            self._unitary(dft_matrix(d.p, d.m), d.wires)
            return
        lo, hi = P.digits[0], P.digits[1]
        p = P.p
        self._unitary(dft_matrix(p, hi.m), hi.wires)  # hi: j1 -> k0
        for a, wa in enumerate(reversed(lo.wires)):  # twiddle omega_{p^2}^{j0 k0}
            for b_, wb in enumerate(reversed(hi.wires)):
                qml.ControlledPhaseShift(2 * np.pi * (2 ** (a + b_)) / p ** 2, wires=[wa, wb])
        self._unitary(dft_matrix(p, lo.m), lo.wires)  # lo: j0 -> k1

    def x_syndrome(self, P: SyndromePart):
        R = self.ring
        u1 = R.reduce(P.scale * np.asarray(P.generator))
        for d in P.digits:
            self._unitary(dft_matrix(d.p, d.m), d.wires)
        for d in P.digits:
            for c in range(1, d.p):
                self.X(R.reduce(c * d.p ** d.pos * u1), controls=[(d.wires, c)])
        self.fourier_g(P)

    def measured_value_order(self, P: SyndromePart) -> list[Digit]:
        """Digits in the order (most significant first) in which the measured value is read."""
        if P.kind == "X" and P.f == 2:
            return [P.digits[0], P.digits[1]]  # after G: lo holds k1 (high), hi holds k0 (low)
        return list(reversed(P.digits))

    # expected measurement value of a part for a given error
    def expected_part(self, P: SyndromePart, err) -> int:
        R = self.ring
        q = R.q
        e = R.reduce(np.asarray(err).reshape(1, 1, 2))
        if P.kind == "Z":
            t = int(R.trace(R.hermitian(P.generator.reshape(1, 1, 2), e))[0])
            return (t // P.scale) % (P.p ** P.f)
        u1 = R.reduce(P.scale * P.generator).reshape(1, 1, 2)
        t = int(R.trace(R.hermitian(e, u1))[0])
        unit = q // P.p ** P.f
        assert t % unit == 0
        return (t // unit) % (P.p ** P.f)

    def measure_part(self, P: SyndromePart, reset: bool):
        """Mid-circuit measurement of every ancilla qubit of the part; returns MeasurementValue."""
        val = 0
        for d in self.measured_value_order(P):
            dv = 0
            for wire in d.wires:
                dv = dv * 2 + qml.measure(wire, reset=reset)
            val = val * d.p + dv
        return val

    # ------------------------------------------------------------------ resources
    def wire_summary(self) -> dict:
        return {"data_qubits": self.L.n_qubits, "logical_qubits": len(self.logical_wires),
                "ancilla_qubits": len(self.anc_wires), "total_wires": self.n_wires,
                "digits": [(d.name, d.p, r) for d, r in zip(self.L.digits, self.roles)],
                "parts": [(P.kind, P.gen_index, P.p, P.f) for P in self.parts], "reuse_ancilla": self.reuse}
