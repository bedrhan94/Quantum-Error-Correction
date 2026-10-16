"""Check the WSL GPU stack: torch CUDA (Blackwell sm_120), lightning.gpu, and agreement of
lightning.gpu with lightning.qubit on a small random circuit."""
import sys

import numpy as np
import pennylane as qml
import torch

print("python", sys.version.split()[0])
print("torch", torch.__version__, "cuda build", torch.version.cuda, "available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device", torch.cuda.get_device_name(0), "capability", torch.cuda.get_device_capability(0))
    print("arch list", torch.cuda.get_arch_list())
print("pennylane", qml.__version__)

n = 12
rng = np.random.default_rng(0)
params = rng.normal(size=(3, n, 3))


def circuit():
    for layer in params:
        for w in range(n):
            qml.Rot(*layer[w], wires=w)
        for w in range(n - 1):
            qml.CNOT([w, w + 1])
    qml.Adder(7, x_wires=list(range(5)), mod=25, work_wires=[10, 11])
    return qml.state()


states = {}
for name, kw in (("lightning.qubit", {}), ("lightning.gpu", {}), ("lightning.gpu", {"c_dtype": np.complex64})):
    dev = qml.device(name, wires=n, **kw)
    states[(name, str(kw))] = np.asarray(qml.QNode(circuit, dev)())
ref = states[("lightning.qubit", "{}")]
for k, s in states.items():
    print(k, "fidelity vs lightning.qubit:", float(abs(np.vdot(ref, s)) ** 2))
