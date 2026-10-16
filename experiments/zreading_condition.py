"""Review item C1 - Proposition 5 under the Z-type reading, over ALL valid ideal pairs.

    .venv/Scripts/python.exe experiments/zreading_condition.py [--config zreading_condition.toml]

For each q, every pair of ideals C1 < C2 with C2^perpH <= C1 (Theorem 4 hypotheses), and every
eps choice (C2/C1 transversal):
  condition  : (eps - eps) /\\ C1^perpH = {0}      [coset labels mod C1^perpH; also pairwise when small]
  syndromes  : number of distinct X-stabilizer syndromes of Z(e), e in eps  (RingCSSCode.xsyn: the
               trace values Tr<e, u_k>_H against the additive generators u_k of C1)
  claim      : condition  <=>  |distinct| = |eps|
eps choices: greedy (Theorem 2, index order), canonical (the authors' find_epsilon_canonical rule:
first r*alpha2 in (a,b) order that opens a new coset), paper_multiples ({0, alpha2, ..., (K-1) alpha2},
only when it is a transversal), random (seeded random transversal).
"""
from __future__ import annotations

import argparse
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.decoder import check_transversal, greedy_transversal
from epsqec.ideals import AdditiveCode, hermitian_dual
from epsqec.ring import GaussianRing
from epsqec.stabilizer import QuditSpace, RingCSSCode

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_checks import divisor_generators  # noqa: E402


def coset_labels(code: AdditiveCode) -> np.ndarray:
    """label[idx(x)] = id of the coset x + code, for every x in R^n (O(|R^n|) work)."""
    R, n = code.ring, code.n
    lab = np.full(R.size ** n, -1, dtype=np.int64)
    V = code.vectors()
    nxt = 0
    for idx in range(R.size ** n):
        if lab[idx] >= 0:
            continue
        x = R.vec_from_index(idx, n)
        lab[R.vec_index(R.add(V, x[None]))] = nxt
        nxt += 1
    return lab


_LABEL_CACHE: dict = {}


def coset_labels_fast(code: AdditiveCode) -> np.ndarray:
    """n = 1 ideals: vectorised.  In split coordinates every ideal is a product of p-power ideals
    p^v Z_{p^e} per component, so  x = y (mod code)  <=>  each component agrees mod p^v.
    (Cross-checked against the generic loop in tests/test_review.py and below for small q.)
    n > 1: generic O(|R^n|) loop."""
    key = (code.ring.q, code.n, code.mask.tobytes())
    if key in _LABEL_CACHE:
        return _LABEL_CACHE[key]
    if code.n == 1:
        from epsqec.pl_circuits.split_layout import SplitLayout

        R = code.ring
        lay = SplitLayout(R)
        val = lay.valuations(code)
        sp = lay.split(R.elements())
        lab = np.zeros(R.size, dtype=np.int64)
        for bi, B in enumerate(lay.blocks):
            for ci, comp in enumerate(("U", "V")):
                m = B["p"] ** val[(bi, comp)]
                lab = lab * m + np.mod(sp[bi][ci], m)
        out = lab
    else:
        out = coset_labels(code)
    _LABEL_CACHE[key] = out
    return out


def canonical_eps(R, alpha2, C1, K):
    """Authors' find_epsilon_canonical rule, vectorised: scan r = a + bi in (a, b) order."""
    E = R.elements()
    reps = R.mul(E, R.reduce(alpha2)[None])
    lab = coset_labels_fast(C1)[R.index(reps)]
    _, first = np.unique(lab, return_index=True)
    first = np.sort(first)[:K]
    return reps[first][:, None, :]


def random_eps(R, C2, C1, rng, lab1=None):
    lab1 = coset_labels_fast(C1) if lab1 is None else lab1
    V = C2.vectors()
    perm = rng.permutation(len(V))
    _, first = np.unique(lab1[R.vec_index(V[perm])], return_index=True)
    return V[perm][np.sort(first)]


def transversal_ok(eps, C2, C1, small=2000) -> bool:
    """eps is a C2/C1 transversal  <=>  eps subset C2, |eps| = [C2:C1], coset labels mod C1 distinct.
    Vectorised (n = 1 via split labels); for |eps| <= small also the pairwise check_transversal."""
    R = C2.ring
    eps = np.asarray(eps)
    if eps.ndim == 2:
        eps = eps[:, None, :]
    lab = coset_labels_fast(C1)[R.vec_index(eps)]
    ok = bool(C2.contains(eps).all()) and len(eps) == C2.size // C1.size and len(np.unique(lab)) == len(eps)
    if len(eps) <= small:
        assert ok == check_transversal(eps, C2, C1).valid, "vectorised and pairwise transversal checks disagree"
    return ok


def evaluate(R, code, eps, D1, labD, pairwise_limit) -> dict:
    eps = np.asarray(eps)
    if eps.ndim == 2:
        eps = eps[:, None, :]
    labs = labD[R.vec_index(eps)]
    cond = len(np.unique(labs)) == len(eps)
    direct = None
    if len(eps) ** 2 <= pairwise_limit:
        diffs = R.sub(eps[:, None], eps[None, :]).reshape(-1, eps.shape[1], 2)
        nz = ~np.all(diffs.reshape(len(diffs), -1) == 0, axis=1)
        direct = not bool(D1.contains(diffs[nz]).any())
    syn = code.xsyn(eps)
    distinct = len({tuple(r) for r in syn.tolist()})
    return {"|eps|": len(eps), "condition": cond, "condition_pairwise": direct,
            "distinct_syndromes": distinct, "prop5_Z_reading_holds": distinct == len(eps),
            "equivalence_holds": cond == (distinct == len(eps)) and (direct is None or direct == cond)}


