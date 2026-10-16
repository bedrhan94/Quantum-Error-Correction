"""Signal constellations used to reconstruct Section 4 (Figures 1-3) of the paper.

The paper does not publish its simulation code beyond ``gaussian_modulo`` (Appendix A.2), so
every constellation here is an explicit, documented choice:

* square M-QAM (16, 256, 1024): odd-integer grid,
* cross 32-QAM and cross 128-QAM: 6x6 minus 4 corners / 12x12 minus 4 (2x2) corner blocks,
* Gaussian-integer residue constellations  Z[i]/(w): the N(w) minimal residues
  r = z - round(z / w) w  (Appendix A.2 mapping), e.g. w = 5  -> 5x5 grid  ("Z_5[i]"),
  w = 3+4i -> tilted 25-point set ("Z[i]/(2+i)^2"), w = 25 -> 25x25 grid ("Z_25[i]"),
* the coded subset  <g> mod w  (Section 4.2: C = <2+i> inside Z_25[i], 125 points).

Every constellation is returned un-normalised together with the Gaussian-integer label of each
point; ``normalize`` scales to unit average energy (uniform priors), as stated in Section 4.
"""
from __future__ import annotations

import numpy as np


def square_qam(M: int) -> np.ndarray:
    m = int(round(np.sqrt(M)))
    assert m * m == M
    a = np.arange(-(m - 1), m, 2)
    return (a[:, None] + 1j * a[None, :]).reshape(-1)


def cross_qam(M: int) -> np.ndarray:
    """Standard cross constellations: 32 = 6x6 - 4 corners, 128 = 12x12 - 16 corner points."""
    if M == 32:
        g, cut = 6, 1
    elif M == 128:
        g, cut = 12, 2
    else:
        raise ValueError(M)
    a = np.arange(-(g - 1), g, 2)
    pts = (a[:, None] + 1j * a[None, :]).reshape(-1)
    lim = g - 1 - 2 * cut  # coordinates beyond lim on BOTH axes are corner points
    keep = ~((np.abs(pts.real) > lim) & (np.abs(pts.imag) > lim))
    out = pts[keep]
    assert len(out) == M, len(out)
    return out


def gaussian_modulo(z, w):
    """Appendix A.2:  z - round(z / w) * w  (np.round = round-half-to-even, as printed)."""
    qq = z * np.conj(w) / (np.abs(w) ** 2)
    q_r = np.round(qq.real) + 1j * np.round(qq.imag)
    return z - q_r * w


def gaussian_residues(w: complex) -> np.ndarray:
    """The N(w) residues of Z[i]/(w) as returned by gaussian_modulo, ordered canonically."""
    w = complex(w)
    N = int(round(abs(w) ** 2))
    R = int(np.ceil(abs(w))) + 2
    a = np.arange(-R, R + 1)
    z = (a[:, None] + 1j * a[None, :]).reshape(-1)
    r = gaussian_modulo(z, w)
    r = np.unique(np.round(r.real).astype(int) + 1j * np.round(r.imag).astype(int))
    if len(r) != N:
        raise AssertionError(f"expected {N} residues for w={w}, got {len(r)}")
    return r


def coded_subset(w: complex, g: complex) -> np.ndarray:
    """Residues (mod w) of the ideal <g>: {gaussian_modulo(g r, w)}."""
    res = gaussian_residues(w)
    c = gaussian_modulo(g * res, w)
    c = np.unique(np.round(c.real).astype(int) + 1j * np.round(c.imag).astype(int))
    return c


def normalize(points: np.ndarray) -> tuple[np.ndarray, float]:
    """Scale to unit average energy; returns (scaled points, scale factor s with x_scaled = x / s)."""
    es = np.mean(np.abs(points) ** 2)
    s = np.sqrt(es)
    return points / s, float(s)


def min_distance(points: np.ndarray) -> float:
    d = np.abs(points[:, None] - points[None, :])
    d[np.diag_indices(len(points))] = np.inf
    return float(d.min())


def describe(points: np.ndarray) -> dict:
    p, s = normalize(points)
    return {
        "M": int(len(points)),
        "bits_per_symbol": float(np.log2(len(points))),
        "avg_energy_unnormalised": float(np.mean(np.abs(points) ** 2)),
        "dmin_unnormalised": min_distance(points),
        "dmin_normalised": min_distance(p),
        "dmin2_over_Es": min_distance(p) ** 2,
    }
