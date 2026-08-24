"""音声デコード: 任意フォーマット(WAV/MP3/FLAC/AAC/M4A) -> 解析用WAVへの変換"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".aac", ".m4a"}

# madmom の解析パイプラインが前提とするサンプルレート
TARGET_SAMPLE_RATE = 44100


def decode_to_wav(input_path: Path) -> Path:
    """入力音声を解析用の一時WAV(PCM16, mono, 44100Hz)に変換してパスを返す。

    呼び出し元は使用後に一時ファイルを削除すること。
    """
    input_path = Path(input_path)
    if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"未対応のフォーマットです: {input_path.suffix} "
            f"(対応: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
        )
    if not input_path.exists():
        raise FileNotFoundError(f"音声ファイルが見つかりません: {input_path}")

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    fd, out_path_str = tempfile.mkstemp(suffix=".wav", prefix="tempoextractor_")
    import os

    os.close(fd)
    out_path = Path(out_path_str)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_path),
        "-ac", "1",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-sample_fmt", "s16",
        str(out_path),
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode != 0 or not out_path.exists():
        stderr = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"音声デコードに失敗しました:\n{stderr}")
    return out_path
