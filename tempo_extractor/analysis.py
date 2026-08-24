"""madmom RNN+DBN による拍/小節頭検出"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# 拍子 -> 1小節あたりの拍数 (DBNDownBeatTrackingProcessor の beats_per_bar 引数)
TIME_SIGNATURE_BEATS_PER_BAR = {
    "4/4": 4,
    "3/4": 3,
    "6/8": 6,
}


@dataclass
class BeatDetection:
    timestamp: float
    beat_number: int  # 小節内の拍位置 (1 = 小節頭/downbeat)

    @property
    def is_downbeat(self) -> bool:
        return self.beat_number == 1


@dataclass
class AnalysisParams:
    time_signature: str = "4/4"
    min_bpm: float = 60.0
    max_bpm: float = 180.0


def analyze(wav_path: Path, params: AnalysisParams) -> list[BeatDetection]:
    """音声を解析し、拍タイムスタンプと小節頭フラグの時系列を返す。"""
    from madmom.features.downbeats import (
        DBNDownBeatTrackingProcessor,
        RNNDownBeatProcessor,
    )

    beats_per_bar = TIME_SIGNATURE_BEATS_PER_BAR.get(params.time_signature, 4)

    rnn_proc = RNNDownBeatProcessor()
    activations = rnn_proc(str(wav_path))

    dbn_proc = DBNDownBeatTrackingProcessor(
        beats_per_bar=[beats_per_bar],
        min_bpm=params.min_bpm,
        max_bpm=params.max_bpm,
        fps=100,
    )
    result = dbn_proc(activations)  # shape (N, 2): [timestamp, beat_number]

    detections: list[BeatDetection] = []
    for timestamp, beat_number in result:
        detections.append(
            BeatDetection(
                timestamp=float(timestamp),
                beat_number=int(round(beat_number)),
            )
        )
    return detections
