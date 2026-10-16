"""Closed-form checks of the Phase 6 noise engine (the ring-vs-baseline conclusions rest on it)."""
import numpy as np
import pytest
import torch

from epsqec.noise import (five_qubit_code, five_qubit_x3_metrics, logical_channel_metrics, modular_code_embedded,
                          ring_code_embedded, unencoded_embedded)
from epsqec.noise.channels import check_cptp, kraus_1q
from epsqec.noise.montecarlo import RingMC
from epsqec.simulation.awgn import clopper_pearson


@pytest.mark.parametrize("ch", ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "phase_damping"])
def test_channels_are_cptp(ch):
    assert check_cptp(kraus_1q(ch, 0.137)) < 1e-12


def test_recovery_isometries_complete(built):
    for c in (ring_code_embedded(built("Z25")), modular_code_embedded(), unencoded_embedded(5), five_qubit_code()):
        assert c.completeness_error() < 1e-12


def test_zero_noise_zero_logical_error(built):
    for c in (ring_code_embedded(built("Z25")), modular_code_embedded(), unencoded_embedded(5)):
        assert abs(logical_channel_metrics(c, "depolarizing", 0.0)["logical_error_rate"]) < 1e-12


@pytest.mark.parametrize("p", [1e-3, 1e-2, 0.1])
def test_unencoded_bitflip_closed_form(p):
    """5 levels {0..4} in 3 qubits; bit flips: F_e = (1-p)^3 exactly (any flip changes the label or leaks)."""
    r = logical_channel_metrics(unencoded_embedded(5), "bit_flip", p)
    assert abs(r["entanglement_fidelity"] - (1 - p) ** 3) < 1e-12


def test_five_qubit_block_bitflip_leading_order():
    """[[5,1,3]] is perfect: every weight-2 error is a logical error -> 1 - F_e(block) ~ 10 p^2 (1-p)^3."""
    p = 1e-4
    fq = five_qubit_code()
    r = logical_channel_metrics(fq, "bit_flip", p)
    approx = 10 * p**2 * (1 - p) ** 3
    assert abs(r["logical_error_rate"] - approx) / approx < 2e-3
    r3 = five_qubit_x3_metrics(fq, "bit_flip", p)
    assert 2.0 * approx < r3["logical_error_rate"] < 3.2 * approx  # three blocks, 5 of 8 levels used


def test_gpu_matches_cpu_density_matrix(built):
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
    c = ring_code_embedded(built("Z25"))
    a = logical_channel_metrics(c, "amplitude_damping", 0.05)
    b = logical_channel_metrics(c, "amplitude_damping", 0.05, device="cuda", dtype=torch.complex64)
    assert abs(a["logical_error_rate"] - b["logical_error_rate"]) < 1e-5


def test_ring_mc_within_ci_of_exact(built):
    mc = RingMC(built("Z25"), "cpu")
    r = mc.run(0.05, 6000, 2000, seed=11)
    lo, hi = clopper_pearson(r["trials"] - r["successes"], r["trials"], 0.99)
    assert lo <= 1 - mc.exact_unit_shift(0.05) <= hi


def test_ring_unit_shift_exact_is_p_squared(built):
    """Z_25[i]: T_X = {0, +-1, +-i}; failure iff both coordinates shifted -> LER = p^2 (Z part never fails)."""
    mc = RingMC(built("Z25"), "cpu")
    for p in (0.01, 0.1):
        assert abs((1 - mc.exact_unit_shift(p)) - p * p) < 1e-12
