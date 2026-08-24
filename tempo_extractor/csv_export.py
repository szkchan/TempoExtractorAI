"""解析レポート(.csv)出力"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .postprocess import BeatRecord


def save_csv(records: list[BeatRecord], out_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "Bar_Number": r.bar,
                "Beat_Number": r.beat,
                "Timestamp_Sec": r.timestamp_sec,
                "Raw_BPM": r.raw_bpm,
                "Smoothed_BPM": r.smoothed_bpm,
            }
            for r in records
        ]
    )
    df.to_csv(out_path, index=False)
