#!/usr/bin/env python3
from __future__ import annotations

import datetime
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


def _env_with_pythonpath(root: Path) -> Dict[str, str]:
    env = dict(os.environ)
    # Assure que la racine du repo et dd_coherence_tool sont importables
    pp_parts: List[str] = []
    pp_parts.append(str(root))
    pp_parts.append(str(root / "dd_coherence_tool"))
    existing = env.get("PYTHONPATH", "")
    if existing:
        pp_parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run(cmd: List[str], *, cwd: Path, log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = _env_with_pythonpath(cwd)
    with log_path.open("w", encoding="utf-8") as f:
        f.write("+ " + " ".join(cmd) + "\n")
        f.flush()
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
        return p.wait()


def tail_text(path: Path, n_lines: int = 120) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return f"(impossible de lire {path}: {e})"
    if len(lines) <= n_lines:
        return "\n".join(lines)
    return "\n".join(lines[-n_lines:])


def fail_with_log(rc: int, log_path: Path, label: str) -> int:
    print(f"[band_suite] {label} a echoue (rc={rc}). Log: {log_path}")
    print(f"[band_suite] Dernieres lignes de {log_path}:")
    print(tail_text(log_path, 160))
    return rc


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    ci_out = root / "_ci_out"
    ci_out.mkdir(parents=True, exist_ok=True)

    meta = {
        "utc": datetime.datetime.utcnow().isoformat() + "Z",
        "pwd": str(root),
        "python": subprocess.check_output(["python", "-V"], text=True).strip(),
        "pip": subprocess.check_output(["pip", "-V"], text=True).strip(),
        "py_path": os.environ.get("PYTHONPATH", ""),
    }
    (ci_out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # 0) Sanity check: fichiers attendus
    (ci_out / "sanity.txt").write_text(
        "\n".join([
            f"root={root}",
            f"has_dd_tool={(root / 'dd_coherence_tool').exists()}",
            f"has_run_dd={(root / 'dd_coherence_tool' / 'scripts' / 'run_dd.py').exists()}",
            f"has_tests={(root / 'dd_coherence_tool' / 'tests').exists()}",
        ]) + "\n",
        encoding="utf-8"
    )

    # 1) Tests DD si présents
    dd_tests = root / "dd_coherence_tool" / "tests"
    if dd_tests.exists():
        log = ci_out / "pytest_dd.log"
        rc = run(["python", "-m", "pytest", "-q", str(dd_tests)], cwd=root, log_path=log)
        if rc != 0:
            return fail_with_log(rc, log, "pytest")

    # 2) Smoke DD (avec composants)
    sample_csv = ci_out / "sample.csv"
    make_log = ci_out / "make_sample.log"
    rc = run([
        "python", "-c",
        (
            "import numpy as np, pandas as pd; "
            "np.random.seed(0); "
            "x=np.r_[np.random.normal(0,1,200),np.random.normal(3,1.5,200)]; "
            "y=np.r_[np.random.normal(0,1,200),np.random.normal(0,1,200)]; "
            "pd.DataFrame({'x':x,'y':y}).to_csv(r'%s', index=False)"
        ) % str(sample_csv)
    ], cwd=root, log_path=make_log)
    if rc != 0:
        return fail_with_log(rc, make_log, "make_sample")

    run_dd = root / "dd_coherence_tool" / "scripts" / "run_dd.py"
    if run_dd.exists():
        out_dd = ci_out / "out_dd"
        out_dd.mkdir(parents=True, exist_ok=True)
        smoke_log = ci_out / "run_dd_smoke.log"
        rc = run([
            "python", str(run_dd),
            "--input", str(sample_csv),
            "--outdir", str(out_dd),
            "--cols", "x,y"
        ], cwd=root, log_path=smoke_log)
        if rc != 0:
            return fail_with_log(rc, smoke_log, "run_dd_smoke")
    else:
        (ci_out / "run_dd_missing.txt").write_text("dd_coherence_tool/scripts/run_dd.py introuvable\n", encoding="utf-8")

    # 3) Batch sur CSV commités (optionnel)
    run_batch = root / "dd_coherence_tool" / "scripts" / "run_dd_batch.py"
    params_small = root / "dd_params.small.json"
    if run_batch.exists() and params_small.exists():
        csvs = sorted([
            p for p in (root / "dd_coherence_tool").glob("*.csv")
            if not p.name.endswith("_uuid.csv") and not p.name.endswith("_orig.csv")
        ])
        if csvs:
            batch_log = ci_out / "run_dd_batch.log"
            cmd = ["python", str(run_batch), "--outdir", str(ci_out / "dd_runs"), "--config", str(params_small)] + [str(p) for p in csvs]
            rc = run(cmd, cwd=root, log_path=batch_log)
            if rc != 0:
                return fail_with_log(rc, batch_log, "run_dd_batch")

    print("[band_suite] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
