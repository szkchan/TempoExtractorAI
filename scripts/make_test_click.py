"""テスト用: 120BPM 4/4 のクリック音源(WAV)を生成する"""
import numpy as np
import soundfile as sf

sr = 44100
bpm = 120.0
beat_interval = 60.0 / bpm
n_bars = 16
beats_per_bar = 4
lead_in = 0.8  # 曲頭の無音区間

total_beats = n_bars * beats_per_bar
duration = lead_in + total_beats * beat_interval + 1.0
audio = np.zeros(int(duration * sr))

click_len = int(0.02 * sr)
t_click = np.linspace(0, 0.02, click_len, endpoint=False)

for i in range(total_beats):
    beat_in_bar = i % beats_per_bar
    freq = 1500.0 if beat_in_bar == 0 else 1000.0
    click = np.sin(2 * np.pi * freq * t_click) * np.exp(-t_click * 80)
    start_sample = int((lead_in + i * beat_interval) * sr)
    end_sample = start_sample + click_len
    if end_sample <= len(audio):
        audio[start_sample:end_sample] += click

audio = audio / max(np.max(np.abs(audio)), 1e-9) * 0.9
sf.write("test_click_120bpm.wav", audio, sr, subtype="PCM_16")
print("wrote test_click_120bpm.wav", duration, "sec")
