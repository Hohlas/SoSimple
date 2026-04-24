#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def run_command(args: list[str]) -> None:
    print({"cmd": args})
    subprocess.run(args, cwd=REPO_ROOT, check=True)


def write_manifest(*, instrument: str, provider: str, ohlc_path: str, generated_dir: Path) -> Path:
    manifest_path = generated_dir / f"{instrument.lower()}_transfer_manifest.json"
    payload = {
        "datasets": [
            {
                "dataset_name": f"{instrument.lower()}_{provider.lower()}_transfer_test_labeled",
                "instrument": instrument,
                "provider": provider,
                "kind": "cross_instrument_transfer",
                "ohlc_path": ohlc_path,
                "signals": [
                    {
                        "system_name": "quality",
                        "signal_csv": str(generated_dir / "quality_test_signals.csv"),
                        "policy_name": "trail_x8_tp12",
                    },
                    {
                        "system_name": "frequency",
                        "signal_csv": str(generated_dir / "frequency_test_signals.csv"),
                        "policy_name": "trail_x8",
                    },
                    {
                        "system_name": "original_plus_path",
                        "signal_csv": str(generated_dir / "original_plus_path_test_signals.csv"),
                        "policy_name": "trail_x8",
                    },
                ],
            }
        ]
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen transfer pipeline for one instrument using *_test_labeled.csv.")
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--provider", default="Alpari")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--ohlc-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--benchmark-output-dir", required=True)
    args = parser.parse_args()

    generated_dir = (REPO_ROOT / args.output_dir).resolve()
    generated_dir.mkdir(parents=True, exist_ok=True)

    baseline_predictions = generated_dir / "baseline_test_predictions.csv"
    original_predictions = generated_dir / "original_plus_path_test_predictions.csv"

    run_command(
        [
            sys.executable,
            "-m",
            "ML.export_take_skip_v2_predictions",
            "--input-csv",
            args.input_csv,
            "--checkpoint",
            "ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt",
            "--output",
            str(baseline_predictions),
            "--mode",
            "original_contour",
            "--feature-mode",
            "original_baseline",
            "--seq-len",
            "50",
            "--batch-size",
            "2048",
        ]
    )
    run_command(
        [
            sys.executable,
            "-m",
            "ML.export_take_skip_v2_predictions",
            "--input-csv",
            args.input_csv,
            "--checkpoint",
            "ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/checkpoint.pt",
            "--output",
            str(original_predictions),
            "--mode",
            "original_contour",
            "--feature-mode",
            "original_plus_path",
            "--seq-len",
            "50",
            "--batch-size",
            "2048",
        ]
    )
    for rule_name, source, output_name in [
        ("ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json", baseline_predictions, "quality_test_signals.csv"),
        ("ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json", baseline_predictions, "frequency_test_signals.csv"),
        ("ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json", original_predictions, "original_plus_path_test_signals.csv"),
    ]:
        run_command(
            [
                sys.executable,
                "-m",
                "API.export_take_skip_trailing_stop_v2_signals",
                "--predictions",
                str(source),
                "--rule-path",
                rule_name,
                "--output",
                str(generated_dir / output_name),
            ]
        )

    manifest_path = write_manifest(
        instrument=args.instrument,
        provider=args.provider,
        ohlc_path=args.ohlc_path,
        generated_dir=generated_dir,
    )
    run_command(
        [
            sys.executable,
            "-m",
            "ML.benchmark_cross_instrument_robustness",
            "--manifest",
            str(manifest_path),
            "--baseline-reference",
            "ML/reports/cross_instrument_robustness/metaquotes_baseline_reference.json",
            "--output-dir",
            args.benchmark_output_dir,
        ]
    )


if __name__ == "__main__":
    main()
