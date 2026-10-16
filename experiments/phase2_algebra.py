"""Phase 2 - independent algebraic implementation, exhaustive checks and decoder cost.

Reproducible command:
    .venv/Scripts/python.exe experiments/phase2_algebra.py [--config phase2_algebra.toml] [--only a,b]
Sections: axioms, units, css, lemma1, transversals, decoding, scaling, multiqudit
"""
from __future__ import annotations

import argparse
import math
import time

import numpy as np

from epsqec.benchmarking import Experiment, load_config
from epsqec.css import PAPER_EXAMPLES, analyze_principal_pair, analyze_z9_table_row
from epsqec.css.examples import Z5_N4_CLAIMS, Z9_CLAIMS
from epsqec.decoder import EpsilonDecoder, check_transversal, greedy_transversal, multiples_transversal
from epsqec.decoder.direct import DirectCosetDecoder
from epsqec.ideals import (
    AdditiveCode, euclidean_dual, hermitian_dual, hermitian_dual_def6, orthogonal_exhaustive,
)
from epsqec.ring import GaussianRing, factorize, zi


# ----------------------------------------------------------------------------- axioms
def ring_axioms(q: int, triple_limit: int, random_triples: int, rng) -> dict:
    R = GaussianRing(q)
    E = R.elements()
    out = {"q": q, "|R|": R.size}
    keys = ["mul_commutative_all_pairs", "add_commutative_all_pairs", "conj_multiplicative_all_pairs",
            "conj_additive_all_pairs", "norm_multiplicative_all_pairs", "trace_pairing_nondegenerate_all"]
    acc = dict.fromkeys(keys, True)
    nz = ~R.is_zero(E)
    Y = E[None, :, :]
    for s in range(0, R.size, 256):  # all pairs, chunked over the first operand
        X = E[s:s + 256, None, :]
        xy, yx = R.mul(X, Y), R.mul(Y, X)
        acc["mul_commutative_all_pairs"] &= bool(np.array_equal(xy, yx))
        acc["add_commutative_all_pairs"] &= bool(np.array_equal(R.add(X, Y), R.add(Y, X)))
        acc["conj_multiplicative_all_pairs"] &= bool(np.array_equal(R.conj(xy), R.mul(R.conj(X), R.conj(Y))))
        acc["conj_additive_all_pairs"] &= bool(np.array_equal(R.conj(R.add(X, Y)), R.add(R.conj(X), R.conj(Y))))
        acc["norm_multiplicative_all_pairs"] &= bool(np.array_equal(R.norm(xy), np.mod(R.norm(X) * R.norm(Y), q)))
        # trace non-degeneracy: for every s != 0 there is t with Tr(s t) != 0
        tr = R.trace(xy)
        acc["trace_pairing_nondegenerate_all"] &= bool(np.all(np.any(tr[nz[s:s + 256]] != 0, axis=1)))
    out.update(acc)
    out["conj_involution_all"] = bool(np.array_equal(R.conj(R.conj(E)), E))
    out["norm_equals_x_conj_x_all"] = bool(np.array_equal(R.mul(E, R.conj(E)), np.stack([R.norm(E), 0 * R.norm(E)], -1)))
    out["i_squared_is_minus_one"] = bool(np.array_equal(R.mul(R.elem(0, 1), R.elem(0, 1)), R.elem(-1, 0)))
    if R.size ** 3 <= triple_limit:
        assoc = distr = True
        for x in E:
            xyz = R.mul(R.mul(x[None, None], E[:, None]), E[None, :])
            x_yz = R.mul(x[None, None], R.mul(E[:, None], E[None, :]))
            assoc &= bool(np.array_equal(xyz, x_yz))
            lhs = R.mul(x[None, None], R.add(E[:, None], E[None, :]))
            rhs = R.add(R.mul(x[None, None], E[:, None]), R.mul(x[None, None], E[None, :]))
            distr &= bool(np.array_equal(lhs, rhs))
        out["triples"] = "exhaustive"
    else:
        T = rng.integers(0, q, size=(random_triples, 3, 2))
        x, y, z = T[:, 0], T[:, 1], T[:, 2]
        assoc = bool(np.array_equal(R.mul(R.mul(x, y), z), R.mul(x, R.mul(y, z))))
        distr = bool(np.array_equal(R.mul(x, R.add(y, z)), R.add(R.mul(x, y), R.mul(x, z))))
        out["triples"] = f"random({random_triples})"
    out["mul_associative"] = assoc
    out["distributive"] = distr
    return out


