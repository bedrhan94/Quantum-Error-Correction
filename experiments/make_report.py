"""Fill reports/teknik_rapor.template.md with tables built from the latest result directories.

    .venv/Scripts/python.exe experiments/make_report.py
Writes reports/teknik_rapor.md.  No number in the generated tables is typed by hand: each table
names the experiment directory it was read from.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def latest(category: str, prefix: str, need: str | None = None, status: str | None = "PASS") -> Path:
    cands = []
    for d in sorted((RES / category).glob(prefix + "-*")):
        st = d / "status.json"
        if not st.exists():
            continue
        s = json.loads(st.read_text(encoding="utf-8"))
        if status and s["status"] != status:
            continue
        if need and not (d / need).exists():
            continue
        cands.append(d)
    if not cands:
        raise FileNotFoundError(f"no {category}/{prefix} run with {need}")
    return cands[-1]


def rel(d: Path) -> str:
    return d.name


def f(x, nd=3):
    if x is None or x == "":
        return "—"
    x = float(x)
    if x == 0:
        return "0"
    if abs(x) < 1e-3 or abs(x) >= 1e4:
        return f"{x:.{nd - 1}e}"
    return f"{x:.{nd}g}"


def fid(x):
    """Fidelity close to 1 written as 1 - delta (plain rounding would print '1' or a row of 9s)."""
    if x is None or x == "":
        return "—"
    dev = 1 - float(x)
    return "1 (sapma < 10⁻¹⁵)" if abs(dev) < 1e-15 else (f"1 − {dev:.1e}" if dev > 0 else f"1 + {-dev:.1e}")


def tr_bool(v):
    return {True: "evet", False: "hayır", "True": "evet", "False": "hayır"}.get(v, str(v))


def md(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def phase5(rep: dict):
    d = latest("quantum", "phase5_prop5", "results.json", status=None)
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    rep["PHASE5_PROP5_ID"] = f"{rel(d)} (status {st['status']}, {st['wall_time_s']:.0f} s)"
    rows, alt = [], []
    for k, v in r.items():
        A = v["A_paper_reading_X_errors"]
        C = v["C_alternative_design_recovery"]
        B = v["B_supplementary_Z_errors"]
        fid = max(x["fidelity_random_logical_state"] for x in A["eps_rows"][1:]) if len(A["eps_rows"]) > 1 else None
        ov = max(x["|<psi_0|X(e)|psi_0>|^2"] for x in A["eps_rows"][1:]) if len(A["eps_rows"]) > 1 else None
        rows.append([k, v["dim_H"], int(v["K"]), A["C2_elements_tested"], A["C2_elements_with_nonzero_syndrome"],
                     "✓" if A["kernel_of_X_syndrome_equals_C2"] else "✗",
                     f"{A['distinct_syndrome_patterns_over_eps']} / {A['|eps|']}", f(ov), f(fid),
                     f(A["knill_laflamme_eps_X_errors"]["max_deviation"], 4),
                     f"{B['distinct_Z_syndromes_over_eps']} / {B['|eps|']}"])
        kl = C["knill_laflamme_alt_set"]
        alt.append([k, C["|T_X|"], C["|T_Z|"], f"{C['pairs_tested']} ({C['mode']})", C["recovered_exactly"],
                    f(C["min_fidelity"], 12), f(kl["max_deviation"]) + (f" ({kl['mode']})" if "mode" in kl else " (exhaustive)"),
                    f"{C['weight2_X_errors_recovered']} / {C['weight2_X_errors_tested']}"])
    rep["PHASE5_TABLE"] = md(rows, ["Kod", "dim H", "K", "C2 elemanı (exhaustive)", "sıfırdan farklı sendrom",
                                   "sendrom çekirdeği = C2", "farklı sendrom / \\|ε\\|", "max \\|⟨ψ₀\\|X(e)\\|ψ₀⟩\\|² (e≠0)",
                                   "max sadakat X(e)ψ vs ψ (e≠0)", "KL sapması {X(e)}", "Z(e) okuması: farklı sendrom"])
    rep["PHASE5_ALT_TABLE"] = (f"Deney: `{rel(d)}`\n\n" + md(alt, ["Kod", "\\|T_X\\|", "\\|T_Z\\|", "test edilen (a,b)",
                                                               "tam düzeltilen", "min sadakat", "KL sapması",
                                                               "ağırlık-2 X hatası düzeltilen"]) +
                               "\n\nSon sütun karşılaştırma içindir: ağırlık-2 X-hataları, T_X onları içermiyorsa düzeltilemez "
                               "(beklenen; Z25 ve Z85'te T_X yalnızca {0, ±1, ±i}); Z325'te T_X 13 elemanlıdır ve tüm "
                               "ağırlık-≤2 kaymaları içerdiği için hepsi düzeltildi; Z5n4'te kısmen.")


def phase5_pl(rep: dict):
    d = latest("quantum", "phase5_pennylane", "results.json")
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    rep["PHASE5_PL_ID"] = f"{rel(d)} ({st['wall_time_s']:.0f} s, süreç tepe çalışma kümesi {st.get('peak_wset_MB')} MB)"
    t1 = []
    for k, v in r["adder_leakage"].items():
        t1.append([k, v["m"], v["k_tested"], "✓" if v["valid_inputs_correct"] else "✗",
                   "✓" if v["work_wires_clean_valid"] else "✗", v["invalid_inputs"],
                   "evet" if v["invalid_stay_invalid"] else "hayır", v["method"]])
    s = "**(a) `qml.Adder` sızıntı testi** (her taban girdisi; yardımcı kubitler |00⟩):\n\n"
    s += md(t1, ["Halka", "kayıt kubiti", "k sayısı", "geçerli girdi doğru", "yardımcılar temiz",
                 "geçersiz girdi sayısı", "geçersiz → geçersiz kalır", "yöntem"])
    s += ("\n\nGeçerli hesaplama altuzayından sızıntı yoktur. Geçersiz girdiler (a ≥ q) geçerli bölgeye dönebilir ve yardımcı "
          "kubitleri kirli bırakabilir — gürültü bir durumu altuzay dışına itmişse sonraki aritmetik onu tanımsız biçimde "
          "geri getirebilir (Bölüm 9'daki sızıntı ölçümü).\n\n")
    t2 = [[k, v["wires"], f(v["X_max_abs_error_vs_reference"]), f(v["Z_max_abs_error_vs_reference"]),
           f(v["max_leakage_or_dirty_work"])] for k, v in r["gate_tests"].items()]
    s += "**(b) Kapı ayrıştırmaları vs. matris-içermeyen referans** (rastgele ring durumları):\n\n"
    s += md(t2, ["Halka", "tel", "X(u) max hata", "Z(v) max hata", "sızıntı/kirli yardımcı"])
    t3 = []
    for k, v in r["prop5_circuit"].items():
        rows = v.get("rows", [])
        t3.append([k, v["status"], v.get("wires"), f"{v.get('distinct_measured_syndromes')} / {v.get('|eps|')}",
                   f(min(x["syndrome_probability"] for x in rows), 12),
                   f(min(x["fidelity_with_X(e)psi"] for x in rows), 12),
                   f(max(x["fidelity_with_original_logical_state"] for x in rows[1:])),
                   f(sum(x["seconds"] for x in rows), 3)])
    s += "\n\n**(c) Devre içinde Önerme 5** (rastgele lojik durum → X(e), e ∈ ε → Z-tipi sendrom ancilla'ya):\n\n"
    s += md(t3, ["Halka", "durum", "tel", "ölçülen farklı sendrom / \\|ε\\|", "min sendrom olasılığı",
                 "min sadakat(veri, X(e)ψ)", "max sadakat(veri, ψ) e≠0", "toplam s"])
    t4 = [[k, v["status"], v.get("wires"), v.get("x_anc_orders"), "✓" if v.get("all_match") else "✗",
           len(v.get("rows", [])), f(sum(x["seconds"] for x in v.get("rows", [])), 3)] for k, v in r["x_syndrome_circuit"].items()]
    s += "\n\n**(d) X-tipi sendrom (faz kestirimi, DFT_N ancilla) — Z(f) hataları, f ∈ T_Z:**\n\n"
    s += md(t4, ["Halka", "durum", "tel", "ancilla mertebesi", "cebirle uyum", "hata sayısı", "toplam s"])
    t5 = [[k, v["status"], v.get("wires"), v.get("mcm_method"), len(v.get("rows", [])), f(v.get("min_fidelity"), 12)]
          for k, v in r["full_cycle"].items()]
    s += ("\n\n**(e) Tam QEC döngüsü — ALTERNATİF TASARIM** (X(a)Z(b) → iki sendrom orta-devre ölçümü → `qml.cond` "
          "ile geri besleme → veri yoğunluk matrisi):\n\n")
    s += md(t5, ["Halka", "durum", "tel", "MCM yöntemi", "(a,b) çifti", "min sadakat"])
    t6 = []
    for k, v in r["specs"].items():
        for name, sp in v.items():
            t6.append([k, name, sp.get("wires_allocated"), sp.get("num_gates"), sp.get("depth"),
                       sp.get("gate_types", {}).get("Toffoli", 0), sp.get("gate_types", {}).get("QubitUnitary", 0)])
    s += "\n\n**(f) Kaynak sayımı** (ayrıştırılmış kapı kümesi; X-sendrom turu Z325 için yalnızca sayıldı, simüle edilmedi):\n\n"
    s += md(t6, ["Halka", "devre", "tel", "kapı", "derinlik", "Toffoli", "QubitUnitary"])
    rep["PHASE5_PL_TABLE"] = s


def phase6(rep: dict):
    dq = latest("quantum", "phase6_noise", "qubit_level.csv")
    rows = list(csv.DictReader(open(dq / "qubit_level.csv", encoding="utf-8")))
    sel = ["0.0001", "0.001", "0.01", "0.1"]
    codes = ["ring", "modular", "no QEC", "[[5,1,3]]"]
    t = []
    for ch in dict.fromkeys(r["channel"] for r in rows):
        for p in sel:
            line = [ch, p]
            for c in codes:
                rr = [x for x in rows if x["channel"] == ch and x["p"] == p and x["code"].startswith(c)]
                line.append(f(rr[0]["logical_error_rate"]) if rr else "—")
            rr = [x for x in rows if x["channel"] == ch and x["p"] == p and x["code"].startswith("ring")]
            line.append(f(rr[0]["leakage"]) if rr else "—")
            line.append(f(rr[0]["no_recovery_logical_error_rate"]) if rr else "—")
            t.append(line)
    gdiff = max(float(r["gpu_minus_cpu_abs"]) for r in rows if r.get("gpu_minus_cpu_abs"))
    s = (f"Deney: `{rel(dq)}` · Şekil: `figures/noise_qubit_level_LER.png`\n\n"
         "**Lojik hata oranı (1 − F_e), kubit düzeyi kod-kapasitesi gürültüsü:**\n\n")
    s += md(t, ["kanal", "p", "halka Z25[i] (10q)", "standart Z625 (10q)", "kodlamasız (3q)", "[[5,1,3]]×3 (15q)",
                "halka: sızıntı", "halka: kurtarmasız LER"])
    s += f"\n\nGPU (complex64) ile CPU (complex128) arasındaki en büyük LER farkı: {f(gdiff)}."
    # where (if anywhere) the ring code beats no-QEC
    better = [(r["channel"], r["p"]) for r in rows if r["code"].startswith("ring") and
              float(r["logical_error_rate"]) < float(next(x for x in rows if x["code"].startswith("no QEC") and
                                                          x["channel"] == r["channel"] and x["p"] == r["p"])["logical_error_rate"])]
    s += ("\n\nHalka kodunun kodlamasız 3 kubitten **daha iyi** olduğu (kanal, p) noktaları: "
          + (", ".join(f"{a} {b}" for a, b in better) if better else "**hiçbiri**") + ".")
    rep["PHASE6_QUBIT_TABLE"] = s
    dr = latest("quantum", "phase6_noise", "qudit_level.csv")
    q = list(csv.DictReader(open(dr / "qudit_level.csv", encoding="utf-8")))
    tq = [[r["code"], r["hilbert_dim"], r["K"], r["p"], f(r["LER_unit_shift_exact"]), f(r["LER_qudit_depolarizing_exact"]),
           f(r["LER_unencoded_K_qudit_depolarizing"]), f(r["LER_paper_eps_error_model"])]
          for r in q if r["p"] in ("0.01", "0.1")]
    s = (f"**Qudit düzeyi genelleştirilmiş kanallar (kesin sayım)** — deney `{rel(dr)}`. Birim-kayma modeli: her "
         "bileşenin reel/sanal koordinatı bağımsız olarak p olasılıkla ±1 kayar (X için kayma, Z için faz-tekmesi). "
         "Qudit depolarizasyonu: p olasılıkla tüm d²−1 Pauli'den düzgün biri. ε-modeli: p olasılıkla X(e), e ∈ ε düzgün.\n\n")
    s += md(tq, ["kod", "dim", "K", "p", "LER birim-kayma", "LER qudit depolarizasyon", "kodlamasız K-qudit depol.",
                 "LER makalenin ε-modeli"])
    mc = list(csv.DictReader(open(dr / "montecarlo_cpu_gpu.csv", encoding="utf-8")))
    tm = [[r["code"], r["hilbert_dim"], r["device"], r["trials"], f(r["logical_error_rate"]), f(r["exact_LER"]),
           "✓" if r["exact_within_CI"] == "True" else "✗", f(r["seconds"]), f(r["us_per_trial"]), f(r.get("gpu_peak_MB") or None)]
          for r in mc]
    s += "\n\n**Monte-Carlo yörünge simülatörü (birim-kayma, p = 0.05) — kesin değere karşı doğrulama:**\n\n"
    s += md(tm, ["kod", "dim", "cihaz", "deneme", "MC LER", "kesin LER", "kesin %95 GA içinde", "s", "µs/deneme", "GPU tepe MB"])
    rep["PHASE6_QUDIT_TABLE"] = s
    res = json.loads((dr / "results.json").read_text(encoding="utf-8")).get("resources", {})
    tr = [[k, v.get("wires"), v.get("num_gates"), v.get("depth"), v.get("two_qubit_gates"), v.get("three_qubit_gates", 0) or 0]
          for k, v in res.items()]
    rep["PHASE6_RES_TABLE"] = md(tr, ["kod", "tel (veri+ancilla+yardımcı)", "kapı", "derinlik", "2-kubit", "Toffoli"])
    rep["_dq"], rep["_dr"] = rel(dq), rel(dr)


def phase5_gpu(rep: dict):
    """lightning.gpu runs inside WSL2 (Linux) - section 8.5."""
    s = []
    try:
        d = latest("quantum", "phase5_pennylane_gpu", "results.json", status=None)
    except FileNotFoundError:
        rep["PHASE5_GPU"] = "lightning.gpu çalıştırması bulunamadı (NOT RUN)."
        return
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    env = json.loads((d / "env.json").read_text(encoding="utf-8"))
    s.append(f"Deney: `{rel(d)}` (durum {st['status']}, {st['wall_time_s']:.0f} s) · platform `{env['platform']}` · "
             f"PennyLane {r.get('pennylane_version')} · cihaz `{r.get('device')}` · {r.get('c_dtype')} · "
             f"GPU {env.get('torch_device')}")
    t = []
    for k, v in r.get("gate_tests", {}).items():
        t.append([k, "X/Z kapıları vs referans", v["wires"], f"{f(v['X_max_abs_error_vs_reference'])} / {f(v['Z_max_abs_error_vs_reference'])}",
                  f(v["seconds_X"] + v["seconds_Z"])])
    for k, v in r.get("prop5_circuit", {}).items():
        rows = v.get("rows", [])
        if rows:
            t.append([k, "Önerme 5 (X(e), Z-sendromu)", v["wires"],
                      f"{v['distinct_measured_syndromes']}/{v['|eps|']} sendrom; min sadakat X(e)ψ {f(min(x['fidelity_with_X(e)psi'] for x in rows), 9)}",
                      f(sum(x["seconds"] for x in rows))])
    for k, v in r.get("x_syndrome_circuit", {}).items():
        rows = v.get("rows", [])
        t.append([k, f"X-sendromu ({v.get('mode', '')})", v.get("circuit_widths", v.get("wires")),
                  ("cebirle uyum ✓" if v.get("all_match") else "uyumsuz ✗") + f", {len(rows)} hata" if rows else v.get("reason", ""),
                  f(sum(x["seconds"] for x in rows)) if rows else "—"])
    for k, v in r.get("full_cycle", {}).items():
        t.append([k, "tam döngü, qml.measure + qml.cond", v.get("wires"), f"min sadakat {f(v.get('min_fidelity'), 9)}, {len(v.get('rows', []))} çift",
                  f(sum(x["seconds"] for x in v.get("rows", [])))])
    for k, v in r.get("full_cycle_coherent", {}).items():
        t.append([k, "tam döngü, koherent geri besleme", v.get("wires"), f"min sadakat {f(v.get('min_fidelity'), 9)}, {len(v.get('rows', []))} çift",
                  f(sum(x["seconds"] for x in v.get("rows", [])))])
    s.append(md(t, ["halka", "devre", "tel", "sonuç", "toplam s"]))
    try:
        db = latest("benchmarks", "bench_pennylane_devices", "bench_pennylane_devices.csv", status=None)
        rows = list(csv.DictReader(open(db / "bench_pennylane_devices.csv", encoding="utf-8")))
        tb = [[x["circuit"], x["wires"], x["device"], x["c_dtype"], f(x["seconds_min"]), f(x["speedup_vs_lightning_qubit"]),
               f(x["fidelity_vs_lightning_qubit_c128"], 12), f(x.get("gpu_used_MB_after_run") or None)] for x in rows]
        s.append(f"**Cihaz karşılaştırması** (aynı devre, aynı WSL2 ortamı; `{rel(db)}`; GPU belleği nvidia-smi ile cihaz geneli, "
                 "ekran ve diğer süreçler dahil):")
        s.append(md(tb, ["devre", "tel", "cihaz", "hassasiyet", "en iyi s", "hızlanma vs lightning.qubit",
                         "sadakat vs lightning.qubit c128", "GPU kullanılan MB"]))
    except FileNotFoundError:
        s.append("Cihaz karşılaştırması çalıştırılmadı (NOT RUN).")
    rep["PHASE5_GPU"] = "\n\n".join(s)


def decode_table(rep: dict):
    d = latest("algebra", "phase2_algebra", "decoder_exhaustive.csv")
    rows = list(csv.DictReader(open(d / "decoder_exhaustive.csv", encoding="utf-8")))
    t = []
    for r in rows:
        if r["oracle"] in ("bitmap", "pyset", "algebraic"):
            t.append([r["ring"], r["oracle"], int(r["ok"]) + int(r["not_in_C2"]) + int(r["no_candidate"]) + int(r["non_unique"]),
                      r["ok"], r["not_in_C2"], r["non_unique"], r["wrong"], r["membership_tests_total"],
                      f(r["seconds_all_R_best_of"]), f(r["us_per_word"]), f(r["memory_bytes_C1_oracle_est"])])
    rep["DECODE_TABLE"] = (f"Deney `{rel(d)}`.\n\n" + md(t, ["halka", "oracle", "test edilen sözcük", "başarılı decode",
                                                           "C2 dışı (reddedildi)", "çoklu aday", "yanlış", "üyelik testi",
                                                           "toplam s", "µs/sözcük", "oracle belleği (B, tahmini)"]))


def phase6_extra(rep: dict):
    dq = latest("quantum", "phase6_noise", "qubit_level.csv")
    rows = list(csv.DictReader(open(dq / "qubit_level.csv", encoding="utf-8")))
    st = json.loads((dq / "status.json").read_text(encoding="utf-8"))
    t = []
    for r in rows:
        if r["p"] != "0.01":
            continue
        t.append([r["channel"], r["code"][:28], f(r["logical_error_rate"]), f(r["average_fidelity"], 6),
                  f(r["recovery_success_rate"], 6), f(r["leakage"]), f(r["seconds"]),
                  f(r.get("gpu_seconds") or None), f(r.get("gpu_peak_MB") or None)])
    rep["PHASE6_QUBIT_TABLE"] += (
        "\n\n**Tüm metrikler, p = 0.01** (ortalama sadakat = (K·F_e+1)/(K+1); kurtarma başarısı = "
        "taban girdiler için ⟨j|çıktı|j⟩ ortalaması; süre = CPU complex128 / GPU complex64 tek nokta):\n\n" +
        md(t, ["kanal", "kod", "LER", "ort. sadakat", "kurtarma başarısı", "sızıntı", "CPU s", "GPU s", "GPU tepe MB"]) +
        f"\n\nCPU belleği satır başına ölçülmedi; çalıştırma başına süreç tepe çalışma kümesi {st.get('peak_wset_MB')} MB "
        f"(`status.json`), toplam süre {st['wall_time_s']:.0f} s. Devre derinliği ve kapı sayısı bu tablodaki kodlar için "
        "aşağıdaki kaynak tablosundadır (gürültü kod-kapasitesi modelinde kapılara uygulanmadı).")


def bench(rep: dict):
    try:
        d = latest("benchmarks", "bench_cpu_gpu", "bench.csv")
    except FileNotFoundError:
        rep["PHASE_BENCH"] = "Kıyaslama çalıştırılmadı (NOT RUN)."
        return
    rows = list(csv.DictReader(open(d / "bench.csv", encoding="utf-8")))
    t = [[r["workload"], r["device"], r["status"], f(r.get("wall_s_median")), f(r.get("wall_s_min")),
          f(r.get("speedup_vs_cpu_median")), f(r.get("gpu_peak_MB")), f(r.get("throughput_Msym_s"))] for r in rows]
    env = json.loads((d / "env.json").read_text(encoding="utf-8"))
    gpu = env.get("torch_device")
    s = (f"Deney: `{rel(d)}` (makine boştayken, 3 tekrar; GPU: {gpu}, sürücü CUDA "
         f"{env['nvidia_smi'].get('driver_cuda_version')}, torch CUDA {env.get('torch_cuda_build')}).\n\n")
    s += md(t, ["iş yükü", "cihaz", "durum", "medyan s", "min s", "hızlanma (CPU/GPU)", "GPU tepe MB", "Msembol/s"])
    s += ("\n\nNotlar: GPU satırları complex64, CPU yoğunluk-matrisi satırı complex128 kullanır (sonuç farkı Bölüm 9'da). "
          "PennyLane devreleri Windows'ta `lightning.qubit` (CPU, OpenMP) üzerinde koştu; PennyLane için CPU/GPU "
          "karşılaştırması WSL2'deki `lightning.gpu` ile Bölüm 8.5'tedir. Monte-Carlo CPU/GPU karşılaştırması Bölüm 9 tablosundadır.")
    rep["PHASE_BENCH"] = s


def tests(rep: dict):
    p = RES / "tests" / "test_report.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    s = (f"Kaynak: `results/tests/test_report.json` ({r['generated_utc'][:19]} UTC). Özet: **PASS {r['summary']['PASS']}, "
         f"FAIL {r['summary']['FAIL']}, NOT RUN {r['summary']['NOT RUN']}**.\n\n")
    bc = r.get("summary_by_category")
    if bc:
        s += md([[c, v["PASS"], v["FAIL"], v["NOT RUN"]] for c, v in bc.items()], ["test sınıfı", "PASS", "FAIL", "NOT RUN"]) + "\n\n"
    clean = lambda m: m.splitlines()[0].replace("AssertionError: ", "").replace("|", "\\|")[:110] if m else ""
    fails = [[t["test"].split("::")[-1].replace("|", "\\|"), t["test"].split("::")[0].replace("tests/", ""),
              t.get("category", ""), t["failure_class"], clean(t["message"])]
             for t in r["tests"] if t["outcome"] == "FAIL"]
    s += md(fails, ["FAIL testi", "dosya", "test sınıfı", "hata sınıfı", "mesaj"])
    nr = [t for t in r["tests"] if t["outcome"] == "NOT RUN"]
    s += "\n\nNOT RUN testleri: " + (", ".join(t["test"] for t in nr) if nr else "yok") + "."
    s += ("\n\nGevşetilmiş veya gizlenmiş test yoktur. `paper_claim` testleri makale ifadesini aynen doğrular; FAIL olmaları "
          "makale iddiasının sağlanmadığı anlamına gelir. Bu projenin uygulama testlerinin tamamı PASS'tir; "
          "tek 'implementation (original source)' FAIL'i yazar kodundaki gizli çift-dual hatasıdır (Bölüm 3). İnceleme sonrası "
          "sınıf güncellemeleri: Z9 satırı testleri ek olarak `outside_hypothesis` ile işaretlendi (makalenin hipotezi dışında); "
          "Tanım 6 ile ilgili testler `definition_consistency` sınıfında kaldı; Önerme 5 testi açıkça \"X-tipi okuma\" olarak "
          "belgelendi. Hiçbir FAIL silinmedi.")
    rep["TEST_SUMMARY"] = s


def gpu_results():
    try:
        d = latest("quantum", "phase5_pennylane_gpu", "results.json", status=None)
        return json.loads((d / "results.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def not_run_text() -> str:
    g = gpu_results() or {}
    xs = g.get("x_syndrome_circuit", {}).get("Z325", {})
    cc = g.get("full_cycle_coherent", {})
    b = []
    if g:
        b.append("* **lightning.gpu / cuQuantum (native Windows)**: kurulamıyor (`custatevec-cu12` Windows dağıtımı yok). "
                 "Çözüm olarak aynı makinedeki WSL2 Ubuntu'da kuruldu ve kullanıldı (Bölüm 8.5).")
    else:
        b.append("* **lightning.gpu / cuQuantum**: Windows'ta kurulamıyor; WSL2 çalıştırması yok (NOT RUN).")
    if xs.get("status") == "RUN":
        b.append(f"* **Z325[i] X-tipi sendromu tek devrede**: 32 tel (2³² genlik; complex128 ≈ 69 GB) bu GPU'ya sığmaz → NOT RUN. "
                 f"Bunun yerine her üreteç ayrı devrede ölçüldü (genişlikler {xs.get('circuit_widths')}), "
                 f"{len(xs.get('rows', []))} Z-hatası için; cebirle uyum: {'✓' if xs.get('all_match') else '✗'} (Bölüm 8.5). "
                 "Daha fazla hata denenmedi (hata başına dakikalar mertebesinde süre).")
    else:
        b.append("* **Z325[i] X-tipi sendrom devresinin simülasyonu**: NOT RUN (32 tel; üreteç başına 23/29 tel). "
                 "Matris-içermeyen qudit simülatörü ile aynı sendromlar doğrulandı (Bölüm 8.1–8.3).")
    ran = [k for k, v in cc.items() if v.get("status") == "RUN"]
    b.append("* **Tam QEC döngüsü**: Z25'te orta-devre ölçümü + `qml.cond` ile (Windows ve GPU); "
             + (f"{', '.join(ran)} için koherent geri beslemeyle GPU'da (Bölüm 8.5); " if ran else "")
             + "Z325 için NOT RUN — koherent geri besleme ancilla yeniden kullanamadığı için 36 tel (2³⁶ genlik) gerektirir; "
               "gerçek orta-devre ölçüm + sıfırlama ile 29 tel yeterli olurdu, denenmedi.")
    b += """* **Kubit düzeyi gürültü Z85/Z325 gömmelerinde**: yoğunluk matrisi 2¹⁴×2¹⁴ (Z85) / 2¹⁸×2¹⁸ (Z325) — Z325 için imkânsız, Z85 için 17²=289 girişin her biri 4.3 GB; çalıştırılmadı. Qudit düzeyinde aynı kodlar kesin sayımla ve GPU Monte-Carlo ile çalıştırıldı.
