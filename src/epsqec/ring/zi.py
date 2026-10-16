"""Exact arithmetic in the Gaussian integers Z[i] (not reduced mod q).

Used only for *formula-based* cross-checks (norms, gcds, Gaussian factorisation of q).
Every quantity derived here is also checked against brute-force enumeration in Z_q[i].
Elements are plain Python int tuples (a, b) meaning a + b i.
"""
from __future__ import annotations

from fractions import Fraction

GI = tuple[int, int]


def mul(x: GI, y: GI) -> GI:
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def conj(x: GI) -> GI:
    return (x[0], -x[1])


def norm(x: GI) -> int:
    """Algebraic norm N(a+bi) = a^2 + b^2 in Z (no reduction)."""
    return x[0] * x[0] + x[1] * x[1]


def _round_half_away(fr: Fraction) -> int:
    # deterministic rounding, exact on rationals
    n, d = fr.numerator, fr.denominator
    q, r = divmod(2 * n + d, 2 * d)
    return q


def divmod_gi(x: GI, y: GI) -> tuple[GI, GI]:
    """Euclidean division x = qy + r with N(r) <= N(y)/2 (rounding of x/y)."""
    if y == (0, 0):
        raise ZeroDivisionError("division by 0 in Z[i]")
    num = mul(x, conj(y))
    n = norm(y)
    qq = (_round_half_away(Fraction(num[0], n)), _round_half_away(Fraction(num[1], n)))
    qy = mul(qq, y)
    return qq, (x[0] - qy[0], x[1] - qy[1])


def divides(d: GI, x: GI) -> bool:
    """True iff d | x in Z[i]  <=>  x * conj(d) == 0 (mod N(d)) componentwise."""
    if d == (0, 0):
        return x == (0, 0)
    n = norm(d)
    num = mul(x, conj(d))
    return num[0] % n == 0 and num[1] % n == 0


def gcd(x: GI, y: GI) -> GI:
    """A gcd in Z[i] (defined up to units)."""
    while y != (0, 0):
        _, r = divmod_gi(x, y)
        x, y = y, r
    return normalize_unit(x)


def normalize_unit(x: GI) -> GI:
    """Pick the associate with a > 0, b >= 0 (unique representative up to units)."""
    if x == (0, 0):
        return x
    for u in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        y = mul(x, u)
        if y[0] > 0 and y[1] >= 0:
            return y
    raise AssertionError("unreachable")


def gaussian_prime_above(p: int) -> GI:
    """For a rational prime p = 1 (mod 4) return pi = a + bi with N(pi) = p (a > b > 0)."""
    if p % 4 != 1:
        raise ValueError(f"{p} does not split in Z[i]")
    for a in range(1, int(p ** 0.5) + 1):
        b2 = p - a * a
        b = int(round(b2 ** 0.5))
        if b * b == b2 and b > 0:
            return normalize_unit((max(a, b), min(a, b)))
    raise ValueError(f"no decomposition for {p}")


def ideal_index_in_Zq(alpha: GI, q: int) -> int:
    """|Z_q[i] / <alpha>| = N(gcd(alpha, q)) (correct norm formula for arbitrary alpha).

    The paper uses |<alpha>| = q^2 / N(alpha), which coincides with this only when alpha | q.
    """
    g = gcd(alpha, (q, 0))
    return norm(g)