def units_check(q: int, table_limit: int, rng) -> dict:
    R = GaussianRing(q)
    E = R.elements()
    crit = np.array([math.gcd(int(n), q) == 1 for n in R.norm(E)])
    out = {"q": q, "units_by_norm_criterion": int(crit.sum())}
    if R.size ** 2 <= table_limit:
        has_inv = np.zeros(R.size, dtype=bool)
        one = R.index(R.elem(1, 0))
        for s in range(0, R.size, 512):
            prod = R.index(R.mul(E[s:s + 512, None], E[None, :]))
            has_inv[s:s + 512] = (prod == one).any(axis=1)
        out["units_by_brute_force"] = int(has_inv.sum())
        out["criterion_matches_brute_force"] = bool(np.array_equal(has_inv, crit))
        out["mode"] = "exhaustive multiplication table"
    # Euler-type count:  |R^x| = prod over p^e || q of (p^e)^2 (1 - 1/p)^2 for split p
    phi = 1
    for p, e in factorize(q).items():
        phi *= (p ** (2 * e)) * (1 - 1 / p) ** 2
    out["units_formula_split_primes"] = round(phi)
    return out


# ------------------------------------------------------------------------------ lemma 1
def lemma1_check(q: int, alphas) -> dict:
    """Test the three statements of Lemma 1 under the two dual definitions in the paper."""
    R = GaussianRing(q)
    ideals = {}
    for a in alphas:
        C = AdditiveCode.principal(R, a)
        key = C.mask.tobytes()
        if key not in ideals:
            ideals[key] = (R.reduce(a), C)
    items = list(ideals.values())
    res = {"q": q, "n_alpha_tested": len(alphas), "n_distinct_ideals": len(items)}
    ex = {"p1_true": None, "p1_def6": None, "p2_true": None, "p2_def6": None, "p3_true": None, "p3_def6": None}
    cnt = {k: [0, 0] for k in ex}  # [violations, tested]
    duals_true, duals_def6 = [], []
    for a, C in items:
        Dt = hermitian_dual(C)
        D6 = hermitian_dual_def6(R, a)
        duals_true.append(Dt)
        duals_def6.append(D6)
        sig = lambda D: AdditiveCode.from_indices(R, 1, R.index(R.conj(D.vectors()[:, 0, :])))
        if math.gcd(int(R.norm(a)), q) == 1:  # hypothesis of property 1
            for tag, D in (("p1_true", Dt), ("p1_def6", D6)):
                cnt[tag][1] += 1
                if not (sig(D) == C):
                    cnt[tag][0] += 1
                    ex[tag] = ex[tag] or {"alpha": R.fmt(a), "|C|": C.size, "|sigma(dual)|": sig(D).size}
        for tag, D in (("p2_true", Dt), ("p2_def6", D6)):
            cnt[tag][1] += 1
            if C.size * D.size != R.size:
                cnt[tag][0] += 1
                ex[tag] = ex[tag] or {"alpha": R.fmt(a), "|C|": C.size, "|dual|": D.size, "q^2": R.size}
    for i, (a1, C1) in enumerate(items):
        for j, (a2, C2) in enumerate(items):
            if i == j or not C1.issubset(C2):
                continue
            for tag, Ds in (("p3_true", duals_true), ("p3_def6", duals_def6)):
                cnt[tag][1] += 1
                if not Ds[j].issubset(Ds[i]):
                    cnt[tag][0] += 1
                    ex[tag] = ex[tag] or {"C1": R.fmt(a1), "C2": R.fmt(a2),
                                          "|C1|": C1.size, "|C2|": C2.size,
                                          "|C2dual|": Ds[j].size, "|C1dual|": Ds[i].size}
    res["violations"] = {k: {"violations": v[0], "tested": v[1]} for k, v in cnt.items()}
    res["first_counterexample"] = ex
    return res


