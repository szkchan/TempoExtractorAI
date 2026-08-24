"""解析パイプライン全体のオーケストレーション"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import audio_io
from .analysis import AnalysisParams, analyze
from .postprocess import BeatRecord, PostProcessParams, process

ProgressCallback = Callable[[str], None]


@dataclass
class TempoMapResult:
    records: list[BeatRecord]
    time_signature: str

    @property
    def bar_count(self) -> int:
        return self.records[-1].bar if self.records else 0


def run_analysis(
    input_path: Path,
    analysis_params: AnalysisParams,
    postprocess_params: PostProcessParams,
    on_progress: ProgressCallback | None = None,
) -> TempoMapResult:
    def report(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    report("音声をデコード中...")
    wav_path = audio_io.decode_to_wav(Path(input_path))
    try:
        report("madmomでビート/小節頭を解析中...")
        detections = analyze(wav_path, analysis_params)
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass

    report("ポストプロセッシング中...")
    records = process(detections, postprocess_params)

    report(f"解析完了。{records[-1].bar if records else 0} 小節を検出しました。")
    return TempoMapResult(records=records, time_signature=analysis_params.time_signature)


def filter_by_resolution(records: list[BeatRecord], mode: str) -> list[BeatRecord]:
    """resolution mode: 'bar' -> 小節頭(Beat_Number=1)のみ, 'beat' -> 全拍"""
    if mode == "bar":
        return [r for r in records if r.beat == 1]
    return records
