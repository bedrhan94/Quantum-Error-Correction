"""Regression values frozen from the first verified runs (2026-10-15).  A change here means the
implementation's output changed - investigate before updating the numbers."""
import numpy as np
import pytest

from epsqec.css import PAPER_EXAMPLES, analyze_principal_pair

FROZEN = {
    "Z25": {"C1": 25, "C2": 125, "K": 5, "dual_true": 5, "dual_def6": 125, "C1_dual": 25},
    "Z85": {"C1": 85, "C2": 1445, "K": 17, "dual_true": 5, "dual_def6": 1445, "C1_dual": 85},
    "Z325": {"C1": 1625, "C2": 8125, "K": 5, "dual_true": 13, "dual_def6": 8125, "C1_dual": 65},
}


@pytest.mark.parametrize("key", list(FROZEN))
def test_frozen_algebra(key):
    pe = PAPER_EXAMPLES[key]
    _, r = analyze_principal_pair(pe.q, pe.alpha1, pe.alpha2)
    f = FROZEN[key]
    assert (r["size_C1_enumerated"], r["size_C2_enumerated"], r["K"], r["size_C2_dual_true"],
            r["size_C2_dual_def6"], r["size_C1_dual_true"]) == (f["C1"], f["C2"], f["K"], f["dual_true"],
                                                               f["dual_def6"], f["C1_dual"])


def test_frozen_transversal_original_canonical_z25(built):
    from epsqec.decoder import multiples_transversal

    b = built("Z25")
    eps = multiples_transversal(b.ring, b.ring.mul(b.ring.elem(0, 1), b.ring.elem(2, 1)), 5)
    assert [b.ring.fmt(e[0]) for e in eps] == ["0+0i", "24+2i", "23+4i", "22+6i", "21+8i"]


def test_frozen_alternative_correctable_x_set_z25(built):
    from epsqec.stabilizer import min_weight_transversal

    b = built("Z25")
    TX = min_weight_transversal(b.space, b.code.zsyn_key, 5)
    assert sorted(b.ring.fmt(t[0]) for t in TX) == sorted(["0+0i", "0+1i", "0+24i", "1+0i", "24+0i"])
