"""PennyLane circuits for the R_Q = Z_q[i] codes (qubit embedding of one ring qudit).

The sub-package is deliberately NOT called ``pennylane`` so that it can never shadow the real
PennyLane package on sys.path.
"""
from .ring_circuits import RingRegisterLayout, RingCircuits

__all__ = ["RingRegisterLayout", "RingCircuits"]
