#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT_DIR"

for instrument in EURUSD GBPUSD USDCHF XAGUSD; do
  out_dir="ML/reports/cross_instrument_robustness/generated/${instrument}"
  mkdir -p "$out_dir"

  ./.venv/bin/python -m ML.export_take_skip_v2_predictions \
    --input-csv "MT/MQL4/Files/Nero_${instrument}.csv" \
    --checkpoint ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt \
    --output "$out_dir/baseline_predictions.csv" \
    --mode original_contour \
    --feature-mode original_baseline \
    --seq-len 50 \
    --inference-only

  ./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
    --predictions "$out_dir/baseline_predictions.csv" \
    --rule-path ML/reports/take_skip_trailing_stop_v2_quality_selected_rule.json \
    --output "$out_dir/quality_signals.csv"

  ./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
    --predictions "$out_dir/baseline_predictions.csv" \
    --rule-path ML/reports/take_skip_trailing_stop_v2_frequency_selected_rule.json \
    --output "$out_dir/frequency_signals.csv"

  ./.venv/bin/python -m ML.export_take_skip_v2_predictions \
    --input-csv "MT/MQL4/Files/Nero_${instrument}.csv" \
    --checkpoint ML/reports/take_skip_original_contour_feature_matrix/original_plus_path_seq50/checkpoint.pt \
    --output "$out_dir/original_plus_path_predictions.csv" \
    --mode original_contour \
    --feature-mode original_plus_path \
    --seq-len 50 \
    --inference-only

  ./.venv/bin/python -m API.export_take_skip_trailing_stop_v2_signals \
    --predictions "$out_dir/original_plus_path_predictions.csv" \
    --rule-path ML/reports/take_skip_trailing_stop_v2_original_plus_path_selected_rule.json \
    --output "$out_dir/original_plus_path_signals.csv"
done
