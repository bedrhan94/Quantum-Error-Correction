"""QEC-cycle programs for layouts A and B, run either with PennyLane-native mid-circuit
measurements or with an exact segmented simulator.

Program items (shared by both engines):
  ("ops", fn)                      quantum function, applied as is
  ("measure", name, wires, reset)  computational-basis measurement of `wires` (record = integer,
                                   big-endian over `wires`); with reset=True the wires are set to |0>
                                   AFTER the measurement, otherwise they keep the measured value
  ("cond", choose, names)          choose(record) -> quantum function or None (classical feed-forward);
                                   `names` = the measurement records it depends on

Engines
  native     : one QNode; "measure" -> qml.measure(w, reset), "cond" -> qml.cond over every possible
               record value (PennyLane mcm_method, e.g. tree-traversal on default.qubit)
  segmented  : the circuit is simulated segment by segment (lightning); at each "measure" the exact
               outcome distribution of `wires` is computed from the state vector, every outcome with
               probability > branch_tol is followed (collapse + optional reset), and the weighted final
               distribution is returned.  The discarded probability mass is reported.
"""
from __future__ import annotations

import itertools

import numpy as np
import pennylane as qml

from ..stabilizer import min_weight_transversal
from .ring_circuits import RingCircuits
from .split_layout import SplitCircuits


