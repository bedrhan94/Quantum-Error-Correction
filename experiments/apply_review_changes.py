"""Apply reports/degisiklikler.py to reports/teknik_rapor.template.md (idempotent, fails loudly).

    .venv/Scripts/python.exe experiments/apply_review_changes.py
Writes reports/degisiklikler.json (the change log rendered as Ek C by make_report.py).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "reports" / "teknik_rapor.template.md"


def load_changes():
    spec = importlib.util.spec_from_file_location("degisiklikler", ROOT / "reports" / "degisiklikler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CHANGES


def main():
    files = {}

    def get(path):
        if path not in files:
            files[path] = (ROOT / path).read_text(encoding="utf-8")
        return files[path]

    log = []
    changes = load_changes()
    fpath = lambda c: c.get("file", "reports/teknik_rapor.template.md")
    for i, c in enumerate(changes):
        path = fpath(c)
        tpl = get(path)
        # a later entry may revise part of this entry's NEW text (chains such as C05 -> C24); on a re-run the
        # file then holds the revised text, so compare against the effective final text as well
        final, revised_by = c["yeni"], []
        for d in changes[i + 1:]:
            if fpath(d) == path and d["eski"] and d["eski"] in final:
                final = final.replace(d["eski"], d["yeni"])
                revised_by.append(d["id"])
        if revised_by:
            c = {**c, "revised_by": revised_by}
        if c["eski"]:
            n_old = tpl.count(c["eski"])
            if c["yeni"] in tpl:  # checked first: NEW may contain OLD as a prefix
                state = "already applied"
            elif revised_by and final in tpl:
                state = f"already applied (later revised by {', '.join(revised_by)})"
            elif n_old == 1:
                tpl = tpl.replace(c["eski"], c["yeni"])
                state = "applied"
            else:
                raise SystemExit(f"{c['id']}: old text found {n_old} times - template and change log disagree")
        else:
            if c["yeni"].strip() in tpl:
                state = "already applied"
            elif revised_by and final.strip() in tpl:
                state = f"already applied (later revised by {', '.join(revised_by)})"
            else:
                anchor = c["after"]
                k = tpl.find(anchor)
                if k < 0 or tpl.count(anchor) != 1:
                    raise SystemExit(f"{c['id']}: anchor not unique/not found")
                end = k + len(anchor)
                if c.get("after_line"):
                    end = tpl.index("\n", end)
                tpl = tpl[:end] + ("\n" if c.get("after_line") else "") + c["yeni"] + tpl[end:]
                state = "inserted"
        files[path] = tpl  # store the edited text of THIS file
        log.append({**c, "file": path, "state": state})
        print(c["id"], path, state)
    key = "reports/teknik_rapor.template.md"
    t = get(key)
    if "EK_C" not in t:
        files[key] = t.rstrip() + "\n\n## Ek C — İnceleme sonrası değişen ifadeler (eski → yeni)\n\nEK_C\n"
    # sanity: every file must still start with its own title (guards against cross-file writes)
    heads = {"reports/teknik_rapor.template.md": "# ε-Kuantum Hata Düzeltme Kodları",
             "CALISMA_OZETI.md": "# Çalışma Özeti", "experiments/make_report.py": '"""Fill reports/teknik_rapor'}
    for path, text in files.items():
        if path in heads and not text.startswith(heads[path]):
            raise SystemExit(f"refusing to write {path}: unexpected content")
        (ROOT / path).write_text(text, encoding="utf-8")
    (ROOT / "reports" / "degisiklikler.json").write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
