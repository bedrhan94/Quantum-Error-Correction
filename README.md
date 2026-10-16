# epsilon_qec_research

Independent, reproducible implementation of

> M. Güzeltepe, N. Aytaç, *ε-Quantum error correction codes over the ring R_Q*,
> Finite Fields and Their Applications 117 (2027) 102881, doi:10.1016/j.ffa.2026.102881

plus a test of whether its ring codes can be turned into physical quantum circuits (PennyLane).
The technical report (Turkish) is [reports/teknik_rapor.md](reports/teknik_rapor.md); a one-page Turkish
summary of what was done and found is [CALISMA_OZETI.md](CALISMA_OZETI.md); the gate-level CSS simulation has its own
short summary [reports/kapi_duzeyi_ozet.md](reports/kapi_duzeyi_ozet.md).  Changes made after the second-author review
are kept as data in `reports/degisiklikler.py` (old -> new, applied by `experiments/apply_review_changes.py`, rendered as
Ek C of the report).  The character chi (trace convention) is fixed in one place: `GaussianRing.trace_convention`.

## Layout

| Path | Content |
|---|---|
| `original_source/` | authors' code `epsilon codes.py` and the paper PDF, **unchanged** (SHA-256 recorded in Phase 1); `paper/appendix_A_transcribed.py` is a hand transcription of the Appendix A listing. The publisher's PDF is **not** in the git repository (copyright); to rerun Phase 1 and `experiments/extract_paper_figures.py`, download it via the DOI above and save it as `original_source/paper/1-s2.0-S1071579726000924-main.pdf` |
| `src/epsqec/ring` | arithmetic in Z_q[i] (vectorised) and exact Z[i] arithmetic for norm/gcd cross-checks |
| `src/epsqec/ideals` | additive codes as enumerated bitmaps; Hermitian dual (true complement), Definition 6 dual, trace dual, Euclidean dual |
| `src/epsqec/decoder` | coset transversals, instrumented ε-decoder (3 membership oracles), direct quotient-map baseline |
| `src/epsqec/css` | paper examples (as claims), structural analysis, builders |
| `src/epsqec/stabilizer` | matrix-free generalised Pauli operators, Theorem 4 stabilizer code, syndromes, Knill–Laflamme |
| `src/epsqec/pl_circuits` | PennyLane circuits; named so it cannot shadow `pennylane`. `ring_circuits.py` = layout A (binary a, b registers, `qml.Adder`); `split_layout.py` = layout B (CRT + split coordinates, base-p digits, gate-level encoder, digit adders, radix-p phase estimation); `cycle.py` = QEC-cycle programs with mid-circuit measurement, run natively (PennyLane MCM) or by the exact segmented engine |
| `src/epsqec/noise` | qubit channels, embedded codes + ideal recovery, exact logical-channel metrics, GPU Monte-Carlo |
| `src/epsqec/simulation` | AWGN constellations, receivers and SER Monte-Carlo (torch, CPU/GPU) |
| `src/epsqec/benchmarking` | experiment bookkeeping (ids, env capture, CSV/JSON), plot style |
| `configs/` | one TOML per experiment — every number used by a run comes from here |
| `experiments/` | one script per phase + plotting + CPU/GPU benchmark |
| `results/<category>/<experiment-id>/` | `config.json`, `env.json` (GPU, CUDA, Python, package versions, seed), `results.json`, CSV tables, `status.json` |
| `figures/` | PNG figures; every figure carries the experiment id and config hash it was drawn from |
| `tests/` | pytest suite; `results/tests/test_report.{json,csv}` lists PASS / FAIL / NOT RUN with failure class |

## Setup (Windows, as used for every run in `results/`)

```powershell
python -m venv .venv
# CUDA build of torch first (a plain `pip install torch` gives the CPU-only build on Windows):
.venv\Scripts\python.exe -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_arch_list())"
```

(The runs in `results/` used `python -m venv --system-site-packages .venv` on a machine where the cu128 torch
build was already installed globally.)  Without a GPU every experiment still runs on CPU; GPU rows are then
recorded as CPU (`device` column) or NOT RUN — never substituted silently.

`pennylane-lightning-gpu` / cuQuantum cannot be installed on native Windows (no `custatevec-cu12`
wheels). On Windows PennyLane circuits run on `lightning.qubit` (CPU); GPU acceleration is used through
PyTorch (AWGN, density matrices, Monte-Carlo trajectories) and always reported per row.

### lightning.gpu through WSL2 (same machine)

```powershell
wsl -d Ubuntu -- bash /mnt/c/<path>/epsilon_qec_research/wsl/setup_wsl_gpu.sh   # venv ~/venvs/epsqec, Python 3.12
wsl -d Ubuntu --cd /mnt/c/<path>/epsilon_qec_research -- ~/venvs/epsqec/bin/python experiments/phase5_pennylane.py --config phase5_pennylane_gpu.toml
wsl -d Ubuntu --cd /mnt/c/<path>/epsilon_qec_research -- ~/venvs/epsqec/bin/python experiments/bench_pennylane_devices.py
```

The setup script installs the same package versions plus `pennylane-lightning-gpu==0.45.0` (cuStateVec,
`custatevec-cu12`) and checks `lightning.gpu` against `lightning.qubit` (`wsl/verify_wsl_gpu.py`). Results are
written into the same `results/` tree; `env.json` records the Linux platform. (From Git Bash prefix the
commands with `MSYS_NO_PATHCONV=1`.)

## Reproduce

```powershell
.venv\Scripts\python.exe run_all.py            # all phases, then pytest
.venv\Scripts\python.exe run_all.py --list     # the individual commands
.venv\Scripts\python.exe -m pytest -q          # tests only
```

`pytest` exits non-zero **by design**: tests marked `paper_claim` assert statements of the paper
literally, and several of them do not hold (classified as *mathematical* in the test report).
