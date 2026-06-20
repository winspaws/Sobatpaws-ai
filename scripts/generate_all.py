#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-shot orchestrator for the full Sobatpaws synthetic dataset.

Runs, in order:
  1. generate_dataset.py     (taxonomy + clinical matrix + symptoms/diagnosa)
  2. generate_operational.py (operational + ML + AI)
  3. validate_dataset.py     (FK / PK / unique / enum-domain checks)

Usage:
  python3 scripts/generate_all.py                    # ~500k baris (default)
  python3 scripts/generate_all.py --target-rows 1000000
  python3 scripts/generate_all.py --taxonomy large   # taksonomi besar (jutaan baris)
  python3 scripts/generate_all.py --scale 0.02       # sample 2%
  python3 scripts/generate_all.py --no-validate
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(script, *args):
    cmd = [PY, os.path.join(HERE, script), *args]
    print("\n>>> %s\n" % " ".join(cmd))
    t0 = time.time()
    rc = subprocess.call(cmd)
    print("\n<<< %s finished in %.1fs (exit %d)" % (script, time.time() - t0, rc))
    if rc != 0:
        sys.exit(rc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--target-rows", type=int, default=500000,
                    help="target total baris dataset (default 500000)")
    ap.add_argument("--taxonomy", choices=["default", "large"], default="default")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--with-views", action="store_true",
                    help="Jalankan build_ml_views.py setelah validate")
    ap.add_argument("--with-registry", action="store_true",
                    help="Refresh platform registry setelah selesai")
    args = ap.parse_args()
    scale = str(args.scale)
    target = str(args.target_rows)

    t0 = time.time()
    run("generate_dataset.py", "--scale", scale, "--taxonomy", args.taxonomy)
    run("generate_operational.py", "--scale", scale, "--target-rows", target)
    if not args.no_validate:
        run("validate_dataset.py")
    if args.with_views:
        run("build_ml_views.py")
    if args.with_registry:
        _refresh_registry()
    print("\n=== ALL STAGES DONE in %.1fs (scale=%s, target=%s) ==="
          % (time.time() - t0, scale, target))


def _refresh_registry():
    import subprocess
    env = os.environ.copy()
    root = os.path.normpath(os.path.join(HERE, ".."))
    env["PYTHONPATH"] = os.path.join(root, "src") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.call(
        [PY, "-m", "sobatpaws.platform.registry", "--refresh"],
        cwd=root, env=env,
    )


if __name__ == "__main__":
    main()
