# ---------------------------------------------------------------------------------------
# VERBATIM TRANSCRIPTION of the listings printed in Appendix A of the paper
#   M. Guzeltepe, N. Aytac, FFA 117 (2027) 102881, pages 21-22.
# Transcribed by hand from the PDF for comparison only.  This is NOT one of the files the
# authors supplied; it depends on GaussianVector / GaussianCodeN from "epsilon codes.py".
# No line has been altered except that `import numpy as np` is added (used by A.2).
# ---------------------------------------------------------------------------------------
import numpy as np


# A.1. Coset-based decoder
def find_epsilon(C2, C1):
    zero = GaussianVector([(0,0)] * C2.n, C2.q)
    eps = [zero]
    for elem in C2.elements:
        if elem == zero: continue
        if not any((elem - rep) in C1.elements
                   for rep in eps):
            eps.append(elem)
        if len(eps) == C2.size() // C1.size():
            break
    return eps


def decode(y, eps, C1, C2):
    if y not in C2.elements:
        return None, None
    candidates = [e for e in eps
                  if (y - e) in C1.elements]
    if len(candidates) != 1:
        raise ValueError("Non-unique decoding.")
    return candidates[0], y - candidates[0]


# A.2. SER simulation
def gaussian_modulo(z, w):
    q = z * np.conj(w) / (np.abs(w)**2)
    q_r = np.round(q.real) + 1j*np.round(q.imag)
    return z - q_r * w
