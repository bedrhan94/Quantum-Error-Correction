"""Exact logical-channel metrics for an EmbeddedCode under i.i.d. single-qubit noise.

Definitions (stated because QEC papers use several):
  * logical error rate  = 1 - F_e, entanglement infidelity of the logical channel
                          (encode -> noise -> ideal recovery -> decode) on the K-dim logical space;
  * average fidelity    = (K F_e + 1) / (K + 1)  (Horodecki/Nielsen relation);
  * recovery success    = mean over logical basis inputs |j> of <j| out |j>;
  * leakage             = mean over basis inputs of the population outside the embedded subspace
                          after the noise (lost by the recovery);
  * no-recovery F_e     = same channel without recovery (decode only), for reference.
"""
from __future__ import annotations

import time

import numpy as np
import torch

from .channels import apply_1q_channel, kraus_1q
from .codes import EmbeddedCode


def _inputs(V: np.ndarray) -> np.ndarray:
    """All K^2 encoded operators |psi_i><psi_j|  -> (K^2, D, D)."""
    K = V.shape[0]
    return np.einsum("id,je->ijde", V, V.conj()).reshape(K * K, V.shape[1], V.shape[1])


def logical_channel_metrics(code: EmbeddedCode, channel: str, p: float, device="cpu",
                            dtype=torch.complex128, chunk: int | None = None) -> dict:
    """chunk: number of the K^2 input operators |psi_i><psi_j| propagated at once (memory bound)."""
    t0 = time.perf_counter()
    K, D = code.K, code.V.shape[1]
    if device != "cpu":
        torch.cuda.reset_peak_memory_stats()
    B = torch.tensor(code.B, dtype=dtype, device=device)  # (S, D, K)
    Vt = torch.tensor(code.V, dtype=dtype, device=device)
    pairs = [(i, j) for i in range(K) for j in range(K)]
    chunk = chunk or len(pairs)
    out = np.zeros((K * K, K, K), dtype=complex)
    out_nr = np.zeros((K * K, K, K), dtype=complex)
    diag_rho = np.zeros((K * K, D))
    ks = kraus_1q(channel, p)
    for s0 in range(0, len(pairs), chunk):
        sel = pairs[s0:s0 + chunk]
        Vi = Vt[[i for i, _ in sel]]
        Vj = Vt[[j for _, j in sel]]
        rho = torch.einsum("xd,xe->xde", Vi, Vj.conj())
        rho = apply_1q_channel(rho, code.n_qubits, ks)
        out[s0:s0 + len(sel)] = torch.einsum("sdk,xde,sel->xkl", B.conj(), rho, B).cpu().numpy()
        out_nr[s0:s0 + len(sel)] = torch.einsum("kd,xde,le->xkl", Vt.conj(), rho, Vt).cpu().numpy()
        diag_rho[s0:s0 + len(sel)] = torch.diagonal(rho, dim1=1, dim2=2).real.cpu().numpy()
        del rho
    out = out.reshape(K, K, K, K)
    out_nr = out_nr.reshape(K, K, K, K)
    diag_rho = diag_rho.reshape(K, K, D)
    idx = np.arange(K)
    Fe = float(np.real(out[idx[:, None], idx[None, :], idx[:, None], idx[None, :]].sum()) / K**2)
    Fe_nr = float(np.real(out_nr[idx[:, None], idx[None, :], idx[:, None], idx[None, :]].sum()) / K**2)
    success = float(np.mean([np.real(out[j, j, j, j]) for j in range(K)]))
    leak = float(np.mean([diag_rho[j, j][~code.valid].sum() for j in range(K)]))
    res = {
        "code": code.name, "channel": channel, "p": p, "physical_qubits": code.n_qubits, "K": K,
        "logical_error_rate": 1 - Fe, "entanglement_fidelity": Fe,
        "average_fidelity": (K * Fe + 1) / (K + 1), "recovery_success_rate": success,
        "leakage": leak, "no_recovery_logical_error_rate": 1 - Fe_nr,
        "trace_preserved_valid_part": float(np.real(np.trace(out[0, 0]))),
        "seconds": time.perf_counter() - t0, "device": str(device),
    }
    if device != "cpu":
        res["gpu_peak_MB"] = torch.cuda.max_memory_allocated() / 2**20
    return res


def five_qubit_x3_metrics(block: EmbeddedCode, channel: str, p: float, K: int = 5) -> dict:
    """Three independent [[5,1,3]] blocks hold a 3-qubit logical register; the K = 5 levels are
    the basis states 0..4 of that register.  Exact: the logical channel is the tensor product of
    three identical exact single-block channels."""
    t0 = time.perf_counter()
    rho = torch.tensor(_inputs(block.V), dtype=torch.complex128)
    rho = apply_1q_channel(rho, block.n_qubits, kraus_1q(channel, p))
    B = torch.tensor(block.B, dtype=torch.complex128)
    out1 = torch.einsum("sdk,xde,sel->xkl", B.conj(), rho, B).numpy().reshape(2, 2, 2, 2)  # [i,j,k,l]
    # 3-block output for input |i><j| (3-bit labels) -> element <k| . |l>
    bits = lambda v: [(v >> 2) & 1, (v >> 1) & 1, v & 1]
    Fe = 0.0
    succ = 0.0
    for i in range(K):
        for j in range(K):
            bi, bj = bits(i), bits(j)
            val = np.prod([out1[bi[t], bj[t], bi[t], bj[t]] for t in range(3)])
            Fe += np.real(val)
        succ += np.real(np.prod([out1[bits(i)[t], bits(i)[t], bits(i)[t], bits(i)[t]] for t in range(3)]))
    Fe /= K**2
    return {"code": "[[5,1,3]] x 3 (15 qubits)", "channel": channel, "p": p, "physical_qubits": 15, "K": K,
            "logical_error_rate": 1 - Fe, "entanglement_fidelity": Fe, "average_fidelity": (K * Fe + 1) / (K + 1),
            "recovery_success_rate": succ / K, "leakage": 0.0, "seconds": time.perf_counter() - t0, "device": "cpu"}