def divisor_generators(q: int) -> list[tuple[int, int]]:
    """All divisors of q in Z[i] up to units (generate every ideal of Z_q[i])."""
    primes = []
    for p, e in factorize(q).items():
        pi = zi.gaussian_prime_above(p)
        primes.append((pi, zi.conj(pi), e))
    divs = [(1, 0)]
    for pi, pib, e in primes:
        new = []
        for d in divs:
            for i in range(e + 1):
                for j in range(e + 1):
                    x = d
                    for _ in range(i):
                        x = zi.mul(x, pi)
                    for _ in range(j):
                        x = zi.mul(x, pib)
                    new.append(x)
        divs = new
    return divs


# ----------------------------------------------------------------------------- decoding
def exhaustive_decoding(key: str, pair, eps: np.ndarray, oracles, repeats: int, alpha1, alpha2) -> list[dict]:
    R, C1, C2 = pair.ring, pair.C1, pair.C2
    rows = []
    allY = R.all_vectors(1)
    # (1) vectorised: candidate count for every y in R
    dec = EpsilonDecoder(C2, C1, eps, oracle="bitmap", alpha1=alpha1, alpha2=alpha2)
    M = dec.candidate_matrix(allY)
    ncand = M.sum(axis=1)
    inC2 = C2.mask
    vec = {
        "y_total": len(allY), "y_in_C2": int(inC2.sum()),
        "in_C2_exactly_one_candidate": int((ncand[inC2] == 1).sum()),
        "in_C2_zero_candidates": int((ncand[inC2] == 0).sum()),
        "in_C2_multiple_candidates": int((ncand[inC2] > 1).sum()),
        "not_in_C2_with_candidate": int((ncand[~inC2] > 0).sum()),
    }
    # reconstruction y = c + e with c in C1 for every y in C2
    k = M[inC2].argmax(axis=1)
    c = R.sub(allY[inC2], dec.eps[k])
    vec["all_c_in_C1"] = bool(C1.contains(c).all())
    # every (c, e) in C1 x eps decodes back to (c, e)
    cs = C1.vectors()
    Ys = R.add(cs[:, None], dec.eps[None])  # (|C1|, k, 1, 2)
    kk = dec.candidate_matrix(Ys.reshape(-1, 1, 2)).argmax(axis=1).reshape(len(cs), -1)
    vec["all_codeword_error_pairs_recovered"] = bool(np.all(kk == np.arange(len(dec.eps))[None]))
    rows.append({"ring": key, "oracle": "bitmap-vectorised", **vec})

    # (2) per-word decoding loop with instrumentation (all y in R), each oracle
    for oname in oracles:
        d = EpsilonDecoder(C2, C1, eps, oracle=oname, alpha1=alpha1, alpha2=alpha2)
        best = math.inf
        for _ in range(repeats):
            stats = {"ok": 0, "not_in_C2": 0, "no_candidate": 0, "non_unique": 0, "wrong": 0}
            tests = 0
            t = time.perf_counter()
            for idx in range(R.size):
                y = allY[idx]
                r = d.decode(y)
                tests += r.n_membership_tests
                stats[r.status] += 1
                if r.status == "ok" and not (np.array_equal(R.add(r.c, r.e), R.reduce(y).reshape(1, 2))):
                    stats["wrong"] += 1
            best = min(best, time.perf_counter() - t)
        rows.append({
            "ring": key, "oracle": oname, **stats, "membership_tests_total": tests,
            "membership_tests_per_word": tests / R.size,
            "seconds_all_R_best_of": best, "us_per_word": 1e6 * best / R.size,
            "preprocess_s_C1": d.info["C1_oracle"]["preprocess_s"],
            "preprocess_s_C2": d.info["C2_oracle"]["preprocess_s"],
            "memory_bytes_C1_oracle_est": d.info["C1_oracle"]["memory_bytes_est"],
        })
    # (3) direct quotient-map labelling (comparison baseline)
    dd = DirectCosetDecoder(R.q, alpha1, alpha2, eps)
    t = time.perf_counter()
    agree = 0
    for idx in np.flatnonzero(inC2):
        y = allY[idx, 0]
        e, cc = dd.decode(y)
        r = dec.decode(y)
        agree += int(np.array_equal(np.asarray(e).reshape(1, 2), r.e))
    rows.append({"ring": key, "oracle": "direct-quotient-map(baseline)", "ok": agree,
                 "seconds_all_C2_incl_reference": time.perf_counter() - t,
                 "agrees_with_eps_decoder_on_all_C2": agree == int(inC2.sum())})
    return rows


