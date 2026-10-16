"""Single-qubit noise channels (Kraus form) and their application to batched density matrices.

Noise model used in Phase 6: *code capacity* - every physical qubit of the embedded code
suffers the same independent channel once; encoding, syndrome extraction and recovery are ideal.
"""
from __future__ import annotations

import numpy as np
import torch

I2 = np.eye(2, dtype=complex)
PX = np.array([[0, 1], [1, 0]], dtype=complex)
PY = np.array([[0, -1j], [1j, 0]], dtype=complex)
PZ = np.array([[1, 0], [0, -1]], dtype=complex)


def kraus_1q(name: str, p: float) -> list[np.ndarray]:
    if name == "bit_flip":
        return [np.sqrt(1 - p) * I2, np.sqrt(p) * PX]
    if name == "phase_flip":
        return [np.sqrt(1 - p) * I2, np.sqrt(p) * PZ]
    if name == "depolarizing":
        return [np.sqrt(1 - p) * I2, np.sqrt(p / 3) * PX, np.sqrt(p / 3) * PY, np.sqrt(p / 3) * PZ]
    if name == "amplitude_damping":
        return [np.array([[1, 0], [0, np.sqrt(1 - p)]], dtype=complex), np.array([[0, np.sqrt(p)], [0, 0]], dtype=complex)]
    if name == "phase_damping":
        return [np.array([[1, 0], [0, np.sqrt(1 - p)]], dtype=complex), np.array([[0, 0], [0, np.sqrt(p)]], dtype=complex)]
    raise ValueError(name)


def check_cptp(ks: list[np.ndarray]) -> float:
    return float(np.abs(sum(k.conj().T @ k for k in ks) - I2).max())


def apply_1q_channel(rho: torch.Tensor, n_qubits: int, ks: list[np.ndarray], qubits=None) -> torch.Tensor:
    """rho: (B, D, D) with D = 2^n (big-endian: qubit 0 is the most significant bit)."""
    B, D, _ = rho.shape
    assert D == 2 ** n_qubits
    qubits = range(n_qubits) if qubits is None else qubits
    Kt = [torch.tensor(k, dtype=rho.dtype, device=rho.device) for k in ks]
    for i in qubits:
        left, right = 2 ** i, 2 ** (n_qubits - i - 1)
        r = rho.reshape(B, left, 2, right, left, 2, right)
        out = torch.zeros_like(r)
        for K in Kt:
            out += torch.einsum("ab,xibjkcl,dc->xiajkdl", K, r, K.conj())
        rho = out.reshape(B, D, D)
    return rho
