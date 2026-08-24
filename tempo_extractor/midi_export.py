"""MIDIテンポマップ出力 (SMF, 480 TPQN, 0xFF 0x51 テンポメタイベント)"""
from __future__ import annotations

from pathlib import Path

import mido

from .postprocess import BeatRecord

TICKS_PER_BEAT = 480

TIME_SIGNATURE_NUMERATOR_DENOMINATOR = {
    "4/4": (4, 4),
    "3/4": (3, 4),
    "6/8": (6, 8),
}


def save_midi(
    records: list[BeatRecord],
    out_path: Path,
    time_signature: str = "4/4",
    smf_format: int = 0,
) -> None:
    if not records:
        raise ValueError("出力対象のテンポデータがありません")

    midi_file = mido.MidiFile(type=smf_format, ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    numerator, denominator = TIME_SIGNATURE_NUMERATOR_DENOMINATOR.get(
        time_signature, (4, 4)
    )
    track.append(
        mido.MetaMessage(
            "time_signature",
            numerator=numerator,
            denominator=denominator,
            time=0,
        )
    )

    # (time_sec, bpm) の並び。先頭は無音区間/アウフタクト分を最初の検出BPMで補う。
    points = [(0.0, records[0].smoothed_bpm)]
    for rec in records:
        points.append((rec.timestamp_sec, rec.smoothed_bpm))

    prev_time_sec, prev_bpm = points[0]
    total_ticks = 0.0
    prev_ticks_written = 0

    for time_sec, bpm in points:
        bpm = max(bpm, 1e-6)
        delta_sec = time_sec - prev_time_sec
        # 区間中は「直前のBPM」が有効だったとみなしてtick換算する
        total_ticks += delta_sec * (TICKS_PER_BEAT * max(prev_bpm, 1e-6) / 60.0)

        delta_ticks = max(int(round(total_ticks)) - prev_ticks_written, 0)

        track.append(
            mido.MetaMessage(
                "set_tempo",
                tempo=mido.bpm2tempo(bpm),
                time=delta_ticks,
            )
        )
        prev_ticks_written += delta_ticks
        prev_time_sec, prev_bpm = time_sec, bpm

    track.append(mido.MetaMessage("end_of_track", time=0))

    out_path = Path(out_path)
    midi_file.save(str(out_path))