def scaling(primes, family: str, oracles, n_dec: int, rng) -> list[dict]:
    rows = []
    g5 = (2, 1)
    for p in primes:
        q = 5 * p
        pi = zi.gaussian_prime_above(p)
        a1 = zi.mul(g5, pi)
        a2 = g5 if family == "A" else pi
        R = GaussianRing(q)
        t = time.perf_counter()
        C1 = AdditiveCode.principal(R, a1)
        C2 = AdditiveCode.principal(R, a2)
        t_enum = time.perf_counter() - t
        k = C2.size // C1.size
        eps = multiples_transversal(R, a2, k)
        sample = C2.vectors()[rng.integers(0, C2.size, n_dec)]
        for oname in oracles:
            d = EpsilonDecoder(C2, C1, eps, oracle=oname, alpha1=a1, alpha2=a2)
            t = time.perf_counter()
            tests = 0
            for y in sample:
                tests += d.decode(y).n_membership_tests
            dt = time.perf_counter() - t
            rows.append({"family": family, "p": p, "q": q, "|R|": R.size, "|C1|": C1.size, "|C2|": C2.size,
                         "|eps|": k, "oracle": oname, "us_per_decode": 1e6 * dt / n_dec,
                         "membership_tests_per_decode": tests / n_dec,
                         "us_per_membership_test": 1e6 * dt / tests,
                         "preprocess_s": d.info["C1_oracle"]["preprocess_s"] + d.info["C2_oracle"]["preprocess_s"],
                         "enumeration_s": t_enum,
                         "oracle_memory_bytes_est": d.info["C1_oracle"]["memory_bytes_est"]})
        dd = DirectCosetDecoder(q, a1, a2, eps)
        t = time.perf_counter()
        for y in sample:
            dd.decode(y[0])
        dt = time.perf_counter() - t
        rows.append({"family": family, "p": p, "q": q, "|R|": R.size, "|C1|": C1.size, "|C2|": C2.size,
                     "|eps|": k, "oracle": "direct-quotient-map(baseline)", "us_per_decode": 1e6 * dt / n_dec,
                     "membership_tests_per_decode": 0, "preprocess_s": 0.0, "enumeration_s": 0.0,
                     "oracle_memory_bytes_est": dd.table.nbytes})
    return rows


# --------------------------------------------------------------------------- multiqudit
def multiqudit_search(q: int, n: int, max_tries: int, rng) -> dict:
    """Search R-submodules C1 <= C2 <= Z_5[i]^4 matching Remark 8's sizes (independent
    reconstruction - the paper does not give generators)."""
    R = GaussianRing(q)
    target = Z5_N4_CLAIMS
    for t in range(max_tries):
        g2 = rng.integers(0, q, size=(3, n, 2))
        C2 = AdditiveCode.submodule(R, g2)
        if C2.size != target["size_C2"]:
            continue
        D2 = hermitian_dual(C2)
        if D2.size != target["size_dual"] or not D2.issubset(C2):
            continue
        # C1 = C2^perp + R w for a random w in C2
        for _ in range(50):
            w = C2.vectors()[rng.integers(0, C2.size)]
            gens = list(D2.vectors()[[i for i in range(1, D2.size)]][:4]) + [w]
            C1 = AdditiveCode.submodule(R, np.array(gens))
            if C1.size == target["size_C1"] and D2.issubset(C1) and C1.issubset(C2):
                return {
                    "found_after_tries": t + 1,
                    "C2_generators": g2.tolist(),
                    "C1_generators": np.array(gens).tolist(),
                    "size_C2": C2.size, "size_C1": C1.size, "size_C2_dual": D2.size,
                    "C1_subset_C2": True, "dual_subset_C1": True,
                    "orth_exhaustive_C2_vs_dual": orthogonal_exhaustive(C2, D2),
                    "K_theorem4_|C2|/|C1|": C2.size // C1.size,
                    "K_remark8_|C1|/|C2dual|": C1.size // D2.size,
                    "C1_dual_size": hermitian_dual(C1).size,
                    "status": "independent reconstruction (paper gives no generators)",
                }
    return {"found_after_tries": None, "status": f"not found in {max_tries} tries"}


