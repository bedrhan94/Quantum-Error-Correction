"""Batched Monte-Carlo trajectories of qudit-level Pauli noise on R^n ring codes (torch, CPU/GPU).

Per trial: |psi> (fixed random logical state) -> X(u_b) Z(v_b) with u_b, v_b drawn from the
*unit-shift* model (every real/imaginary coordinate of every component independently shifted by
+-1 with probability p, i.e. +1 w.p. p/2, -1 w.p. p/2) -> generator eigenvalues measured as
expectation values of the actual operators -> table-lookup correction (alternative-design
transversals T_X, T_Z) -> success iff |<psi|phi>|^2 > 1 - tol.
The exact success probability for the same model is computed by enumeration in
``exact_unit_shift`` so the simulator is validated against an independent number.
"""
from __future__ import annotations

import itertools
import time

import numpy as np
import torch

from ..stabilizer import min_weight_transversal


class RingMC:
    def __init__(self, built, device="cpu"):
        self.b = built
        self.dev = torch.device(device)
        sp, code, R = built.space, built.code, built.ring
        self.q, self.n, self.dim = R.q, sp.n, sp.dim
        self.TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // built.C2.size)
        self.TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // built.C1_dual.size)
        self.lutX = {int(k): a for k, a in zip(code.zsyn_key(self.TX), self.TX)}
        self.lutZ = {int(k): f for k, f in zip(code.xsyn_key(self.TZ), self.TZ)}
        V = code.logical_states(built.eps)
        rng = np.random.default_rng(0)
        c = rng.normal(size=len(V)) + 1j * rng.normal(size=len(V))
        self.psi = torch.tensor((c / np.linalg.norm(c)) @ V, dtype=torch.complex64, device=self.dev)
        vecs = sp.vecs  # (dim, n, 2)
        self.xa = torch.tensor(vecs[..., 0], device=self.dev)  # (dim, n)
        self.xb = torch.tensor(vecs[..., 1], device=self.dev)
        # float32 copies for the phase exponent (CUDA has no int64 matmul); all partial sums are
        # integers < n q^2 < 2^24, hence exact in float32
        assert self.n * self.q * self.q < 2**24
        self.xa_f, self.xb_f = self.xa.T.float(), self.xb.T.float()
        self.w = torch.tensor([R.size ** j for j in range(self.n)], device=self.dev)
        self.zg = [torch.tensor(np.asarray(v), device=self.dev) for v in code.zgens]
        self.xg = [torch.tensor(np.asarray(u), device=self.dev) for u in code.xgens]

    # ---------------------------------------------------------------- batched Paulis
    def _phase_exponent(self, v):  # v (B, n, 2) -> Tr<v, x> (B, dim)
        c, d = v[..., 0], v[..., 1]
        ca, cb = ((c + d) % self.q).float(), ((d - c) % self.q).float()
        return torch.round(ca @ self.xa_f + cb @ self.xb_f).long() % self.q

    def apply_Z(self, v, phi):
        e = self._phase_exponent(v).to(torch.float32)
        return phi * torch.polar(torch.ones_like(e), 2 * np.pi * e / self.q)

    def apply_X(self, u, phi):
        a = (self.xa[None] - u[:, None, :, 0]) % self.q  # (B, dim, n)
        b = (self.xb[None] - u[:, None, :, 1]) % self.q
        idx = ((a * self.q + b) * self.w).sum(-1)
        return torch.gather(phi, 1, idx)

    # ---------------------------------------------------------------- syndromes
    def syndromes(self, phi):
        """Eigenvalues of every generator from the state -> integer syndromes (B, #gens)."""
        p = (phi.abs() ** 2)
        zs, xs = [], []
        for v in self.zg:
            e = self._phase_exponent(v[None].expand(phi.shape[0], -1, -1)).to(torch.float32)
            lam = (p * torch.polar(torch.ones_like(e), 2 * np.pi * e / self.q)).sum(1)
            zs.append(torch.round(torch.angle(lam) * self.q / (2 * np.pi)).long() % self.q)
        for u in self.xg:
            sh = self.apply_X(u[None].expand(phi.shape[0], -1, -1), phi)
            lam = (phi.conj() * sh).sum(1)
            xs.append(torch.round(torch.angle(lam) * self.q / (2 * np.pi)).long() % self.q)
        stack = lambda L: torch.stack(L, 1) if L else torch.zeros((phi.shape[0], 0), dtype=torch.long, device=self.dev)
        return stack(zs), stack(xs)

    def run(self, p: float, trials: int, batch: int, seed: int, tol: float = 1e-3, model: str = "unit_shift") -> dict:
        """model = "unit_shift" (default, see module docstring) or "depolarizing": with probability p
        a uniformly random NON-identity qudit Pauli X(u)Z(v), (u, v) in R^n x R^n minus (0, 0)."""
        gen = np.random.default_rng(seed)
        ok = hits_total = 0
        t0 = time.perf_counter()
        if self.dev.type == "cuda":
            torch.cuda.reset_peak_memory_stats()
        q = self.q
        wkey = lambda s: (s.cpu().numpy() * (q ** np.arange(s.shape[1]))).sum(1) if s.shape[1] else np.zeros(s.shape[0], np.int64)
        done = 0
        while done < trials:
            B = min(batch, trials - done)
            if model == "depolarizing":
                hit = gen.random(B) < p
                hits_total += int(hit.sum())
                dim2 = self.dim * self.dim
                idx = gen.integers(1, dim2, size=B)  # uniform over the d^2 - 1 non-identity Paulis
                iu, iv = np.divmod(idx, self.dim)
                vecs = self.b.space.vecs
                shiftX = np.where(hit[:, None, None], vecs[iu], 0)
                shiftZ = np.where(hit[:, None, None], vecs[iv], 0)
            else:
                shiftX = gen.choice([-1, 0, 1], p=[p / 2, 1 - p, p / 2], size=(B, self.n, 2))
                shiftZ = gen.choice([-1, 0, 1], p=[p / 2, 1 - p, p / 2], size=(B, self.n, 2))
            u = torch.tensor(shiftX % q, device=self.dev)
            v = torch.tensor(shiftZ % q, device=self.dev)
            phi = self.psi[None].expand(B, -1).clone()
            phi = self.apply_X(u, self.apply_Z(v, phi))
            zs, xs = self.syndromes(phi)
            ka, kz = wkey(zs), wkey(xs)
            a = np.array([self.lutX[int(k)] for k in ka]) % q
            f = np.array([self.lutZ[int(k)] for k in kz]) % q
            phi = self.apply_X(torch.tensor((-a) % q, device=self.dev), phi)
            phi = self.apply_Z(torch.tensor((-f) % q, device=self.dev), phi)
            fid = (self.psi.conj()[None] * phi).sum(1).abs() ** 2
            ok += int((fid > 1 - tol).sum().item())
            done += B
        if self.dev.type == "cuda":
            torch.cuda.synchronize()
        res = {"p": p, "trials": trials, "successes": ok, "logical_error_rate": 1 - ok / trials,
               "seconds": time.perf_counter() - t0, "device": self.dev.type, "batch": batch, "model": model}
        if model == "depolarizing":
            res["hits"] = hits_total
        if self.dev.type == "cuda":
            res["gpu_peak_MB"] = torch.cuda.max_memory_allocated() / 2**20
        return res

    # ---------------------------------------------------------------- exact reference
    def correctable_counts(self) -> tuple[int, int]:
        """(N_X, N_Z): number of X(u) / Z(v), u, v in R^n, fixed by the LUT recovery."""
        R, code, V = self.b.ring, self.b.code, self.b.space.vecs
        a = np.array([self.lutX[int(k)] for k in code.zsyn_key(V)])
        f = np.array([self.lutZ[int(k)] for k in code.xsyn_key(V)])
        return int(self.b.C1.contains(R.sub(V, a)).sum()), int(self.b.D_true.contains(R.sub(V, f)).sum())

    def exact_depolarizing(self, p: float) -> float:
        """Exact success probability: (1 - p) + p (N_X N_Z - 1) / (d^2 - 1)."""
        NX, NZ = self.correctable_counts()
        d = self.dim
        return (1 - p) + p * (NX * NZ - 1) / (d * d - 1)

    def unit_shift_pattern_counts(self) -> dict:
        """How many of the 3^(2n) X-shift / Z-shift patterns of the unit-shift model are corrected."""
        R, code = self.b.ring, self.b.code
        raw = np.array(list(itertools.product([-1, 0, 1], repeat=2 * self.n))).reshape(-1, self.n, 2)
        pats = R.reduce(raw)
        a = np.array([self.lutX[int(k)] for k in code.zsyn_key(pats)])
        f = np.array([self.lutZ[int(k)] for k in code.xsyn_key(pats)])
        okX = self.b.C1.contains(R.sub(pats, a))
        okZ = self.b.D_true.contains(R.sub(pats, f))
        fmt = lambda m: " ".join(str(tuple(int(t) for t in r.ravel())) for r in raw[~m])
        return {"patterns": len(pats), "X_corrected": int(okX.sum()), "Z_corrected": int(okZ.sum()),
                "X_uncorrected_shifts": fmt(okX), "Z_uncorrected_shifts": fmt(okZ)}

    def exact_unit_shift(self, p: float) -> float:
        """Exact success probability for the same model by enumerating all 3^(2n) shift patterns
        separately for the X and the Z part (independent)."""
        R, code = self.b.ring, self.b.code
        pats = np.array(list(itertools.product([-1, 0, 1], repeat=2 * self.n))).reshape(-1, self.n, 2)
        prob = np.prod(np.where(pats == 0, 1 - p, p / 2), axis=(1, 2))
        E = R.reduce(pats)
        a = np.array([self.lutX[int(k)] for k in code.zsyn_key(E)])
        f = np.array([self.lutZ[int(k)] for k in code.xsyn_key(E)])
        okX = self.b.C1.contains(R.sub(E, a))
        okZ = self.b.D_true.contains(R.sub(E, f))
        return float((prob * okX).sum() * (prob * okZ).sum())
