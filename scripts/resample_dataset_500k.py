#!/usr/bin/env python3
"""Resample dataset kesehatan hewan hingga N baris (default 500k)."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "import" / "Dataset_Kesehatan_Hewan_Komprehensif.csv"
DEFAULT_OUTPUT = ROOT / "data" / "generated" / "Dataset_Kesehatan_Hewan_500K_Rows.csv"


def main() -> None:
    ap = argparse.ArgumentParser(description="Resample dataset kesehatan hewan ke N baris")
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--rows", type=int, default=500_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not args.input.exists():
        raise SystemExit(f"File tidak ditemukan: {args.input}")

    df_awal = pd.read_csv(args.input)
    print(f"Loaded {len(df_awal):,} baris dari {args.input.name}")

    df_out = df_awal.sample(n=args.rows, replace=True, random_state=args.seed).reset_index(drop=True)
    df_out["ID_Kasus"] = [f"VET-{200_000 + i}" for i in range(args.rows)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output, index=False)

    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(f"Sukses: {len(df_out):,} baris → {args.output} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