# --------------------------------------------------------------------------------- main
def main(cfg_path: str, only: set[str] | None):
    cfg = load_config(cfg_path)
    rng = np.random.default_rng(cfg["seed"])
    want = lambda s: only is None or s in only
    with Experiment("algebra", "phase2_algebra", cfg, seed=cfg["seed"]) as ex:
        out: dict = {}
        if want("axioms"):
            out["axioms"] = [ring_axioms(q, cfg["axioms"]["triple_limit"], cfg["axioms"]["random_triples"], rng)
                             for q in cfg["axioms"]["q_values"]]
            for a in out["axioms"]:
                bad = [k for k, v in a.items() if v is False]
                if bad:
                    ex.fail(f"ring axioms failed for q={a['q']}: {bad}")
            print("axioms:", out["axioms"])
        if want("units"):
            out["units"] = [units_check(q, cfg["axioms"]["unit_table_limit"], rng) for q in cfg["axioms"]["q_values"] + [325]]
            print("units:", out["units"])

        pairs = {}
        if want("css") or want("transversals") or want("decoding"):
            out["css"] = {}
            for key in cfg["examples"]:
                pe = PAPER_EXAMPLES[key]
                pair, rep = analyze_principal_pair(pe.q, pe.alpha1, pe.alpha2)
                R = pair.ring
                # paper's claimed dual generator vs computed dual
                if "dual_generator" in pe.claimed:
                    Dg = AdditiveCode.principal(R, pe.claimed["dual_generator"])
                    rep["claimed_dual_generator"] = R.fmt(R.reduce(pe.claimed["dual_generator"]))
                    rep["claimed_dual_generator_ideal_equals_true_dual"] = Dg == pair.C2_dual
                E2 = euclidean_dual(pair.C2)
                rep["size_C2_euclidean_dual"] = E2.size
                rep["euclidean_dual_subset_C1"] = E2.issubset(pair.C1)
                rep["euclidean_dual_equals_hermitian_dual"] = E2 == pair.C2_dual
                # explicit counter-example to Definition 6: <alpha2, sigma(alpha2)>_H = alpha2^2
                a2 = R.reduce(pe.alpha2)
                v = R.conj(a2)
                rep["def6_counterexample"] = {
                    "c_in_C2": R.fmt(a2), "v_in_def6_dual": R.fmt(v),
                    "<c,v>_H": R.fmt(R.hermitian(a2[None], v[None])),
                    "nonzero": bool(not R.is_zero(R.hermitian(a2[None], v[None]))),
                }
                # Def-6 stabilisers do not commute: Tr <v, u>_H for v = sigma(alpha2), u = alpha1
                u = R.reduce(pe.alpha1)
                tr = int(R.trace(R.hermitian(v[None], u[None])))
                rep["def6_commutation_counterexample"] = {
                    "u_in_C1": R.fmt(u), "v_in_def6_dual": R.fmt(v), "Tr<v,u>_H mod q": tr,
                    "chi": complex(np.exp(2j * np.pi * tr / pe.q)), "commute": tr == 0,
                }
                checks = {}
                for ck in ("size_C1", "size_C2", "index", "K", "size_dual"):
                    if ck in pe.claimed:
                        got = {"size_C1": rep["size_C1_enumerated"], "size_C2": rep["size_C2_enumerated"],
                               "index": rep["index_C2_C1"], "K": rep["K"], "size_dual": rep["size_C2_dual_true"]}[ck]
                        checks[ck] = {"claimed": pe.claimed[ck], "computed": got, "match": got == pe.claimed[ck]}
                        if got != pe.claimed[ck]:
                            ex.fail(f"{key}: {ck} claimed {pe.claimed[ck]} computed {got}")
                rep["claims_vs_computed"] = checks
                out["css"][key] = rep
                pairs[key] = pair
                print(key, {k: rep[k] for k in ("size_C1_enumerated", "size_C2_enumerated", "K",
                                                 "size_C2_dual_true", "size_C2_dual_def6",
                                                 "size_C2_euclidean_dual", "dual_true_subset_C1")})
            z9 = analyze_z9_table_row()
            z9["table_claims"] = Z9_CLAIMS
            z9["table1_dual_size_matches_true_dual"] = z9["size_C2_dual_true"] == Z9_CLAIMS["size_dual"]
            z9["table2_K_matches_theorem4"] = z9["K_theorem4_formula"] == Z9_CLAIMS["K_table2"]
            out["z9_table_row"] = z9

        if want("lemma1"):
            out["lemma1"] = []
            for q in cfg["lemma1"]["exhaustive_alpha_q"]:
                R = GaussianRing(q)
                res = lemma1_check(q, list(R.elements()))
                res["mode"] = "all alpha in R"
                out["lemma1"].append(res)
                print("lemma1", q, res["violations"])
            for q in cfg["lemma1"]["divisor_ideal_q"]:
                res = lemma1_check(q, divisor_generators(q))
                res["mode"] = "all divisor ideals (= all ideals, Z_q[i] is a PIR)"
                out["lemma1"].append(res)
                print("lemma1", q, res["violations"])

        dec_rows = []
        if want("transversals") or want("decoding"):
            out["transversals"] = {}
            for key, pair in pairs.items():
                pe = PAPER_EXAMPLES[key]
                R = pair.ring
                sets = {
                    "greedy_theorem2": greedy_transversal(pair.C2, pair.C1),
                    "multiples_k_alpha2": multiples_transversal(R, pe.alpha2, pair.K),
                    "orig_canonical_i_multiples": multiples_transversal(R, R.mul(R.elem(0, 1), R.reduce(pe.alpha2)), pair.K),
                }
                for nm, prs in pe.eps_sets.items():
                    sets[nm] = R.reduce(np.array(prs))[:, None, :]
                out["transversals"][key] = {}
                for nm, eps in sets.items():
                    rep = check_transversal(eps, pair.C2, pair.C1)
                    out["transversals"][key][nm] = {"eps": [R.fmt(e[0]) for e in eps], **rep.as_dict()}
                    if not rep.valid:
                        ex.fail(f"{key}: transversal {nm} invalid")
                if want("decoding"):
                    eps = sets.get("paper_example7", sets.get("paper_example6", sets["multiples_k_alpha2"]))
                    dec_rows += exhaustive_decoding(key, pair, eps, cfg["decoder"]["oracles"],
                                                    cfg["decoder"]["timing_repeats"], pe.alpha1, pe.alpha2)
            for r in dec_rows:
                if r.get("wrong") or r.get("non_unique") or r.get("in_C2_multiple_candidates") or r.get("not_in_C2_with_candidate"):
                    ex.fail(f"decoding error row {r}")
            out["decoding"] = dec_rows
            ex.save_csv("decoder_exhaustive.csv", dec_rows)
            for r in dec_rows:
                print("decode", r)

        if want("scaling"):
            sc = scaling(cfg["decoder"]["family_A_primes"], "A", cfg["decoder"]["oracles"], cfg["decoder"]["decodes_per_point"], rng)
            sc += scaling(cfg["decoder"]["family_B_primes"], "B", cfg["decoder"]["oracles"], cfg["decoder"]["decodes_per_point"], rng)
            ex.save_csv("decoder_scaling.csv", sc)
            out["scaling_rows"] = len(sc)
            # linear fit of time vs |eps| for family A
            for o in cfg["decoder"]["oracles"] + ["direct-quotient-map(baseline)"]:
                pts = [(r["|eps|"], r["us_per_decode"]) for r in sc if r["family"] == "A" and r["oracle"] == o]
                x, y = np.array(pts).T
                slope, icpt = np.polyfit(x, y, 1)
                out.setdefault("scaling_fit_family_A", {})[o] = {"us_per_eps_element": slope, "intercept_us": icpt,
                                                                 "r2": float(np.corrcoef(x, y)[0, 1] ** 2)}
            print("scaling fit:", out["scaling_fit_family_A"])

        if want("multiqudit"):
            mq = cfg["multiqudit"]
            out["multiqudit"] = multiqudit_search(mq["q"], mq["n"], mq["max_tries"], rng)
            print("multiqudit:", out["multiqudit"])
        ex.save_json("results.json", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="phase2_algebra.toml")
    ap.add_argument("--only", default=None, help="comma separated sections")
    a = ap.parse_args()
    main(a.config, set(a.only.split(",")) if a.only else None)