* **Gürültülü kapılar / devre-düzeyi gürültü (circuit-level)**: yapılmadı; ~10⁴ kapılık sendrom devreleri için bunun sonucu kod-kapasitesi sonuçlarından yalnızca daha kötü olabilir.
* **Kapı-düzeyi kodlayıcı (encoder)**: Düzen B (split koordinatlar) için yazıldı ve her j için referansla sadakat 1.0 doğrulandı (Bölüm 8.6). Düzen A (ikili a, b kayıtları) için kapı düzeyi kodlayıcı **yok** (NOT RUN); Düzen A deneylerinde giriş/çıkış genel bir kapı düzeyi durum hazırlama (Möttönen) ile yüklendi.
* **Makalenin "exact reproduction" kategorisindeki AWGN deneyleri**: yazar simülasyon kodu ve parametreleri olmadığı için mümkün değil; tümü bağımsız yeniden kurulum.
* **Stim**: kuruldu ama kullanılmadı — halka kodları qudit/aritmetik (Clifford olmayan) yapıdadır; kubit tabanı [[5,1,3]] için 5 kubitlik tam yoğunluk-matrisi hesabı örneklemeden daha kesin olduğundan tercih edildi; Stim genlik sönümünü temsil edemez.
* **SageMath**: kurulu değil; gerekmedi (tüm cebir doğrudan sayımla yapıldı).
* **Makaledeki Z5[i]⁴ örneğinin kendisi**: üreteçler yayımlanmadığı için yalnızca aynı boyutlarda bağımsız bir yapılandırma test edildi.""".splitlines()
    return "\n".join(b)


NEXT = """1. **Yazarlardan istenmesi gerekenler**: (i) Şekil 1–3 simülasyon betiği, sembol sayısı ve tohumlar; (ii) "25 elemanlı R_Q" takımyıldızının tanımı (Z[i]/(5) mi, Z[i]/(3+4i) mi) ve alıcı; (iii) Z5[i]⁴ örneğinin üreteçleri; (iv) Tanım 6 ile Örnek 6–7 arasındaki dual tanımının hangisinin kastedildiği ve Önerme 5'in hangi hata modeli (X mi Z mi) için iddia edildiği.
2. **Önerme 5'in düzeltilmiş biçimi** (ayrı çalışma olarak): X-hataları için doğru ifade "sendrom ⇔ e + C2 kosetini belirler" (çekirdek C2), Z-hataları için "sendrom ⇔ f + C1^⊥H". Z-okumasındaki "(ε−ε) ∩ C1^⊥H = {0} ⟺ |ε| farklı sendrom" denkliği n = 1'de q ∈ {25, 65, 85, 125, 325} için tüm geçerli ideal çiftlerinde ve Z5[i]⁴'te sayısal olarak doğrulandı (Bölüm 8.2). Hata kümesi tam olarak Z(ε) ise ayırt edilebilirlik düzeltilebilirliğe denktir (tanımlanan hatanın tersi uygulanır, artık 0; Knill–Laflamme), bu yüzden bu kısım açık değildir. C1^⊥H ⊆ C1 yeterli koşuldur (fark e_i − e_j ∉ C1 ⊇ C1^⊥H; 481/481 durumda sağlandı) ama gerekli değildir (16 durumda C1^⊥H ⊄ C1 iken de sağlanıyor). Kalan iş: koşulun ideal üreteçleri ve ε seçimi cinsinden gerekli-yeterli bir karakterizasyonu.
3. **Adil fiziksel karşılaştırma**: ikili kubit gömmelerinde (Düzen A ve B) halka kodu kodlamasızdan kötü; qudit düzeyi birim-kayma gürültüsünde iyi. Anlamlı bir avantaj için ya doğal qudit donanımı (d = 25 veya 625 seviyeli sistem; ör. trapped-ion/süperiletken qudit) için gerçekçi bir gürültü modeli (yakın-komşu seviye geçişleri ≈ birim-kayma modeli) ya da tek-bit hatalarını birim kaymaya eşleyen (Gray-kodu benzeri) bir rakam gömmesi gerekir. Düzen B'nin rakam yapısı (`SplitLayout`) bu tür bir gömme için hazır başlangıç noktasıdır.
4. **Devre-düzeyi gürültü**: sendrom çıkarımında 10⁴ mertebesinde kapı var; eşik analizi için gürültülü kapı simülasyonu (Monte-Carlo, GPU) ve daha ucuz modüler toplayıcılar (QFT'siz, Toffoli tabanlı) gerekli.
5. **Büyük devreler**: Z325 tam döngüsü için koherent geri besleme 36 tel ister (bu GPU'ya sığmaz); gerçek orta-devre ölçüm + sıfırlama (ör. PennyLane `mcm_method="tree-traversal"` / one-shot) ile ancilla yeniden kullanımıyla 29 tel (complex128 8.6 GB) yeterlidir — WSL2'deki `lightning.gpu` ile denenebilir.
6. **AWGN**: eşit hızlı karşılaştırmayı yumuşak-karar (soft-decision) koset/ML decoder ile tekrar etmek ve Eb/N0 ekseninde sunmak; makaledeki "kodlama kazancı" ifadesinin hız-ayarlı yeniden değerlendirmesi."""


def run_index(rep: dict):
    rows = []
    for cat in ("original", "algebra", "awgn", "quantum", "benchmarks"):
        for d in sorted((RES / cat).glob("*-*")):
            st = d / "status.json"
            if not d.is_dir():
                continue
            if not st.exists():
                rows.append([cat, f"`{d.name}`", "INCOMPLETE", "—",
                             "status.json yok: işlem dışarıdan sonlandırıldı (zaman aşımı ya da yavaşlık nedeniyle elle durduruldu); sonuç kullanılmadı, aynı yapılandırmanın sonraki tam çalıştırması kullanıldı"])
                continue
            s = json.loads(st.read_text(encoding="utf-8"))
            note = "; ".join(s.get("notes", []))[:120].replace("|", "\\|")
            if s["status"] == "ERROR":
                note = (s.get("error", "").strip().splitlines() or [""])[-1][:120].replace("|", "\\|")
            rows.append([cat, f"`{d.name}`", s["status"], f(s.get("wall_time_s")), note])
    rep["RUN_INDEX"] = md(rows, ["kategori", "deney kimliği", "durum", "süre s", "not / hata"]) + (
        "\n\nHiçbir çalıştırma silinmedi. ERROR/FAIL kayıtları geliştirme sırasında bulunan ve düzeltilen hatalara aittir "
        "(Phase 2: `multiples_transversal` şekil hatası; Phase 5 PennyLane: çift-kuyruklanan `qml.Adder`; PennyLane cihaz "
        "karşılaştırması: complex64 için fazla sıkı 1e-5 sadakat eşiği — ölçülen 0.99997–0.99999 değerleri tek hassasiyet "
        "yuvarlamasıdır, eşik 1e-4 yapıldı; `gate_level_css_devtest`: `lightning.qubit` yerel MCM tree-traversal'ın "
        "~1e-31 olasılıklı sayısal gürültü dalında çökmesi — segmentli motora geçişin nedeni; `review_checks` ilk çalıştırması: "
        "sağ iz duali kullanılmıştı, sol iz duali düzeltmesinden sonra yeniden çalıştırıldı; INCOMPLETE `zreading_condition` "
        "kayıtları: yavaş Python döngüleri nedeniyle durduruldu, vektörleştirmeden sonra tam çalıştırıldı); her biri "
        "düzeltmeden sonra aynı yapılandırmayla yeniden çalıştırılmış ve PASS olmuştur. Kısmi çalıştırmalar (`--only`, "
        "`--codes`) geliştirme amaçlıdır; rapor tabloları en son tam çalıştırmalardan üretilir.")


# ============================================================================ review + gate level
# Statements added in the second review round. Each is one literal so that reports/degisiklikler.py
# can list it verbatim in Ek C (apply_review_changes.py checks that the text is present here).
T_ZR_SUFF = "C1^⊥H ⊆ C1 yeterli koşuldur: ε, C2/C1'in bir transversali olduğundan i ≠ j için e_i − e_j ∉ C1 ⊇ C1^⊥H, dolayısıyla (ε−ε) ∩ C1^⊥H = {0}. Gerekli değildir: C1^⊥H ⊄ C1 olan bazı durumlarda da koşul sağlanır."
T_ZR_CE = "Makalenin kendi ayarında (n = 1, Teorem 4 hipotezleri) karşı-örnek: Z25[i]'de C1 = ⟨10−5i⟩ ⊂ C2 = ⟨2−i⟩ (K = 25). Burada C1^⊥H = C2 (ve C2^⊥H = C1); ε ⊂ C2 olduğundan ε − ε ⊂ C1^⊥H, yani her Z(e) tüm X-tipi üreteçlerle değişir ve sendromu 0'dır. Bu çift için Z-okuması hiçbir ε seçiminde sağlanmaz."
T_SEG = "Segmentli motor, her orta-devre ölçümünden sonra çökmüş (ve gerekiyorsa sıfırlanmış) durumu bir sonraki segmentin başında `qml.StatePrep` ile yeniden yükler. Bu bir simülasyon kontrol noktasıdır, kodlayıcı değildir (kodlayıcı tamamen kapı düzeyidir); PennyLane-yerel MCM çapraz kontrolünde StatePrep yoktur ve iki motor aynı dağılımı verir."
T_LEAK = "Sızıntı = gürültüden sonra, temel girdiler üzerinden ortalama, geçerli halka-elemanı seviyelerinin dışındaki popülasyon (kurtarma bunu kaybeder). Gürültüsüz devrede sızıntı yoktur: Düzen B kodlayıcısının sızıntısı 0'dır (adım 2) ve tam döngülerde min F ≥ 1 − 10⁻¹² olduğundan döngü sonundaki sızıntı ≤ 1 − F. Gürültülü sızıntı kanaldan gelir; Düzen B'de geçerli seviye oranı daha düşüktür (A: (25/32)² ≈ 0.61, B: (5/8)⁴ ≈ 0.15)."
T_Z65 = "Z65'te birim-kayma LER'i tam olarak 0'dır, çünkü 9 X-kayma deseninin ve 9 Z-kayma deseninin hepsi düzeltilir. Z25 ve Z85'te Z-desenlerinin 9'u, X-desenlerinin 5'i düzeltilir; düzeltilemeyen 4 desen (±1, ±1)'dir ve her birinin olasılığı p²/4 olduğundan LER = p²."
T_DEPOL = "Depolarizasyon Monte Carlo'su (her (kod, p) için bağımsız tohum) kesin formülle uyumludur. İlk çalıştırma tüm kodlar için aynı tohumu kullanmıştı; p = 0.2'de üç kodun ortak vuruş sayısı beklenenden ~2σ fazlaydı ve Z25 ile Z65'te kesin değer %95 GA'nın hemen dışında kaldı. Bu tek bir ortak dalgalanmadır, simülatör hatası değildir; o çalıştırma silinmedi."
T_DEPOL_CRIT = "Geçme ölçütü: her satırda koşullu binom p-değeri > 0.05 / satır sayısı (Bonferroni); aksi halde çalıştırma FAIL olarak işaretlenir. Koşulsuz %95 GA sütunu raporlanır ama ölçüt değildir (6 satırda en az bir GA ıskası ~%26 olasılıkla beklenir). Ölçüt ikinci çalıştırmanın verisi incelendikten sonra eklendi; en küçük koşullu p-değeri 0.18 olduğundan karar bu seçime duyarlı değildir."
T_MC_STATUS = "Bu tablodaki çalıştırma durumu (PASS) yalnızca çalıştırmanın tamamlandığını gösterir; istatistiksel kontrol GA sütunu ve aşağıdaki bağımsız tohum takibidir."
T_DEP_STMT = "Depolarizasyonda qudit düzeyinde avantaj ihmal edilebilir düzeydedir: LER = p·(1 − (N_X·N_Z − 1)/(d² − 1)); Z25 ve Z65'te ≈ 0.96·p, Z85'te ≈ 0.997·p (kod d² Pauli'nin yalnızca N_X·N_Z tanesini düzeltir; rastgele Pauli'lerin çoğu birim kayma değildir)."


def load_latest(category, prefix, fname="results.json", status=None):
    d = latest(category, prefix, fname, status=status)
    return d, json.loads((d / fname).read_text(encoding="utf-8")) if fname.endswith(".json") else None


def review_tables(rep: dict):
    d, r = load_latest("algebra", "review_checks", status="PASS")
    rows = [[x["q"], x["n_ideals"], x["closed_form_mismatches_all_ideals"], x["random_generators_tested"],
             x["closed_form_mismatches_random"], ", ".join(f"⟨{g}⟩" for g in x["def6_coincides_with_true_dual_for"]) or "yok"]
            for x in r["A1_closed_form"]]
    s = f"Deney `{rel(d)}`.\n\n" + md(rows, ["q", "ideal sayısı (tümü)", "kapalı form ≠ Ann (ideal)", "rastgele üreteç",
                                             "kapalı form ≠ Ann (rastgele)", "Tanım 6 = gerçek dual olan idealler"])
    ex = [[x["example"], x["role"], x["alpha"], x["|C|"], x["|true dual|"], x["|<sigma(alpha)>|"],
           "evet" if x["def6_equals_true_dual"] else "**hayır**"] for x in r["A1_example_generators"]]
    s += "\n\nMakale örneklerinin üreteçleri (α₁ ve α₂ ayrı ayrı):\n\n" + md(
        ex, ["örnek", "rol", "üreteç", "\\|C\\|", "\\|gerçek dual\\|", "\\|⟨σ(α)⟩\\|", "Tanım 6 doğru mu"])
    a1 = [x for x in r["A1_example_generators"] if x["role"].startswith("alpha1")]
    same = ", ".join(x["example"] for x in a1 if x["|true dual|"] == x["|<sigma(alpha)>|"]) or "—"
    diff = ", ".join(x["example"] for x in a1 if x["|true dual|"] != x["|<sigma(alpha)>|"]) or "—"
    s += (f"\n\nα₁ için: {same} örneklerinde boyutlar eşit (|⟨σ(α₁)⟩| = |gerçek dual|) ama kümeler farklı; {diff} "
          "örneğinde boyutlar da farklı. Yani Tanım 6 C₁ üreteçleri için de geçerli değildir.")
    rep["REVIEW_A1_TABLE"] = s
    b4 = r["B4_additive"]
    pr = b4["pair"]
    t = [["C = Z_q·1 (Z25[i])", b4["|C|"], "hayır" if not b4["C_is_R_module"] else "evet", b4["|C^perpH|"],
          b4["|C^perpTr| (left)"], b4["|C||C^perpH|"], b4["|C||C^perpTr|"], b4["|R|"]]]
    s = md(t, ["kod", "\\|C\\|", "R-modül", "\\|C^⊥H\\|", "\\|C^⊥Tr\\| (sol)", "\\|C\\|·\\|C^⊥H\\|", "\\|C\\|·\\|C^⊥Tr\\|", "\\|R\\|"])
    t2 = [[k.replace("_", " "), v["|D|"], v["noncommuting_pairs"], v["code_dimension"], v["dense_nullspace"]]
          for k, v in pr.items() if isinstance(v, dict)]
    s += (f"\n\nToplamsal çift C1 = Z_q·1 ⊂ C2 = Z_q·1 + Z_q·5i (K = |C2|/|C1| = {pr['K=|C2|/|C1|']}) için "
          "S = ⟨X(C1), Z(D)⟩:\n\n" + md(t2, ["D", "\\|D\\|", "komütatif olmayan çift", "kod boyutu (yapısal)", "kod boyutu (yoğun)"]))
    rep["REVIEW_B4_TABLE"] = s + f"\n\nDeney `{rel(d)}`."
    c2 = [[x["code"], x["trace_convention"], f(x["pauli_relation_max_error"]), "✓" if x["trace_dual_equals_hermitian_dual"] else "✗",
           x["noncommuting_pairs"], f"{x['K_structural']} / {x['K_formula']}", x["X_reading_C2_nonzero_syndromes"],
           f"{x['Z_reading_distinct_over_eps']} / {x['|eps|']}"] for x in r["C2_conventions"]]
    s = md(c2, ["kod", "Tr", "Pauli bağıntısı max hata", "iz duali = Hermitian dual",
                "komütatif olmayan çift", "K (yapısal / formül)", "X-okuması: C2'de sıfırdan farklı sendrom",
                "Z-okuması: farklı sendrom / \\|ε\\|"]) + f"\n\nDeney `{rel(d)}`."
    try:
        g = latest("quantum", "gate_level_css_2re", "results.json", status=None)
        gr = json.loads((g / "results.json").read_text(encoding="utf-8"))
        steps = gr["codes"]["Z25"]["steps"]
        cyc = steps.get("3_cycle_B_reuse", {})
        s += (f"\n\nKapı düzeyi devre de aynı konvansiyonla çalıştırıldı (`{rel(g)}`, Tr = {gr['trace_convention']}): adımlar "
              + ", ".join(f"{k} {v['status']}" for k, v in steps.items())
              + f"; tam döngü {cyc.get('runs')} çalışma, min sadakat {fid(cyc.get('min_fidelity'))}, yerel MCM çapraz kontrol "
              f"max |fark| {f(max((x['max_abs_diff_full_distribution'] for x in cyc.get('native_crosscheck', [])), default=None))}.")
    except FileNotFoundError:
        s += "\n\nKapı düzeyi devrenin 2re konvansiyonuyla çalıştırması: NOT RUN."
    rep["REVIEW_C2_TABLE"] = s


def zreading_table(rep: dict):
    try:
        d = latest("algebra", "zreading_condition", "pairs.csv", status=None)
    except FileNotFoundError:
        rep["ZREADING_TABLE"] = "Çalıştırma bulunamadı (NOT RUN)."
        return
    rows = list(csv.DictReader(open(d / "pairs.csv", encoding="utf-8")))
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    agg = {}
    for x in rows:
        key = (x["q"], x["eps_method"])
        a = agg.setdefault(key, {"pairs": 0, "eval": 0, "cond": 0, "p5": 0, "viol": 0, "invalid": 0})
        a["pairs"] += 1
        if x["status"] != "ok":
            a["invalid"] += 1
            continue
        a["eval"] += 1
        a["cond"] += x["condition"] == "True"
        a["p5"] += x["prop5_Z_reading_holds"] == "True"
        a["viol"] += x["equivalence_holds"] != "True"
    order = {"greedy": 0, "canonical": 1, "paper_multiples": 2}
    t = []
    for (q, m), a in sorted(agg.items(), key=lambda kv: (len(kv[0][0]), kv[0][0], order.get(kv[0][1], 3), kv[0][1])):
        if m.startswith("random") and q.startswith("5 (n=4)"):
            continue
        t.append([q, m, a["pairs"], a["invalid"], a["eval"], a["cond"], a["p5"], a["viol"]])
    rnd = [x for x in rows if x["q"].startswith("5 (n=4)") and x["eps_method"].startswith("random")]
    if rnd:
        t.append(["5 (n=4)", f"random ×{len(rnd)}", len(rnd), 0, len(rnd), sum(x["condition"] == "True" for x in rnd),
                  sum(x["prop5_Z_reading_holds"] == "True" for x in rnd), sum(x["equivalence_holds"] != "True" for x in rnd)])
    s = (f"Deney `{rel(d)}` (durum {st['status']}, {st['wall_time_s']:.0f} s; çift başına ayrıntı `pairs.csv`).\n\n"
         + md(t, ["q", "ε seçimi", "geçerli çift", "ε transversal değil", "değerlendirilen", "koşul sağlanıyor",
                  "\\|ε\\| farklı sendrom", "denklik ihlali"]))
    s += ("\n\nε seçimleri: *greedy* = Teorem 2 (indeks sırası); *canonical* = yazarların `find_epsilon_canonical` kuralı "
          "(r·α₂, (a,b) sırasıyla, yeni koset açanlar); *paper_multiples* = {0, α₂, …, (K−1)α₂} (yalnızca transversal "
          "olduğunda); *random* = tohumlu rastgele transversal. Denklik her çiftte ve her seçimde sağlanır (ihlal sütunu); "
          "koşulun kendisi ise ε seçimine ve çifte bağlıdır — Z-okuması genel bir önerme değildir.")
    ok = [x for x in rows if x["status"] == "ok"]
    suf = []
    for sub, label in (("True", "C1^⊥H ⊆ C1"), ("False", "C1^⊥H ⊄ C1")):
        rr = [x for x in ok if x["C1^perpH_subset_C1"] == sub]
        qs = list(dict.fromkeys(x["q"] for x in rr))
        suf.append([label, len(rr), sum(x["condition"] == "True" for x in rr),
                    ", ".join(f"q={q}: {sum(x['condition'] == 'True' for x in rr if x['q'] == q)}/{sum(1 for x in rr if x['q'] == q)}" for q in qs)])
    s += "\n\n" + T_ZR_SUFF + "\n\n" + md(suf, ["", "değerlendirme (çift × ε seçimi)", "koşul sağlanıyor", "q'ya göre"])
    ce = [x for x in ok if x["q"] == "25" and x["alpha1"] == "10+-5i" and x["alpha2"] == "2+-1i"]
    if ce and all(x["condition"] == "False" and x["distinct_syndromes"] == "1" for x in ce):
        s += ("\n\n" + T_ZR_CE + f" Veride: {len(ce)} ε seçimi ({', '.join(x['eps_method'] for x in ce)}), her birinde "
              f"\\|ε\\| = {ce[0]['|eps|']} ve 1 farklı sendrom; C1^⊥H = C2 eşitliği `hermitian_dual` ile ayrıca doğrulandı. "
              "Konjuge çift (⟨10+5i⟩ ⊂ ⟨2+i⟩) aynı sonucu verir.")
    else:
        print("WARNING: counterexample rows not found as expected; sentence omitted")
    rep["ZREADING_TABLE"] = s


def gate_level_section(rep: dict):
    try:
        d = latest("quantum", "gate_level_css", "results.json", status=None)
    except FileNotFoundError:
        rep["GATE_LEVEL_SECTION"] = "Çalıştırma bulunamadı (NOT RUN)."
        rep["_gl"] = None
        return
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    rep["_gl"] = (d, r, st)
    s = [f"Deney `{rel(d)}` (durum {st['status']}, {st['wall_time_s'] / 60:.0f} dk) · PennyLane {r['pennylane']} · "
         f"cihaz `{r['device']}` · karakter Tr = {r['trace_convention']} · `experiments/gate_level_css.py`, "
         "`src/epsqec/pl_circuits/split_layout.py`, `cycle.py`."]
    s.append(
        "**Düzen B (split koordinatlar).** CRT + ayırma ile Z_q[i] ≅ Π_b Z_{p^e} × Z_{p^e}, a+bi ↦ (a+s·b, a−s·b), "
        "s² ≡ −1 (Z25'te s = 7). Bu bir **halka izomorfizmidir** (çarpım bileşen bazında; σ bileşenleri takas eder) — "
        "Z25 ve Z65'te tüm çiftlerde doğrulandı. Her bileşen taban-p rakamlarla yazılır; her rakam ⌈log₂p⌉ kubitte "
        "(p = 5: 3 kubit, 3 geçersiz seviye). Her ideal rakam başına bir p-kuvveti idealidir, dolayısıyla "
        "C1 ⊆ C2 için her rakam **ölü** (hep 0), **etiket** (lojik rakam) veya **serbest** (düzgün) olur ve kod durumu "
        "rakamlar üzerinde çarpım durumudur. **Kodlayıcı**: serbest → DFT_p (yalnızca o rakamın kubitleri üzerinde "
        "QubitUnitary), etiket → lojik telden \"taşıma\" (CSHIFT(L→etiket), CSHIFT⁻¹(etiket→L); L |0⟩'a döner), ölü → "
        "kapı yok. Tüm küçük bloklar geçersiz seviyelerde birimdir (sızıntı yok). **X(u)**: rakam bazında sabit ekleme "
        "(taşımalar kontrollü kaydırmalarla). **Z(v)**: her kubite bir PhaseShift (faz χ(⟨v,x⟩_H), Tr = makalenin izi). "
        "**Sendromlar**: Z-tipi = Tr⟨v,x⟩ değerinin rakam ancilla'larına kontrollü sabit eklemelerle birikimi; "
        "X-tipi = her asal kuvvet p^f için X(u') faz kestirimi (rakam başına DFT_p, kontrollü X(c·p^pos·u'), taban-p "
        "Fourier dönüşümü: f = 2 için DFT_p, ikiz faz (ControlledPhaseShift), DFT_p — yoğun 25×25 DFT ile birebir aynı).")
    s.append(
        "**Orta-devre ölçümü.** Sendromlar **sıralı** ölçülür (sıra parametre: ZX = önce Z-tipi + X-düzeltmesi, sonra "
        "X-tipi + Z-düzeltmesi; XZ = tersi); ölçülen ancilla ölçülen değere çöker, kod çözme bu değerden yapılır; ortak "
        "ancilla yeniden kullanıldığında açıkça sıfırlanır (`reset=True`), ayrı kayıt varyantında sıfırlanmaz. Doğrulama "
        "**gidiş-dönüş** ile: girdi U_in|0⟩ (taban durumu ya da Möttönen ile rastgele süperpozisyon) → kodlayıcı → hata → "
        "sendromlar → düzeltme → kod çözücü → U_in† ; P(L = 0, veri = 0) tam olarak lojik sadakattir. "
        "Motor: PennyLane-yerel MCM `lightning.qubit` üzerinde çöktü (faz kestiriminden sonra ~10⁻³¹ olasılıklı sayısal "
        "gürültü dalını normalize etmeye çalışıyor); bu yüzden asıl motor, Lightning üzerinde **kesin segmentli simülasyon** "
        "(her ölçümde durum vektöründen kesin dağılım, çöküş + isteğe bağlı sıfırlama, ölçülen değerle klasik ileri besleme; "
        "atılan olasılık kütlesi raporlanır), ve her kodda rastgele çalışmalar **PennyLane-yerel MCM** "
        "(`default.qubit`, tree-traversal, `qml.measure`/`qml.cond`) ile yeniden simüle edildi. " + T_SEG)
    t = []
    for key, res in r["codes"].items():
        for name, sres in res["steps"].items():
            info = ""
            if name.startswith("1_"):
                info = (f"komütatif olmayan {sres.get('noncommuting_pairs')}, K {sres.get('dim_structural')}/{sres.get('K_formula')}, "
                        f"Gram−I {f(sres.get('gram_minus_I'))}, kapalı form dual {'✓' if sres.get('closed_form_dual_equals_enumerated') else '—'}")
            elif name.startswith("2_"):
                w = sres.get("wires", {})
                info = (f"en kötü sadakat {fid(sres.get('worst_fidelity'))}, süperpozisyon {fid(sres.get('superposition_fidelity'))}, "
                        f"sızıntı {f(sres.get('max_leakage'))}; tel: veri {w.get('data_qubits')}, L {w.get('logical_qubits')}, ancilla {w.get('ancilla_qubits')}")
            elif name.startswith("3_"):
                xc = sres.get("native_crosscheck") or []
                pm = str(sres.get("pairs_mode", ""))
                pm = "tüm" if pm == "exhaustive" else pm.replace("sampled ", "örneklenen ").replace(" of ", "/")
                info = (f"{pm} (a,b) çifti × 2 sıra + süperpozisyonlar = {sres.get('runs')} çalışma; "
                        f"F = 1 olan {sres.get('n_fidelity_1')}/{sres.get('runs')}, min F {fid(sres.get('min_fidelity'))}; "
                        f"{sres.get('wires')} tel; atılan olasılık ≤ {f(sres.get('max_discarded_probability'))}"
                        + (f"; yerel MCM çapraz kontrol {len(xc)} çalışma, max \\|fark\\| {f(max(x['max_abs_diff_full_distribution'] for x in xc))}" if xc else ""))
            elif name.startswith("4_"):
                rows = sres.get("rows", [])
                info = (f"{len(rows)} hata X(e), e ∈ ε∖{{0}}: tüm sendromlar 0 {'✓' if all(x['all_syndromes_zero'] for x in rows) else '✗'}, "
                        f"max \\|⟨ψ₀\\|X(e)\\|ψ₀⟩\\|² = {f(max((x['|<psi0|X(e)|psi0>|^2'] for x in rows), default=None))} → Önerme 5 karşı-örneği "
                        f"{'yeniden üretildi' if sres.get('reproduces_prop5_counterexample') else 'üretilemedi'}") if rows else sres.get("reason", "")
            elif name.startswith("5_"):
                info = (f"Z(e), e ∈ ε: {sres.get('distinct_syndromes')}/{sres.get('|eps|')} farklı sendrom; (ε−ε)∩C1^⊥H = {{0}}: "
                        f"{tr_bool(sres.get('condition_(eps-eps)_cap_C1perp_trivial'))}; denklik {'✓' if sres.get('equivalence_holds') else '✗'}; "
                        f"ölçülen = beklenen {'✓' if sres.get('measured_equals_expected') else '✗'}") if "rows" in sres else sres.get("reason", "")
            t.append([key, name, sres.get("status"), info, f(sres.get("seconds"))])
    s.append(md(t, ["halka", "adım", "durum", "sonuç", "s"]))
    s.append("Düzen A satırları (3_cycle_A): ikili |a⟩|b⟩ kayıtları, X(u) = `qml.Adder`, aynı sıralı sendrom/düzeltme; Düzen A "
             "için kapı düzeyi kodlayıcı yoktur, giriş/çıkış Möttönen durum hazırlamasıyla yüklendi (sadakatteki ~10⁻¹³ sapma "
             "bu hazırlamanın yuvarlamasından gelir).")
    s.append("**Düzen B devre şemaları (Z25[i])** — `experiments/draw_circuits.py`, simülasyondaki aynı `SplitCircuits` "
             "yöntemleriyle; tel adları rakam adlarıdır (U5d1 = U bileşeni, p = 5, rakam 1):\n\n"
             "![Düzen B kodlayıcı](../figures/circuits/splitB_encoder.png)\n\n"
             "![Düzen B X(1) kapısı (taşımalı rakam ekleme)](../figures/circuits/splitB_X.png)\n\n"
             "![Düzen B Z-tipi sendrom](../figures/circuits/splitB_syndrome_Z.png)\n\n"
             "![Düzen B X-tipi sendrom (taban-5 faz kestirimi)](../figures/circuits/splitB_syndrome_X.png)")
    rep["GATE_LEVEL_SECTION"] = "\n\n".join(s)


def noise_layout_tables(rep: dict):
    try:
        d = latest("quantum", "noise_layouts", "results.json", status=None)
    except FileNotFoundError:
        rep["QUDIT_SUMMARY_TABLE"] = rep["NOISE_LAYOUTS_TABLE"] = "Çalıştırılmadı (NOT RUN): kapı düzeyi adımlar bekleniyor."
        return
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    r = json.loads((d / "results.json").read_text(encoding="utf-8"))
    q = list(csv.DictReader(open(d / "qudit_level.csv", encoding="utf-8"))) if (d / "qudit_level.csv").stat().st_size else []
    t = [[x["code"], x["hilbert_dim"], x["K"], x["p"], f(x["LER_unit_shift_exact"]), f(x["LER_uncoded_K_qudit_unit_shift"]),
          f(x["LER_uncoded_ring_qudit_unit_shift"]), f(x["LER_qudit_depolarizing_exact"]), f(x["LER_uncoded_K_qudit_depolarizing"])]
         for x in q if x["p"] in ("0.001", "0.01", "0.1")]
    mc = list(csv.DictReader(open(d / "qudit_mc.csv", encoding="utf-8"))) if (d / "qudit_mc.csv").stat().st_size else []
    s = (f"Deney `{rel(d)}` (kapı düzeyi kaynak: `{r['gate_level_source']}`; adımlar 1–5 geçenler: "
         f"{', '.join(k for k, v in r['gate_level_all_steps_pass'].items() if v) or 'yok'}).\n\n")
    s += md(t, ["kod", "dim", "K", "p", "**kod: birim-kayma**", "kodlamasız K-qudit (birim-kayma)",
                "kodlamasız halka qudit'i (birim-kayma)", "kod: qudit depolarizasyon", "kodlamasız K-qudit depol."])
    s += ("\n\nBirim-kayma modeli: her X- ve Z-koordinatı (gerçel/sanal) bağımsız olarak p olasılıkla ±1 kayar. Kodlamasız "
          "K-qudit: aynı model, bir X ve bir Z koordinatı (LER = 1 − (1−p)²). " + T_DEP_STMT)
    s += unit_shift_mc_text(mc)
    s += depolarizing_text()
    rep["QUDIT_SUMMARY_TABLE"] = s
    if not (d / "qubit_level.csv").exists():
        rep["NOISE_LAYOUTS_TABLE"] = "Kubit düzeyi: NOT RUN (kapı düzeyi adımlar geçmedi)."
        return
    noise_qubit_text(rep, d, st)


def depolarizing_text() -> str:
    s = ""
    try:
        dp = latest("quantum", "qudit_depolarizing_mc", "results.json")
        dr = json.loads((dp / "results.json").read_text(encoding="utf-8"))
        pt = [[x["code"], x["|R|"], f"{x['X_corrected']}/{x['patterns']}", x["X_uncorrected_shifts"] or "—",
               f"{x['Z_corrected']}/{x['patterns']}", x["Z_uncorrected_shifts"] or "—", x["N_X (all u in R)"], x["N_Z (all v in R)"]]
              for x in dr["patterns"]]
        s += ("\n\n**Birim-kayma desenleri ve depolarizasyon için düzeltilebilir Pauli sayıları** "
              f"(`{rel(dp)}`):\n\n" + md(pt, ["kod", "d = \\|R\\|", "X-desen düzeltilen", "düzeltilemeyen X-kaymaları",
                                             "Z-desen düzeltilen", "düzeltilemeyen Z-kaymaları", "N_X", "N_Z"]))
        s += "\n\n" + T_Z65
        dt = [[x["code"], x["p"], x["seed"], x["trials"], x["hits"], x["failures"], f(x["MC_LER"]), f"[{f(x['ci_low'])}, {f(x['ci_high'])}]",
               f(x["exact_LER"]), "✓" if x["exact_within_CI"] else "✗", f(x["conditional_binom_p"]), x["device"]] for x in dr["rows"]]
        s += ("\n\nQudit depolarizasyon Monte Carlo'su kesin değere karşı (vuruş = Pauli uygulanan deneme; koşullu test: "
              "başarısızlık \\| vuruş ~ Binom(vuruş, 1 − (N_X·N_Z − 1)/(d² − 1))):\n\n"
              + md(dt, ["kod", "p", "tohum", "deneme", "vuruş", "başarısız", "MC LER", "%95 GA", "kesin", "GA içinde",
                        "koşullu p-değeri", "cihaz"]))
        runs = sorted(p_ for p_ in (ROOT / "results" / "quantum").glob("qudit_depolarizing_mc-*") if (p_ / "results.json").exists())
        first = json.loads((runs[0] / "results.json").read_text(encoding="utf-8"))["rows"] if runs else []
        n_out = sum(not x["exact_within_CI"] for x in first)
        st_dp = json.loads((dp / "status.json").read_text(encoding="utf-8"))["status"]
        s += (f"\n\n{T_DEPOL_CRIT} Bu çalıştırmada eşik {f(dr.get('bonferroni_threshold'))}, en küçük koşullu p-değeri "
              f"{f(min(x['conditional_binom_p'] for x in dr['rows']))}, durum **{st_dp}**.")
        s += "\n\n" + T_DEPOL + (f" İlk çalıştırma: `{rel(runs[0])}` ({n_out}/{len(first)} satırda kesin değer GA dışında; "
                                 "o sırada geçme ölçütü yoktu ve durum PASS olarak yazıldı)."
                                 if runs and runs[0] != dp else "")
    except FileNotFoundError:
        s += "\n\nQudit depolarizasyon Monte Carlo'su: NOT RUN."
    return s


def unit_shift_mc_text(mc) -> str:
    s = ""
    if mc:
        s += "\n\nMonte Carlo (p = 0.05) kesin değere karşı:\n\n" + md(
            [[x["code"], x["device"], x["trials"], f(x["logical_error_rate"]), f(x["exact_LER"]), "✓" if x["exact_within_CI"] == "True" else "✗",
              f(x["seconds"])] for x in mc], ["kod", "cihaz", "deneme", "MC LER", "kesin", "kesin %95 GA içinde", "s"])
        s += "\n\n" + T_MC_STATUS
        try:
            dm = latest("quantum", "mc_seed_check", "results.json")
            sm = json.loads((dm / "results.json").read_text(encoding="utf-8"))["summary"]
            s += (f"\n\nZ25 satırında kesin değer %95 GA'nın hemen dışında kaldı (CPU ve GPU aynı tohumu kullandığı için tek bir "
                  f"örnek). Bağımsız tohumlarla takip (`{rel(dm)}`): 10 tohum × 40 000 deneme, birleşik LER "
                  f"{f(sm['pooled_LER'])} vs kesin {f(sm['exact_LER'])} (z = {sm['z_score']:.2f}), kesin değer birleşik GA içinde; "
                  f"10 tohumun {10 - sm['seeds_with_exact_outside_CI']}'unda GA kesin değeri içeriyor → istatistiksel dalgalanma, "
                  "simülatörde yanlılık yok.")
        except FileNotFoundError:
            pass
    return s


def noise_qubit_text(rep: dict, d: Path, st: dict):
    rows = list(csv.DictReader(open(d / "qubit_level.csv", encoding="utf-8")))
    codes = list(dict.fromkeys(x["code"] for x in rows))
    t = []
    for ch in dict.fromkeys(x["channel"] for x in rows):
        for p in ("0.001", "0.01", "0.1"):
            line = [ch, p]
            for c in codes:
                rr = [x for x in rows if x["channel"] == ch and x["p"] == p and x["code"] == c]
                line.append(f(rr[0]["logical_error_rate"]) if rr else "—")
            t.append(line)
    s = md(t, ["kanal", "p"] + codes)
    xc = [x for x in rows if x.get("cpu_complex128_LER")]
    if xc:
        s += ("\n\nDüzen B (12 kubit) GPU'da complex64 ile hesaplandı; p = " + xc[0]["p"] + "'de CPU complex128 ile en büyük fark "
              + f(max(float(x["gpu_minus_cpu_abs"]) for x in xc)) + ".")
    lk = []
    la, lb = (next((c for c in codes if "layout " + k in c), None) for k in ("A", "B"))
    for ch in dict.fromkeys(x["channel"] for x in rows):
        for p in ("0.001", "0.01", "0.1"):
            ra = [x for x in rows if x["channel"] == ch and x["p"] == p and x["code"] == la]
            rb = [x for x in rows if x["channel"] == ch and x["p"] == p and x["code"] == lb]
            if ra and rb:
                lk.append([ch, p, f(ra[0]["leakage"]), f(rb[0]["leakage"]), f(ra[0]["logical_error_rate"]), f(rb[0]["logical_error_rate"])])
    if lk:
        s += ("\n\n**Sızıntı, Düzen A ve Düzen B** (aynı çalıştırma, `qubit_level.csv`):\n\n"
              + md(lk, ["kanal", "p", f"sızıntı: {la}", f"sızıntı: {lb}", f"LER: {la}", f"LER: {lb}"]) + "\n\n" + T_LEAK)
    s += ("\n\nKodlamasız referanslar: *minimal* = 5 seviye 3 kubitte; *aynı kayıt (strict)* = lojik j, kodun kaydında tek "
          "taban durumu |t_j⟩ olarak saklanır ve kayıttaki her değişiklik hata sayılır; *etiket rakamı* = Düzen B kaydında yalnızca "
          "etiket rakamı okunur (diğer kubitler boşta) — bu, minimal referansla aynı sonucu verir (beklenen; doğrulama). "
          f"Deney `{rel(d)}`, süre {st['wall_time_s'] / 60:.0f} dk.")
    rep["NOISE_LAYOUTS_TABLE"] = s


def ek_c(rep: dict):
    log = json.loads((ROOT / "reports" / "degisiklikler.json").read_text(encoding="utf-8"))
    ph = ("REVIEW_A1_TABLE", "REVIEW_B4_TABLE", "REVIEW_C2_TABLE", "ZREADING_TABLE", "GATE_LEVEL_SECTION",
          "QUDIT_SUMMARY_TABLE", "NOISE_LAYOUTS_TABLE")

    def clean(t):
        for p in ph:
            t = t.replace(p, f"[tablo: {p.lower()}]")
        return t

    out = ["Bu ek, ikinci yazarın incelemesinden sonra raporda, özet dosyasında ve üretilen metinde değişen her ifadenin "
           "eski ve yeni halini listeler (kaynak: `reports/degisiklikler.py` → `reports/degisiklikler.json`; uygulayan betik "
           "`experiments/apply_review_changes.py` eski metin bulunamazsa durur). \"Eski: —\" yeni eklenen metin demektir. "
           "Hiçbir FAIL kaydı silinmedi; sınıf güncellemeleri Bölüm 13'tedir."]
    for c in log:
        out.append(f"**{c['id']}** · inceleme maddesi {c['madde']} · {c['bolum']} · dosya `{c['file']}`\n\n"
                   f"*Gerekçe:* {c['neden']}\n\n"
                   + (f"*Not:* bu metnin bir kısmı sonradan {', '.join(c['revised_by'])} ile yeniden değişti.\n\n" if c.get("revised_by") else "")
                   + "*Eski:*\n\n" + ("\n".join("> " + ln for ln in clean(c["eski"]).splitlines()) if c["eski"] else "> —")
                   + "\n\n*Yeni:*\n\n" + "\n".join("> " + ln for ln in clean(c["yeni"]).strip("\n").splitlines()))
    rep["EK_C"] = "\n\n".join(out)


def main():
    tpl = (ROOT / "reports" / "teknik_rapor.template.md").read_text(encoding="utf-8")
    rep = {}
    phase5(rep)
    phase5_pl(rep)
    phase5_gpu(rep)
    phase6(rep)
    phase6_extra(rep)
    decode_table(rep)
    bench(rep)
    review_tables(rep)
    zreading_table(rep)
    gate_level_section(rep)
    noise_layout_tables(rep)
    tests(rep)
    run_index(rep)
    rep["NOT_RUN_LIST"] = not_run_text()
    rep["NEXT_LIST"] = NEXT
    ek_c(rep)  # last: its text mentions placeholder names only in cleaned form
    for k, v in rep.items():
        if not k.startswith("_") and k != "EK_C":
            tpl = tpl.replace(k, v)
    tpl = tpl.replace("EK_C", rep["EK_C"])
    out = ROOT / "reports" / "teknik_rapor.md"
    out.write_text(tpl, encoding="utf-8")
    names = ("PHASE5_TABLE", "PHASE6_QUBIT_TABLE", "PHASE_BENCH", "TEST_SUMMARY", "REVIEW_A1_TABLE", "REVIEW_B4_TABLE",
             "REVIEW_C2_TABLE", "ZREADING_TABLE", "GATE_LEVEL_SECTION", "QUDIT_SUMMARY_TABLE", "NOISE_LAYOUTS_TABLE", "EK_C")
    left = [k for k in names if k in tpl]
    print("written", out, "| unresolved placeholders:", left)
    write_gate_level_summary(rep)


def write_gate_level_summary(rep: dict):
    """reports/kapi_duzeyi_ozet.md: short Turkish summary of the gate-level work (numbers from results)."""
    gl = rep.get("_gl")
    lines = ["# Kapı düzeyi CSS simülasyonu — kısa özet", "",
             "Bu dosya `experiments/make_report.py` tarafından sonuç dosyalarından üretilir; her sayının yanında deney kimliği vardır.", ""]
    if gl is None:
        lines.append("Kapı düzeyi deney bulunamadı (NOT RUN).")
    else:
        d, r, st = gl
        lines += [f"Kaynak deney: `{rel(d)}` (durum **{st['status']}**).", "", "## Ne çalıştı", ""]
        for key, res in r["codes"].items():
            for name, s in res["steps"].items():
                if s.get("status") == "PASS":
                    if name.startswith("2_"):
                        lines.append(f"- **{key}, kapı düzeyi kodlayıcı (Düzen B)**: her j için referansla en kötü sadakat {fid(s['worst_fidelity'])}; "
                                     f"L ve ancilla |0⟩'a döndü; sızıntı {f(s['max_leakage'])}.")
                    elif name.startswith("3_"):
                        pm = str(s["pairs_mode"])
                        pm = "tüm" if pm == "exhaustive" else pm.replace("sampled ", "örneklenen ").replace(" of ", "/")
                        lay = {"3_cycle_B_reuse": "Düzen B, ortak ancilla + sıfırlama", "3_cycle_B": "Düzen B, ayrı ancilla kayıtları",
                               "3_cycle_A": "Düzen A"}.get(name, name)
                        lines.append(f"- **{key}, tam döngü ({lay})**: {s['runs']} çalışma ({pm} (a,b) hata çifti, ZX ve XZ sırası, taban + rastgele "
                                     f"süperpozisyon girdileri), min sadakat {fid(s['min_fidelity'])}, {s['wires']} tel.")
                    elif name.startswith("4_"):
                        lines.append(f"- **{key}, negatif kontrol**: X(e), e ∈ ε∖{{0}} → tüm sendromlar 0 ve ⟨ψ₀|X(e)|ψ₀⟩ = 0 (Önerme 5 karşı-örneği devrede).")
                    elif name.startswith("5_"):
                        lines.append(f"- **{key}, Z(e) okuması**: {s['distinct_syndromes']}/{s['|eps|']} farklı sendrom; "
                                     f"(ε−ε)∩C₁^⊥H = {{0}}: {tr_bool(s['condition_(eps-eps)_cap_C1perp_trivial'])} — denklik sağlanıyor.")
        lines += ["", "## Ne çalışmadı / yapılmadı", ""]
        bad = [(k, n, s) for k, res in r["codes"].items() for n, s in res["steps"].items() if s.get("status") != "PASS"]
        lines += [f"- {k} {n}: **{s.get('status')}** — {s.get('reason', s.get('error', ''))}" for k, n, s in bad] or ["- Tüm adımlar geçti."]
        lines += ["- `lightning.qubit` üzerinde PennyLane-yerel MCM (tree-traversal) faz kestiriminden sonra sayısal gürültü dalında çöküyor; "
                  "asıl motor kesin segmentli simülasyon, yerel MCM (`default.qubit`) ile çapraz doğrulandı.",
                  "- Düzen A için kapı düzeyi kodlayıcı yok (Möttönen ile yükleme)."]
        smp = [f"{k} {n}: {s['pairs_mode'].replace('sampled ', '').replace(' of ', '/')}"
               for k, res in r["codes"].items() for n, s in res["steps"].items() if str(s.get("pairs_mode", "")).startswith("sampled")]
        exh = [f"{k} {n}" for k, res in r["codes"].items() for n, s in res["steps"].items() if s.get("pairs_mode") == "exhaustive"]
        lines += [f"- Tam döngü tüm T_X × T_Z hata çiftleri üzerinde yalnızca şu varyantlarda: {', '.join(exh)}. Örneklemeli: "
                  f"{'; '.join(smp)} çift (her biri iki sırada). Z₃₂₅ tam döngü: genişlik nedeniyle yapılmadı.",
                  "- Gürültü yalnızca kod-kapasitesi modelinde (kodlanmış duruma bir kez gürültü, ardından ideal kurtarma); "
                  "sendrom devresinin kendisi gürültüsüz kabul edildi (devre düzeyi / hataya dayanıklı gürültü yapılmadı)."]
    lines += ["", "## Gürültü (adım 6)", "", rep.get("QUDIT_SUMMARY_TABLE", "—"), "", rep.get("NOISE_LAYOUTS_TABLE", "—"), ""]
    lines += ["## Notlar", "",
              "- Karakter χ kodda tek yerde (`GaussianRing.trace_convention`); alternatif Tr = 2a ile aynı kapı düzeyi döngü de "
              "geçti (`gate_level_css_2re-*`, teknik rapor Bölüm 5.7).",
              "- Devre operatörleri yoğun matris olarak kurulmadı (yalnızca ≤ 625 boyutlu bağımsız kontroller ve rakam başına "
              "küçük QubitUnitary blokları). **İstisna**: adım 6'daki kubit düzeyi gürültü, kesin değerlendirme için tam kaydın "
              "yoğunluk matrisiyle (Düzen A: 1024, Düzen B: 4096 boyut) hesaplandı — bu bir operatör değil durum gösterimidir.",
              "- Düzen B devre şemaları: `figures/circuits/splitB_*.png`; ayrıntılar: teknik rapor Bölüm 8.6.", ""]
    (ROOT / "reports" / "kapi_duzeyi_ozet.md").write_text("\n".join(lines), encoding="utf-8")
    print("written reports/kapi_duzeyi_ozet.md")


if __name__ == "__main__":
    main()
