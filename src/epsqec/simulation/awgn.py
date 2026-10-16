"""Monte-Carlo SER over complex AWGN (torch; CUDA if available, CPU fallback).

Conventions (stated explicitly because the paper does not publish them):
  * constellation scaled to unit average symbol energy Es = 1, uniform symbol priors;
  * SNR = Es/N0;  complex noise n = sigma (g1 + i g2), g ~ N(0,1), sigma^2 = N0/2 per dimension;
  * per SNR point, simulate in batches until  errors >= min_errors  or  symbols >= max_symbols;
  * SER confidence interval: exact Clopper-Pearson (two-sided, level `ci`);
  * each SNR point uses its own generator seeded with  seed + round(1000*snr_db)  so points are
    reproducible independently of the SNR grid.

Detectors
  "ml"        : minimum Euclidean distance over the finite constellation (exact ML for AWGN);
  "ring"      : the Gaussian-integer receiver suggested by Appendix A.2 - rescale, round to the
                nearest Gaussian integer, reduce mod w with gaussian_modulo (wraps at the edge);
  "coset"     : Section 4.2 hard-decision coset decoder for C = <g> inside Z[i]/(w):
                round -> reduce mod w -> syndrome S = y mod g -> c_hat = (y - S) mod w.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
import torch
from scipy.stats import beta

from .constellations import normalize


def clopper_pearson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    a = 1 - level
    lo = 0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def pick_device(pref: str = "auto") -> torch.device:
    if pref == "cpu":
        return torch.device("cpu")
    if pref in ("auto", "cuda") and torch.cuda.is_available():
        return torch.device("cuda")
    if pref == "cuda":
        raise RuntimeError("CUDA requested but not available")
    return torch.device("cpu")


def _gmod(zr, zi, wr, wi):
    """torch version of Appendix A.2 gaussian_modulo on split real/imag tensors."""
    n = wr * wr + wi * wi
    qr = (zr * wr + zi * wi) / n
    qi = (zi * wr - zr * wi) / n
    qr, qi = torch.round(qr), torch.round(qi)
    return zr - (qr * wr - qi * wi), zi - (qr * wi + qi * wr)


@dataclass
class Detector:
    kind: str  # ml | ring | coset
    points: np.ndarray  # un-normalised complex constellation (labels are Gaussian integers here)
    w: complex | None = None
    g: complex | None = None
    tx_points: np.ndarray | None = None  # for "coset": transmitted subset (labels); else = points
    normalize_on: str = "tx"  # "tx": unit energy of the transmitted set; "all": of `points`
    _cache: dict = field(default_factory=dict, repr=False)

    def prepare(self, device):
        tx = self.points if self.tx_points is None else self.tx_points
        p_all = self.points
        # energy normalisation uses the TRANSMITTED set (Section 4: "average symbol energy of all
        # constellations is normalised to unity")
        _, s = normalize(tx if self.normalize_on == "tx" else p_all)
        self._cache["s"] = s
        self._cache["Es_tx"] = float(np.mean(np.abs(tx / s) ** 2))
        self._cache["tx"] = torch.tensor(tx / s, dtype=torch.complex64, device=device)
        if self.kind == "ml":
            self._cache["ref"] = self._cache["tx"]
        else:
            # integer lattice label -> index table for the transmitted set
            R = int(np.max(np.abs(np.concatenate([p_all.real, p_all.imag])))) + 2
            self._cache["R"] = R
            table = torch.full(((2 * R + 1) ** 2,), -1, dtype=torch.long, device=device)
            lab = torch.tensor(
                (np.round(tx.real).astype(int) + R) * (2 * R + 1) + (np.round(tx.imag).astype(int) + R),
                device=device,
            )
            table[lab] = torch.arange(len(tx), device=device)
            self._cache["table"] = table

    def decide(self, rx: torch.Tensor) -> torch.Tensor:
        c = self._cache
        if self.kind == "ml":
            ref = c["ref"]
            out = torch.empty(rx.shape[0], dtype=torch.long, device=rx.device)
            step = max(1, (1 << 26) // ref.shape[0])
            for s0 in range(0, rx.shape[0], step):
                d = (rx[s0:s0 + step, None] - ref[None, :]).abs()
                out[s0:s0 + step] = d.argmin(dim=1)
            return out
        z = rx * c["s"]
        zr, zi = torch.round(z.real), torch.round(z.imag)
        wr, wi = float(self.w.real), float(self.w.imag)
        yr, yi = _gmod(zr, zi, wr, wi)
        if self.kind == "coset":
            gr, gi = float(self.g.real), float(self.g.imag)
            sr, si = _gmod(yr, yi, gr, gi)  # syndrome / coset leader
            yr, yi = _gmod(yr - sr, yi - si, wr, wi)
        R = c["R"]
        ir = torch.round(yr).long() + R
        ii = torch.round(yi).long() + R
        ok = (ir >= 0) & (ir <= 2 * R) & (ii >= 0) & (ii <= 2 * R)
        lab = torch.where(ok, ir * (2 * R + 1) + ii, torch.zeros_like(ir))
        idx = c["table"][lab]
        return torch.where(ok, idx, torch.full_like(idx, -1))


def simulate_ser(det: Detector, snr_db: list[float], *, min_errors: int = 300, max_symbols: int = 10**7,
                 batch: int = 1_000_000, seed: int = 0, device: str = "auto", ci: float = 0.95) -> list[dict]:
    dev = pick_device(device)
    det.prepare(dev)
    tx = det._cache["tx"]
    M = tx.shape[0]
    rows = []
    for snr in snr_db:
        n0 = 10 ** (-snr / 10)
        sigma = math.sqrt(n0 / 2)
        gen = torch.Generator(device=dev).manual_seed(int(seed + round(1000 * snr)))
        err = n = 0
        t0 = time.perf_counter()
        while err < min_errors and n < max_symbols:
            b = int(min(batch, max_symbols - n))
            idx = torch.randint(0, M, (b,), generator=gen, device=dev)
            noise = torch.randn((b, 2), generator=gen, device=dev) * sigma
            rx = tx[idx] + torch.complex(noise[:, 0], noise[:, 1])
            dec = det.decide(rx)
            err += int((dec != idx).sum().item())
            n += b
        if dev.type == "cuda":
            torch.cuda.synchronize()
        lo, hi = clopper_pearson(err, n, ci)
        rows.append({"snr_db": snr, "symbols": n, "errors": err, "ser": err / n,
                     "ci_low": lo, "ci_high": hi, "seconds": time.perf_counter() - t0,
                     "device": dev.type, "M_tx": int(M), "detector": det.kind})
    return rows


# ------------------------------------------------------------------ closed-form references
def qfunc(x):
    from scipy.special import erfc

    return 0.5 * erfc(np.asarray(x) / np.sqrt(2))


def ser_square_qam_exact(M: int, snr_db):
    """Exact SER of square M-QAM with ML detection, Es/N0 = snr."""
    snr = 10 ** (np.asarray(snr_db) / 10)
    m = np.sqrt(M)
    p = 2 * (1 - 1 / m) * qfunc(np.sqrt(3 * snr / (M - 1)))
    return 1 - (1 - p) ** 2
