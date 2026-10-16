"""Experiment bookkeeping (single local machine).

Every experiment run creates   results/<category>/<experiment_id>/   containing
  config.json   - the exact configuration used (after defaults were applied)
  env.json      - machine / GPU / CUDA / Python / package versions, seed, timestamps
  results.json  - machine-readable results  (+ any CSV tables written by the experiment)
  status.json   - PASS / FAIL / PARTIAL / ERROR with wall time and peak memory
The experiment id is  <name>-<UTC timestamp>-<host>-<config hash>; runs of the same config share
the hash.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib
import json
import os
import platform
import socket
import subprocess
import sys
import time
import tomllib
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULTS_ROOT = PROJECT_ROOT / "results"
CONFIG_ROOT = PROJECT_ROOT / "configs"

_PACKAGES = [
    "numpy", "scipy", "sympy", "pandas", "matplotlib", "torch", "pennylane",
    "pennylane_lightning", "stim", "psutil", "pytest", "pypdf",
]


def _pkg_version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        dist = {"pennylane_lightning": "pennylane_lightning"}.get(name, name)
        return version(dist)
    except Exception:
        try:
            return getattr(importlib.import_module(name), "__version__", "unknown")
        except Exception:
            return None


def _nvidia_smi() -> dict:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return {"available": False, "error": out.stderr.strip()}
        gpus = []
        for line in out.stdout.strip().splitlines():
            name, mem, drv, cc = [s.strip() for s in line.split(",")]
            gpus.append({"name": name, "memory_MiB": int(mem), "driver": drv, "compute_cap": cc})
        hdr = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=20).stdout
        cuda_drv = None
        for tok in hdr.split("|"):
            if "CUDA Version" in tok:
                cuda_drv = tok.split("CUDA Version:")[-1].strip()
        return {"available": True, "gpus": gpus, "driver_cuda_version": cuda_drv}
    except Exception as exc:  # no driver / not installed
        return {"available": False, "error": repr(exc)}


def environment_info() -> dict:
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_logical": os.cpu_count(),
        "python": sys.version,
        "python_executable": sys.executable,
        "packages": {p: _pkg_version(p) for p in _PACKAGES},
        "nvidia_smi": _nvidia_smi(),
    }
    try:
        import psutil

        info["ram_GB"] = round(psutil.virtual_memory().total / 2**30, 1)
    except Exception:
        pass
    try:
        import torch

        info["torch_cuda_build"] = torch.version.cuda
        info["torch_cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            info["torch_device"] = torch.cuda.get_device_name(0)
            info["torch_capability"] = list(torch.cuda.get_device_capability(0))
            info["torch_arch_list"] = torch.cuda.get_arch_list()
            info["cudnn"] = torch.backends.cudnn.version()
    except Exception as exc:
        info["torch_error"] = repr(exc)
    try:
        import pennylane as qml

        info["pennylane_devices"] = sorted(
            d for d in ("default.qubit", "default.mixed", "lightning.qubit", "lightning.gpu",
                        "lightning.kokkos", "default.qutrit")
            if _device_ok(qml, d)
        )
    except Exception as exc:
        info["pennylane_error"] = repr(exc)
    info["machine_profile"] = detect_machine(info)
    return info


def _device_ok(qml, name: str) -> bool:
    try:
        qml.device(name, wires=1)
        return True
    except Exception:
        return False


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_absolute():
        path = CONFIG_ROOT / path
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def detect_machine(info: dict | None = None) -> dict:
    """All experiments of this project run on a single local machine (no multi-machine setup);
    this only records which GPU (if any) the run actually saw."""
    gpus = (info or {}).get("nvidia_smi", {}).get("gpus") if info is not None else _nvidia_smi().get("gpus")
    gpus = gpus or []
    return {"machine": socket.gethostname(), "gpu": gpus[0]["name"] if gpus else None,
            "memory_MiB": gpus[0]["memory_MiB"] if gpus else None}


def _hash_config(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:10]


class Experiment:
    """Context manager:  with Experiment('algebra', 'phase2', cfg) as ex: ...; ex.save_json(...)"""

    def __init__(self, category: str, name: str, config: dict, seed: int | None = None):
        self.category, self.name = category, name
        self.config = dict(config)
        self.seed = seed if seed is not None else self.config.get("seed")
        self.config_hash = _hash_config(self.config)
        stamp = _dt.datetime.now(_dt.UTC).strftime("%Y%m%dT%H%M%SZ")
        host = socket.gethostname().replace("_", "-")
        self.exp_id = f"{name}-{stamp}-{host}-{self.config_hash}"
        self.dir = RESULTS_ROOT / category / self.exp_id
        self.status = "PASS"
        self.notes: list[str] = []

    def __enter__(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.t0 = time.perf_counter()
        self.started = _dt.datetime.now(_dt.UTC).isoformat()
        try:
            import psutil

            self._proc = psutil.Process()
        except Exception:
            self._proc = None
        self.env = environment_info()
        self.env["seed"] = self.seed
        self.env["experiment_id"] = self.exp_id
        self.env["config_hash"] = self.config_hash
        self.env["command"] = " ".join(sys.argv)
        self._write("config.json", self.config)
        self._write("env.json", self.env)
        return self

    def __exit__(self, exc_type, exc, tb):
        wall = time.perf_counter() - self.t0
        status = {
            "experiment_id": self.exp_id,
            "status": "ERROR" if exc_type else self.status,
            "started_utc": self.started,
            "finished_utc": _dt.datetime.now(_dt.UTC).isoformat(),
            "wall_time_s": wall,
            "notes": self.notes,
        }
        if self._proc is not None:
            mi = self._proc.memory_info()
            status["rss_MB_end"] = round(mi.rss / 2**20, 1)
            status["peak_wset_MB"] = round(getattr(mi, "peak_wset", 0) / 2**20, 1) or None
        try:
            import torch

            if torch.cuda.is_available() and torch.cuda.is_initialized():
                status["torch_cuda_max_allocated_MB"] = round(torch.cuda.max_memory_allocated() / 2**20, 1)
        except Exception:
            pass
        if exc_type:
            status["error"] = "".join(traceback.format_exception(exc_type, exc, tb))
        self._write("status.json", status)
        print(f"[{status['status']}] {self.exp_id}  ({wall:.2f} s)  -> {self.dir}")
        return False

    # ---------------------------------------------------------------- output
    def _write(self, fname: str, obj) -> Path:
        p = self.dir / fname
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, default=_json_default, ensure_ascii=False)
        return p

    def save_json(self, fname: str, obj) -> Path:
        return self._write(fname, obj)

    def save_csv(self, fname: str, rows: list[dict]) -> Path:
        import csv

        p = self.dir / fname
        if not rows:
            p.write_text("")
            return p
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow({k: _json_default(v) if not isinstance(v, (int, float, str, type(None))) else v
                            for k, v in r.items()})
        return p

    def fail(self, note: str):
        self.status = "FAIL"
        self.notes.append(note)

    def note(self, note: str):
        self.notes.append(note)


def _json_default(o):
    try:
        import numpy as np

        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
    except Exception:
        pass
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    if isinstance(o, Path):
        return str(o)
    return str(o)