def transversals(b):
    sp, code = b.space, b.code
    TX = min_weight_transversal(sp, code.zsyn_key, sp.dim // b.C2.size)
    TZ = min_weight_transversal(sp, code.xsyn_key, sp.dim // b.C1_dual.size)
    return TX.reshape(-1, 2), TZ.reshape(-1, 2)


# ============================================================================ layouts
class LayoutB:
    """Split-coordinate digits (SplitCircuits) with the gate-level encoder."""
    name = "B"

    def __init__(self, b, reuse=True):
        self.b = b
        self.sc = SplitCircuits(b, reuse_ancilla=reuse)
        self.TX, self.TZ = transversals(b)
        self.K = self.sc.K
        sc = self.sc
        self.lut = {"Z": {}, "X": {}}
        for kind, T in (("Z", self.TX), ("X", self.TZ)):
            parts = [P for P in sc.parts if P.kind == kind]
            for e in T:
                key = tuple(sc.expected_part(P, e) for P in parts)
                if key in self.lut[kind]:
                    raise AssertionError("syndrome LUT collision")
                self.lut[kind][key] = e

    n_wires = property(lambda self: self.sc.n_wires)

    def prep(self, inp):
        if isinstance(inp, (int, np.integer)):
            self.sc.prepare_basis(int(inp))
        else:
            self.sc.prepare_logical(inp)
        self.sc.encode()

    def unprep(self, inp):
        self.sc.decode()
        if isinstance(inp, (int, np.integer)):
            self.sc.prepare_basis(int(inp))
        else:
            self.sc.unprepare_logical(inp)

    def out_wires(self):
        return self.sc.logical_wires + self.sc.data_wires

    def X(self, u):
        self.sc.X(u)

    def Z(self, v):
        self.sc.Z(v)

    def _part_wires(self, P):
        return [w for d in self.sc.measured_value_order(P) for w in d.wires]

    def _part_value(self, P, bits: int) -> int:
        n = sum(d.m for d in P.digits)
        val, pos = 0, 0
        s = format(bits, f"0{n}b")
        for d in self.sc.measured_value_order(P):
            val = val * d.p + int(s[pos:pos + d.m], 2)
            pos += d.m
        return val

    def round_program(self, kind: str) -> list:
        sc, R = self.sc, self.b.ring
        parts = [P for P in sc.parts if P.kind == kind]
        items = []
        for k, P in enumerate(parts):
            ext = sc.z_syndrome if kind == "Z" else sc.x_syndrome
            items.append(("ops", lambda P=P, ext=ext: ext(P)))
            items.append(("measure", f"{kind}{k}", self._part_wires(P), sc.reuse))

        def choose(rec, parts=parts, kind=kind):
            key = tuple(self._part_value(P, rec[f"{kind}{k}"]) for k, P in enumerate(parts))
            corr = self.lut[kind].get(key)
            if corr is None or not np.any(corr):
                return None
            fn = sc.X if kind == "Z" else sc.Z
            return lambda: fn(R.neg(corr))

        items.append(("cond", choose, [f"{kind}{k}" for k in range(len(parts))]))
        return items


class LayoutA:
    """Binary |a>|b> registers (RingCircuits, qml.Adder).  No gate-level encoder: input/output are
    loaded with a gate-level Mottonen preparation of the reference code state."""
    name = "A"

    def __init__(self, b, reuse=False):
        if reuse:
            raise NotImplementedError("layout A keeps separate syndrome registers")
        self.b = b
        code = b.code
        self.rc = RingCircuits(b.ring.q, zgens=code.zgens, xgens=code.xgens)
        self.TX, self.TZ = transversals(b)
        self.V = code.logical_states(b.eps)
        self.K = len(self.V)
        q, rc = b.ring.q, self.rc
        self.lut = {"Z": {}, "X": {}}
        for e in self.TX:
            z = code.zsyn(e.reshape(1, 1, 2))[0]
            key = tuple(int((int(z[k]) // (q // rc.z_orders[k])) % rc.z_orders[k]) for k in range(len(rc.zgens)))
            self.lut["Z"][key] = e
        for f in self.TZ:
            t = code.xsyn(f.reshape(1, 1, 2))[0]
            key = tuple(int((-(int(t[k]) // (q // rc.x_orders[k]))) % rc.x_orders[k]) for k in range(len(rc.xgens)))
            self.lut["X"][key] = f

    n_wires = property(lambda self: self.rc.L.n_wires)

    def _vec(self, inp):
        amps = np.eye(self.K)[int(inp)] if isinstance(inp, (int, np.integer)) else inp
        return self.rc.embed_ring_state(amps @ self.V)

    def prep(self, inp):
        qml.MottonenStatePreparation(self._vec(inp), wires=self.rc.L.data)

    def unprep(self, inp):
        qml.adjoint(qml.MottonenStatePreparation)(self._vec(inp), wires=self.rc.L.data)

    def out_wires(self):
        return list(self.rc.L.data)

    def X(self, u):
        self.rc.X(np.asarray(u).reshape(2))

    def Z(self, v):
        self.rc.Z(np.asarray(v).reshape(2))

    def round_program(self, kind: str) -> list:
        rc, R = self.rc, self.b.ring
        n = len(rc.zgens) if kind == "Z" else len(rc.xgens)
        items = []
        for k in range(n):
            if kind == "Z":
                items.append(("ops", lambda k=k: rc.z_syndrome(k)))
                items.append(("measure", f"Z{k}", list(rc.L.z_anc[k]), False))
            else:
                items.append(("ops", lambda k=k: rc.x_syndrome(k)))
                items.append(("measure", f"X{k}", list(rc.L.x_anc[k]), False))

        def choose(rec, kind=kind, n=n):
            key = tuple(int(rec[f"{kind}{k}"]) for k in range(n))
            corr = self.lut[kind].get(key)
            if corr is None or not np.any(corr):
                return None
            fn = rc.X if kind == "Z" else rc.Z
            return lambda: fn(R.neg(corr).reshape(2))

        items.append(("cond", choose, [f"{kind}{k}" for k in range(n)]))
        return items


def cycle_program(layout, a, f, inp, order) -> list:
    prog = [("ops", lambda: (layout.prep(inp), layout.X(a), layout.Z(f)))]
    for kind in order:
        prog += layout.round_program(kind)
    prog.append(("ops", lambda: layout.unprep(inp)))
    return prog


# ============================================================================ engines
def run_native(program, n_wires, out_wires, device="default.qubit", mcm_method="tree-traversal"):
    """PennyLane-native mid-circuit measurements; every cond is expanded over all record values."""
    dev = qml.device(device, wires=n_wires)
    names_wires = {it[1]: it[2] for it in program if it[0] == "measure"}

    @qml.qnode(dev, mcm_method=mcm_method)
    def circ():
        rec = {}
        for it in program:
            if it[0] == "ops":
                it[1]()
            elif it[0] == "measure":
                v = 0
                for w in it[2]:
                    v = v * 2 + qml.measure(w, reset=it[3])
                rec[it[1]] = v
            else:  # cond: enumerate every possible value of the records it depends on
                names = list(it[2])
                sizes = [len(names_wires[nm]) for nm in names]
                for vals in itertools.product(*[range(2 ** s) for s in sizes]):
                    fn = it[1](dict(zip(names, vals)))
                    if fn is None:
                        continue
                    c = None
                    for nm, vv in zip(names, vals):
                        t = rec[nm] == vv
                        c = t if c is None else (c & t)
                    qml.cond(c, fn)()
        return qml.probs(wires=out_wires)

    return np.asarray(circ())


def run_segmented(program, n_wires, out_wires, device="lightning.qubit", branch_tol=1e-14, c_dtype=None):
    """Exact segment-by-segment simulation; returns (final probs over out_wires, info)."""
    kw = {"c_dtype": c_dtype} if c_dtype is not None else {}
    dev = qml.device(device, wires=n_wires, **kw)
    info = {"segments": 0, "branches": 0, "discarded_probability": 0.0, "records": []}

    def segment(state, fns):
        @qml.qnode(dev)
        def seg():
            if state is not None:
                qml.StatePrep(state, wires=range(n_wires))
            for fn in fns:
                fn()
            return qml.state()

        info["segments"] += 1
        return np.asarray(seg())

    def explore(state, idx, rec, weight):
        fns = []
        while idx < len(program):
            it = program[idx]
            if it[0] == "ops":
                fns.append(it[1])
                idx += 1
            elif it[0] == "cond":
                fn = it[1](rec)
                if fn is not None:
                    fns.append(fn)
                idx += 1
            else:
                state = segment(state, fns)
                fns = []
                wires, reset = list(it[2]), it[3]
                psi = state.reshape([2] * n_wires)
                psi = np.moveaxis(psi, wires, list(range(len(wires))))
                shp = psi.shape
                M = psi.reshape(2 ** len(wires), -1)
                p = np.sum(np.abs(M) ** 2, axis=1)
                total = None
                for o in range(len(p)):
                    if p[o] <= branch_tol:
                        info["discarded_probability"] += float(weight * p[o])
                        continue
                    info["branches"] += 1
                    new = np.zeros_like(M)
                    new[0 if reset else o] = M[o] / np.sqrt(p[o])
                    new = np.moveaxis(new.reshape(shp), list(range(len(wires))), wires).reshape(-1)
                    r = explore(new, idx + 1, {**rec, it[1]: o}, weight * p[o])
                    total = p[o] * r if total is None else total + p[o] * r
                return total
        state = segment(state, fns)
        info["records"].append({k: int(v) for k, v in rec.items()})
        psi = np.moveaxis(state.reshape([2] * n_wires), out_wires, list(range(len(out_wires))))
        return np.sum(np.abs(psi.reshape(2 ** len(out_wires), -1)) ** 2, axis=1)

    probs = explore(None, 0, {}, 1.0)
    return probs, info
