"""TempoExtractor AI エントリポイント

引数なし: GUIを起動
引数あり: CLIモード (--input, --out-mid, --out-csv 等)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tempo_extractor.analysis import AnalysisParams
from tempo_extractor.csv_export import save_csv
from tempo_extractor.midi_export import save_midi
from tempo_extractor.pipeline import filter_by_resolution, run_analysis
from tempo_extractor.postprocess import PostProcessParams, SmoothingLevel


def run_cli(args: argparse.Namespace) -> int:
    analysis_params = AnalysisParams(
        time_signature=args.time_signature,
        min_bpm=args.min_bpm,
        max_bpm=args.max_bpm,
    )
    postprocess_params = PostProcessParams(
        start_offset_sec=args.offset,
        remove_outliers=not args.no_outlier_filter,
        outlier_threshold=args.outlier_threshold / 100.0,
        smoothing=SmoothingLevel(args.smoothing),
    )

    result = run_analysis(
        Path(args.input),
        analysis_params,
        postprocess_params,
        on_progress=lambda msg: print(msg, file=sys.stderr),
    )
    records = filter_by_resolution(result.records, args.resolution)

    if args.out_mid:
        save_midi(records, Path(args.out_mid), analysis_params.time_signature)
        print(f"MIDI saved: {args.out_mid}")
    if args.out_csv:
        save_csv(records, Path(args.out_csv))
        print(f"CSV saved: {args.out_csv}")

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TempoExtractor AI")
    parser.add_argument("--input", "-i", help="入力音声ファイル (指定するとCLIモード)")
    parser.add_argument("--out-mid", help="出力MIDIファイルパス")
    parser.add_argument("--out-csv", help="出力CSVファイルパス")
    parser.add_argument("--time-signature", default="4/4", choices=["4/4", "3/4", "6/8"])
    parser.add_argument("--min-bpm", type=float, default=60.0)
    parser.add_argument("--max-bpm", type=float, default=180.0)
    parser.add_argument("--resolution", default="beat", choices=["bar", "beat"])
    parser.add_argument("--offset", type=float, default=0.0, help="開始オフセット(秒)")
    parser.add_argument("--no-outlier-filter", action="store_true")
    parser.add_argument("--outlier-threshold", type=float, default=25.0, help="%%")
    parser.add_argument(
        "--smoothing", default="Medium", choices=[lvl.value for lvl in SmoothingLevel]
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.input:
        sys.exit(run_cli(args))
    else:
        from tempo_extractor.gui import main as gui_main

        gui_main()


if __name__ == "__main__":
    main()