def run_q(q, cfg, rng, ex) -> list[dict]:
    R = GaussianRing(q)
    sp = QuditSpace(R, 1)
    ideals = {}
    for d in divisor_generators(q):
        C = AdditiveCode.principal(R, d)
        ideals.setdefault(C.mask.tobytes(), (d, C))
    ideals = list(ideals.values())
    duals = [hermitian_dual(C) for _, C in ideals]
    labs = {}
    rows = []
    for i1, (d1, C1) in enumerate(ideals):
        for i2, (d2, C2) in enumerate(ideals):
            if i1 == i2 or not C1.issubset(C2) or C1.size == C2.size or not duals[i2].issubset(C1):
                continue
            K = C2.size // C1.size
            D1 = duals[i1]
            if i1 not in labs:
                labs[i1] = coset_labels_fast(D1)
            code = RingCSSCode(sp, C1, C2, duals[i2], f"{q}")
            choices = {}
            for m in cfg["eps_methods"]:
                if m == "greedy":
                    choices[m] = greedy_transversal(C2, C1)
                elif m == "canonical":
                    choices[m] = canonical_eps(R, d2, C1, K)
                elif m == "paper_multiples":
                    e = R.scal(np.arange(K), R.reduce(d2)[None])[:, None, :]
                    choices[m] = e if transversal_ok(e, C2, C1) else None
                elif m == "random":
                    choices[m] = random_eps(R, C2, C1, rng)
            for m, eps in choices.items():
                base = {"q": q, "alpha1": f"{d1[0]}+{d1[1]}i", "alpha2": f"{d2[0]}+{d2[1]}i", "|C1|": C1.size,
                        "|C2|": C2.size, "K": K, "|C1^perpH|": D1.size, "C1^perpH_subset_C1": D1.issubset(C1),
                        "eps_method": m}
                if eps is None:
                    rows.append({**base, "status": "not a transversal (multiples of alpha2)"})
                    continue
                if not transversal_ok(eps, C2, C1):
                    ex.fail(f"q={q} {m}: invalid transversal")
                r = evaluate(R, code, eps, D1, labs[i1], cfg["pairwise_limit"])
                rows.append({**base, "status": "ok", **r})
                if not r["equivalence_holds"]:
                    ex.fail(f"q={q} alpha1={d1} alpha2={d2} {m}: equivalence violated")
    return rows


def run_multiqudit(mq, rng, ex) -> list[dict]:
    from epsqec.css.build import build

    b = build({"key": mq["key"], "q": mq["q"], "C1_generators": mq["C1_generators"],
               "C2_generators": mq["C2_generators"], "eps": "greedy"})
    R = b.ring
    D1 = b.C1_dual
    lab = coset_labels_fast(D1)
    lab1 = coset_labels_fast(b.C1)
    rows = []
    sets = {"greedy": greedy_transversal(b.C2, b.C1)}
    for k in range(mq["random_transversals"]):
        sets[f"random{k}"] = random_eps(R, b.C2, b.C1, rng, lab1)
    for m, eps in sets.items():
        r = evaluate(R, b.code, eps, D1, lab, 4_000_000)
        rows.append({"q": "5 (n=4)", "eps_method": m, "K": b.C2.size // b.C1.size, "|C1^perpH|": D1.size,
                     "C1^perpH_subset_C1": D1.issubset(b.C1), "status": "ok", **r})
        if not r["equivalence_holds"]:
            ex.fail(f"Z5n4 {m}: equivalence violated")
    return rows


def main(cfg_path):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    with Experiment("algebra", "zreading_condition", cfg, seed=cfg["seed"]) as ex:
        rows = []
        for q in cfg["q_values"]:
            t = time.perf_counter()
            r = run_q(q, cfg, rng, ex)
            rows += r
            ok = [x for x in r if x["status"] == "ok"]
            print(f"q={q}: pairs={len({(x['alpha1'], x['alpha2']) for x in r})} evaluated={len(ok)} "
                  f"cond_true={sum(x['condition'] for x in ok)} prop5Z_true={sum(x['prop5_Z_reading_holds'] for x in ok)} "
                  f"equiv_violations={sum(not x['equivalence_holds'] for x in ok)} ({time.perf_counter() - t:.1f}s)", flush=True)
        mq = run_multiqudit(cfg["multiqudit"], rng, ex)
        rows += mq
        print("Z5n4:", [(x["eps_method"], x["condition"], x["distinct_syndromes"], x["|eps|"]) for x in mq[:5]],
              "cond_true", sum(x["condition"] for x in mq), "of", len(mq))
        ex.save_csv("pairs.csv", rows)
        summary = {}
        for x in rows:
            if x.get("status") != "ok":
                continue
            key = (str(x["q"]), x["eps_method"])
            s = summary.setdefault(key, {"evaluated": 0, "condition_true": 0, "prop5_Z_holds": 0, "equivalence_violations": 0})
            s["evaluated"] += 1
            s["condition_true"] += int(x["condition"])
            s["prop5_Z_holds"] += int(x["prop5_Z_reading_holds"])
            s["equivalence_violations"] += int(not x["equivalence_holds"])
        ex.save_json("results.json", {"summary": {f"{k[0]}|{k[1]}": v for k, v in summary.items()},
                                      "invalid_multiples": [x for x in rows if x.get("status", "ok") != "ok"]})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="zreading_condition.toml")
    main(ap.parse_args().config)
