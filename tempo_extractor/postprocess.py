"""ポストプロセッシング: オフセット補正 / スパイク除去 / 移動平均スムージング"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from .analysis import BeatDetection

SMOOTHING_WINDOW = {
    "Off": 1,
    "Low": 3,
    "Medium": 5,
    "High": 7,
}


class SmoothingLevel(str, Enum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass
class PostProcessParams:
    start_offset_sec: float = 0.0
    remove_outliers: bool = True
    outlier_threshold: float = 0.25  # ±25%
    smoothing: SmoothingLevel = SmoothingLevel.MEDIUM


@dataclass
class BeatRecord:
    bar: int
    beat: int
    timestamp_sec: float
    raw_bpm: float
    smoothed_bpm: float


def _raw_bpm_series(timestamps: np.ndarray) -> np.ndarray:
    """隣接拍間隔から瞬間BPMを算出する。先頭要素は直後の間隔を流用。"""
    n = len(timestamps)
    bpm = np.zeros(n)
    if n < 2:
        bpm[:] = 0.0
        return bpm
    intervals = np.diff(timestamps)
    intervals = np.where(intervals <= 0, np.nan, intervals)
    bpm[1:] = 60.0 / intervals
    bpm[0] = bpm[1]
    return bpm


def _remove_outlier_spikes(bpm: np.ndarray, threshold: float) -> np.ndarray:
    """前後の平均BPMからthreshold以上外れた値を線形補間で補正する。"""
    n = len(bpm)
    if n < 3:
        return bpm.copy()

    cleaned = bpm.copy()
    valid = np.ones(n, dtype=bool)

    for i in range(1, n - 1):
        neighbor_avg = (bpm[i - 1] + bpm[i + 1]) / 2.0
        if neighbor_avg <= 0:
            continue
        deviation = abs(bpm[i] - neighbor_avg) / neighbor_avg
        if deviation > threshold:
            valid[i] = False

    if np.all(valid):
        return cleaned

    idx = np.arange(n)
    cleaned[~valid] = np.interp(idx[~valid], idx[valid], cleaned[valid])
    return cleaned


def _smooth(bpm: np.ndarray, window: int) -> np.ndarray:
    """移動平均によるスムージング (window=1 は無処理)。"""
    if window <= 1 or len(bpm) < 2:
        return bpm.copy()

    kernel = np.ones(window) / window
    padded = np.pad(bpm, (window // 2, window - 1 - window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def process(
    detections: list[BeatDetection], params: PostProcessParams
) -> list[BeatRecord]:
    if not detections:
        return []

    timestamps = np.array([d.timestamp for d in detections]) + params.start_offset_sec
    raw_bpm = _raw_bpm_series(timestamps)

    filtered_bpm = raw_bpm
    if params.remove_outliers:
        filtered_bpm = _remove_outlier_spikes(filtered_bpm, params.outlier_threshold)

    window = SMOOTHING_WINDOW.get(params.smoothing.value, 1)
    smoothed_bpm = _smooth(filtered_bpm, window)

    records: list[BeatRecord] = []
    bar = 0
    for i, det in enumerate(detections):
        if det.is_downbeat or i == 0:
            bar += 1
        records.append(
            BeatRecord(
                bar=bar,
                beat=det.beat_number,
                timestamp_sec=round(float(timestamps[i]), 3),
                raw_bpm=round(float(raw_bpm[i]), 2),
                smoothed_bpm=round(float(smoothed_bpm[i]), 2),
            )
        )
    return records
