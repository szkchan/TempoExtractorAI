import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tempo_extractor.analysis import BeatDetection
from tempo_extractor.postprocess import PostProcessParams, SmoothingLevel, process

# 120BPM(0.5s間隔)を基準に、1拍だけ異常値(スパイク)を注入
base = 0.5
times = [i * base for i in range(20)]
# 10拍目のタイムスタンプを大きくずらして誤検出スパイクを模擬 (BPMが跳ね上がる)
times[10] = times[9] + 0.05  # 0.05s間隔 -> 1200BPM相当のスパイク

detections = [BeatDetection(timestamp=t, beat_number=(i % 4) + 1) for i, t in enumerate(times)]

records = process(
    detections,
    PostProcessParams(
        start_offset_sec=0.0,
        remove_outliers=True,
        outlier_threshold=0.25,
        smoothing=SmoothingLevel.LOW,
    ),
)

for r in records[7:13]:
    print(r)

# アウトライア除去がなければ raw_bpm[10] は 1200 のはず -> raw_bpmはそのまま残し、smoothedのみ補正される設計
assert records[10].raw_bpm > 1000, "raw_bpmは生値のまま残る設計のはず"
print("raw spike preserved:", records[10].raw_bpm)
