"""Draw the PennyLane circuits used in Phase 5 (Z_25[i] code, 10 data qubits) + a block diagram.

    .venv/Scripts/python.exe experiments/draw_circuits.py
Writes figures/circuits/*.png.  Every circuit is built with the SAME RingCircuits methods that were
simulated in Phase 5 (no separate drawing-only code), with wires renamed for readability:
  re0..re4  = real part a of x = a + bi (re0 = most significant bit)
  im0..im4  = imaginary part b
  sZ0..     = Z-type syndrome ancilla (value mod 5)
  sX0..sX4  = X-type syndrome ancilla (phase estimation, Z_25 Fourier register)
  w0, w1    = work qubits of qml.Adder (return to |0>)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pennylane as qml  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from epsqec.css.build import build  # noqa: E402
from epsqec.pl_circuits import RingCircuits  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "circuits"
STYLE = "black_white"


def names(rc: RingCircuits) -> dict:
    L = rc.L
    m = {}
    for i, w in enumerate(L.re):
        m[w] = f"re{i}"
    for i, w in enumerate(L.im):
        m[w] = f"im{i}"
    for reg in L.z_anc:
        for i, w in enumerate(reg):
            m[w] = f"sZ{i}"
    for reg in L.x_anc:
        for i, w in enumerate(reg):
            m[w] = f"sX{i}"
    m[L.work[0]], m[L.work[1]] = "w0", "w1"
    return m


def name_map(rc):
    return rc.names if hasattr(rc, "names") else names(rc)


def make_tape(rc, body, measure=None, expansion=0):
    """Record the ops of `body` (no QNode, so no artificial measurement); optionally decompose."""
    with qml.queuing.AnnotatedQueue() as q:
        body()
    nm = name_map(rc)
    meas = [qml.probs(wires=[w for w, n in nm.items() if n in measure])] if measure else []
    tape = qml.tape.QuantumScript.from_queue(q, )
    tape = qml.tape.QuantumScript(tape.operations, meas)
    if expansion:
        [tape], _ = qml.transforms.decompose(tape, max_expansion=expansion)
    [tape], _ = qml.map_wires(tape, nm)
    return tape


def save(fig, fname, title):
    fig.suptitle(title, fontsize=13, y=0.995)
    fig.savefig(OUT / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / fname)


def draw(rc, body, fname: str, title: str, measure=None, expansion=0, first=(), only=None):
    tape = make_tape(rc, body, measure, expansion)
    nm = name_map(rc)
    order = [nm[w] for w in sorted(nm)]
    order = [w for w in first] + [w for w in order if w not in first]  # e.g. control ancillas on top
    if only:
        order = [w for w in order if w in only]
    fig, ax = qml.drawer.tape_mpl(tape, style=STYLE, wire_order=order, show_all_wires=True, decimals=None)
    save(fig, fname, title)


def draw_rows(rc, body, fname: str, title: str, expansion: int, only, per_row: int):
    """Long gate-level circuits: split the op list into rows and stack the images vertically."""
    tape = make_tape(rc, body, None, expansion)
    ops = tape.operations
    parts = []
    for k in range(0, len(ops), per_row):
        t = qml.tape.QuantumScript(ops[k:k + per_row])
        fig, ax = qml.drawer.tape_mpl(t, style=STYLE, wire_order=only, show_all_wires=True, decimals=None)
        p = OUT / f"_part{k}.png"
        fig.savefig(p, dpi=130, bbox_inches="tight")
        plt.close(fig)
        parts.append(p)
    from PIL import Image as PI

    ims = [PI.open(p).convert("RGB") for p in parts]
    W = max(i.width for i in ims)
    H = sum(i.height for i in ims) + 40 * (len(ims) - 1)
    canvas = PI.new("RGB", (W, H), "white")
    y = 0
    for im in ims:
        canvas.paste(im, (0, y))
        y += im.height + 40
    fig = plt.figure(figsize=(W / 130, H / 130 + 0.5))
    plt.imshow(canvas)
    plt.axis("off")
    save(fig, fname, title + f"  ({len(ops)} kapı, {len(parts)} satır)")
    for p in parts:
        p.unlink()


def block_diagram():
    """Schematic of one QEC cycle as run in Phase 5 (alternative design, Z_25[i])."""
    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    rows = {"data": 3.2, "sZ": 1.9, "sX": 0.9}
    labels = {"data": "veri: re0..re4, im0..im4\n(x = a + bi, 10 kubit)", "sZ": "Z-sendrom\nancilla (mod 5)",
              "sX": "X-sendrom\nancilla (Z_25 Fourier)"}
    for k, y in rows.items():
        ax.plot([1.9, 12.6], [y, y], color="#333", lw=1.4, zorder=0)
        ax.text(1.8, y, labels[k], ha="right", va="center", fontsize=9)

    def box(x, y0, y1, w, text, fc):
        ax.add_patch(FancyBboxPatch((x, y0), w, y1 - y0, boxstyle="round,pad=0.03", fc=fc, ec="#222", lw=1.2))
        ax.text(x + w / 2, (y0 + y1) / 2, text, ha="center", va="center", fontsize=8.5)

    box(2.1, 2.85, 3.55, 1.2, "Kodlama\n|ψ⟩_L\n(StatePrep)", "#e8eef9")
    box(3.6, 2.85, 3.55, 1.1, "Hata\nX(a) Z(b)", "#fde2d8")
    box(5.0, 1.6, 3.55, 1.5, "Z-sendromu\nTr⟨v,x⟩ → sZ\n(kontrollü Adder)", "#e3f4ec")
    box(6.7, 0.6, 3.55, 1.9, "X-sendromu\n(faz kestirimi)\n\nDFT_25\nkontrollü X(2^k u)\nDFT_25", "#e3f4ec")
    box(8.85, 1.6, 2.2, 0.6, "ölç", "#f2f2f2")
    box(8.85, 0.6, 1.2, 0.6, "ölç", "#f2f2f2")
    box(9.75, 0.6, 2.2, 1.3, "klasik\ndecoder\n(LUT)", "#fff4cc")
    box(11.0, 2.85, 3.55, 1.4, "Kurtarma\nX(−â) Z(−b̂)", "#e8eef9")
    ax.annotate("", xy=(11.3, 2.85), xytext=(11.3, 2.25), arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(6.5, 4.05, "Bir QEC turu (Phase 5, alternatif tasarım; Z_25[i], 20 kubit) — makalenin ε-hataları X(e), e∈C2 "
                       "bu turda sıfır sendrom verir ve düzeltilemez", ha="center", fontsize=9.5)
    fig.savefig(OUT / "qec_cycle_block.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", OUT / "qec_cycle_block.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    b = build({"key": "Z25"})
    code = b.code
    zg = np.asarray(code.zgens[0]).reshape(2)
    xg = np.asarray(code.xgens[0]).reshape(2)
    V = code.logical_states(b.eps)
    rng = np.random.default_rng(1)
    c = rng.normal(size=5) + 1j * rng.normal(size=5)
    psi = (c / np.linalg.norm(c)) @ V

    # 1) X(u) and its first-level decomposition
    rc = RingCircuits(25)
    draw(rc, lambda: rc.X((3, 4)), "gate_X_3p4i.png",
         "X(3+4i): |a⟩|b⟩ → |a+3 mod 25⟩|b+4 mod 25⟩  (iki qml.Adder, mod 25)")
    reg = ["re0", "re1", "re2", "re3", "re4", "w0", "w1"]
    draw(rc, lambda: rc.X((3, 0)), "gate_X_adder_decomposed.png",
         "qml.Adder(3, mod 25) açılımı (2. seviye): QFT → PhaseAdder(3, mod 25) → QFT†",
         expansion=2, only=reg)
    draw_rows(rc, lambda: rc.X((3, 0)), "gate_X_adder_gatelevel.png",
              "qml.Adder(3, mod 25), 4 seviye açılmış (bazı QFT/QFT† alt blokları kutu olarak kaldı; "
              "tam açılım: 178 kapı = 96 kontrollü faz, 36 H, 24 faz, 18 SWAP, 2 CNOT, 2 X)",
              expansion=4, only=reg, per_row=24)
    # 2) Z(v) = single-qubit phases
    draw(rc, lambda: rc.Z((10, 5)), "gate_Z_10p5i.png",
         "Z(10+5i): faz χ(⟨v,x⟩_H) = exp(2πi[(c+d)a + (d−c)b]/25) → her veri kubitine bir PhaseShift")
    # 3) Z-type syndrome extraction
    rcz = RingCircuits(25, zgens=code.zgens)
    draw(rcz, lambda: rcz.z_syndrome(0), "syndrome_Z.png",
         f"Z-tipi sendrom: s = Tr⟨v,x⟩ / 5 mod 5, v = {b.ring.fmt(zg)} — her veri biti ancilla'ya kontrollü Adder ekler",
         measure=[f"sZ{i}" for i in range(3)])
    # 4) X-type syndrome extraction (phase estimation)
    rcx = RingCircuits(25, xgens=code.xgens)
    draw(rcx, lambda: rcx.x_syndrome(0), "syndrome_X.png",
         f"X-tipi sendrom (faz kestirimi), u = {b.ring.fmt(xg)}: U = DFT_25 (32×32, yalnız ancilla) · "
         f"sX_k kontrollü X(2^k u) · DFT_25",
         measure=[f"sX{i}" for i in range(5)], first=[f"sX{i}" for i in range(5)])
    # 5) Proposition 5 counter-example circuit
    init = np.zeros(2 ** rcz.L.n_wires, dtype=complex)
    init.reshape(2 ** 10, -1)[:, 0] = rcz.embed_ring_state(psi)

    def prop5():
        qml.StatePrep(init, wires=range(rcz.L.n_wires))
        rcz.X((2, 1))
        rcz.z_syndrome(0)

    draw(rcz, prop5, "prop5_counterexample.png",
         "Önerme 5 karşı-örneği: |ψ⟩_L → X(2+i) (ε'nin bir elemanı) → Z-sendromu. Ölçüm olasılık 1 ile 000 verir, "
         "ama veri X(2+i)|ψ⟩_L ≠ |ψ⟩_L", measure=[f"sZ{i}" for i in range(3)])
    block_diagram()
    split_drawings()


class _SplitNames:
    """Wire names for a SplitCircuits instance (digits, logical, ancilla pool)."""

    def __init__(self, sc):
        self.sc = sc
        nm = {}
        for d in sc.L.digits:
            for t, w in enumerate(d.wires):
                nm[w] = f"{d.name}.{t}"
        for d in sc.logical:
            for t, w in enumerate(d.wires):
                nm[w] = f"L.{t}"
        for t, w in enumerate(sc.anc_wires):
            nm[w] = f"anc{t}"
        self.names = nm


def split_drawings():
    from epsqec.pl_circuits.split_layout import SplitCircuits

    b = build({"key": "Z25"})
    sc = SplitCircuits(b, reuse_ancilla=True)
    rcn = _SplitNames(sc)
    roles = ", ".join(f"{d.name}={r}" for d, r in zip(sc.L.digits, sc.roles))
    draw(rcn, sc.encode, "splitB_encoder.png",
         f"Düzen B kodlayıcı (Z25, C1=<3+4i>, C2=<2+i>): serbest rakamlar DFT_5, etiket rakamı L'den taşıma, ölü rakam boş  [{roles}]",
         first=[n for n in rcn.names.values() if n.startswith("L.")])
    draw(rcn, lambda: sc.X((1, 0)), "splitB_X.png",
         "Düzen B: X(1) = U ve V bileşenlerine 1 ekleme (taban-5 rakamlar, taşıma = kontrollü kaydırma)")
    zP = [P for P in sc.parts if P.kind == "Z"][0]
    xP = [P for P in sc.parts if P.kind == "X"][0]
    draw(rcn, lambda: sc.z_syndrome(zP), "splitB_syndrome_Z.png",
         f"Düzen B: Z-tipi sendrom (v = {b.ring.fmt(zP.generator)}, değer mod 5): her veri kubiti ancilla rakamına kontrollü kaydırma ekler",
         first=[n for n in rcn.names.values() if n.startswith("anc")])
    anc = [n for n in rcn.names.values() if n.startswith("anc")]
    draw_rows(rcn, lambda: sc.x_syndrome(xP), "splitB_syndrome_X.png",
              f"Düzen B: X-tipi sendrom (u = {b.ring.fmt(xP.generator)}, mertebe 25 = 5²): rakam başına DFT_5, kontrollü X(c·5^pos·u), "
              "taban-5 Fourier (DFT_5, ikiz faz, DFT_5)",
              expansion=0, only=anc + [rcn.names[w] for w in sc.data_wires], per_row=22)


if __name__ == "__main__":
    main()
