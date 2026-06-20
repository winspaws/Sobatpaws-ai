"""Pipeline runner — orkestrator langkah data/ML dengan output JSON untuk agent."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

from ..config import PROJECT_ROOT
from .manifest import PIPELINE_PRESETS, get_preset, get_step


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(PROJECT_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return env


def run_step(step_id: str, *, extra_args: list[str] | None = None) -> dict[str, Any]:
    """Jalankan satu langkah pipeline; kembalikan hasil terstruktur."""
    step = get_step(step_id)
    if not step:
        return {"step_id": step_id, "status": "unknown", "error": "step not found"}

    cmd = list(step["command"])
    if extra_args:
        cmd.extend(extra_args)

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=_env(),
            capture_output=True,
            text=True,
        )
        elapsed = round(time.perf_counter() - t0, 2)
        result: dict[str, Any] = {
            "step_id": step_id,
            "track": step.get("track"),
            "description": step.get("description"),
            "command": cmd,
            "status": "success" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "elapsed_sec": elapsed,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-1000:],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        if proc.returncode == 0 and step_id in ("train_ml", "retrain_ml", "refresh_registry"):
            try:
                from .registry import refresh_registry

                result["registry"] = {"models": len(refresh_registry().get("models", []))}
            except Exception:  # noqa: BLE001
                pass
        return result
    except Exception as exc:  # noqa: BLE001
        return {
            "step_id": step_id,
            "status": "error",
            "error": str(exc),
            "elapsed_sec": round(time.perf_counter() - t0, 2),
        }


def run_preset(preset: str, *, stop_on_error: bool = True) -> dict[str, Any]:
    """Jalankan preset pipeline (urutan step)."""
    steps = get_preset(preset)
    if not steps:
        return {"preset": preset, "status": "unknown", "error": "preset not found"}

    results: list[dict] = []
    overall = "success"
    for sid in steps:
        r = run_step(sid)
        results.append(r)
        if r.get("status") != "success":
            overall = "failed"
            if stop_on_error:
                break

    return {
        "preset": preset,
        "status": overall,
        "steps_run": len(results),
        "results": results,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


def run_steps(step_ids: list[str], *, stop_on_error: bool = True) -> dict[str, Any]:
    results = []
    overall = "success"
    for sid in step_ids:
        r = run_step(sid)
        results.append(r)
        if r.get("status") != "success":
            overall = "failed"
            if stop_on_error:
                break
    return {
        "status": overall,
        "steps_run": len(results),
        "results": results,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Sobatpaws pipeline runner")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--step", action="append", default=[])
    ap.add_argument("--preset", default=None)
    ap.add_argument("--continue-on-error", action="store_true")
    args = ap.parse_args()

    if args.list:
        print(json.dumps({
            "steps": [{"id": s["id"], "track": s["track"], "description": s["description"]}
                      for s in __import__("sobatpaws.platform.manifest", fromlist=["PIPELINE_STEPS"]).PIPELINE_STEPS],
            "presets": PIPELINE_PRESETS,
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.preset:
        out = run_preset(args.preset, stop_on_error=not args.continue_on_error)
    elif args.step:
        out = run_steps(args.step, stop_on_error=not args.continue_on_error)
    else:
        ap.print_help()
        sys.exit(1)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("status") == "success" else 1)
