"""Numerical-simulation sanity checks for the AWGN reconstruction."""
import numpy as np
import pytest
import torch

from epsqec.simulation import awgn as A
from epsqec.simulation import constellations as C


def test_constellation_sizes_and_geometry():
    assert len(C.gaussian_residues(5)) == 25 and len(C.gaussian_residues(3 + 4j)) == 25
    assert len(C.gaussian_residues(25)) == 625
    cs = C.coded_subset(25, 2 + 1j)
    assert len(cs) == 125 and abs(C.min_distance(cs) - np.sqrt(5)) < 1e-12
    assert len(C.cross_qam(32)) == 32 and len(C.cross_qam(128)) == 128


def test_coded_constellation_equivalent_to_128qam_geometry():
    """d_min^2/E_s of the 125 coded points is within 2% of cross 128-QAM (equal-rate baseline)."""
    a = C.describe(C.coded_subset(25, 2 + 1j))["dmin2_over_Es"]
    b = C.describe(C.cross_qam(128))["dmin2_over_Es"]
    assert abs(a - b) / b < 0.02


def test_16qam_ser_matches_closed_form_cpu():
    rows = A.simulate_ser(A.Detector("ml", C.square_qam(16)), [12.0], min_errors=10**9,
                          max_symbols=1_000_000, batch=500_000, seed=3, device="cpu")
    exact = float(A.ser_square_qam_exact(16, 12.0))
    assert rows[0]["ci_low"] <= exact <= rows[0]["ci_high"]


def test_ring_receiver_equals_ml_in_interior_only():
    """Ring receiver (round + mod w) wraps at the edge, so its SER is >= ML SER."""
    det_r = A.Detector("ring", C.gaussian_residues(5), w=5)
    det_m = A.Detector("ml", C.gaussian_residues(5))
    r = A.simulate_ser(det_r, [14.0], min_errors=10**9, max_symbols=400_000, seed=4, device="cpu")[0]
    m = A.simulate_ser(det_m, [14.0], min_errors=10**9, max_symbols=400_000, seed=4, device="cpu")[0]
    assert r["ser"] >= m["ser"]


@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_gpu_and_cpu_agree_statistically():
    det = A.Detector("ml", C.square_qam(16))
    g = A.simulate_ser(det, [14.0], min_errors=10**9, max_symbols=2_000_000, seed=5, device="cuda")[0]
    det2 = A.Detector("ml", C.square_qam(16))
    c = A.simulate_ser(det2, [14.0], min_errors=10**9, max_symbols=2_000_000, seed=6, device="cpu")[0]
    assert g["ci_low"] <= c["ci_high"] and c["ci_low"] <= g["ci_high"]


def test_clopper_pearson_zero_errors():
    lo, hi = A.clopper_pearson(0, 1000)
    assert lo == 0.0 and 0.003 < hi < 0.004
