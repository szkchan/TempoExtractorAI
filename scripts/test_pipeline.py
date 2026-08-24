import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tempo_extractor.analysis import AnalysisParams
from tempo_extractor.postprocess import PostProcessParams, SmoothingLevel
from tempo_extractor.pipeline import run_analysis
from tempo_extractor.midi_export import save_midi
from tempo_extractor.csv_export import save_csv

wav = Path(__file__).resolve().parent.parent / "test_click_120bpm.wav"

result = run_analysis(
    wav,
    AnalysisParams(time_signature="4/4", min_bpm=60, max_bpm=180),
    PostProcessParams(
        start_offset_sec=0.0,
        remove_outliers=True,
        outlier_threshold=0.25,
        smoothing=SmoothingLevel.MEDIUM,
    ),
    on_progress=print,
)

print(f"total records: {len(result.records)}, bars: {result.bar_count}")
for r in result.records[:8]:
    print(r)
print("...")
for r in result.records[-4:]:
    print(r)

out_dir = Path(__file__).resolve().parent.parent
save_midi(result.records, out_dir / "test_output.mid", time_signature="4/4")
save_csv(result.records, out_dir / "test_output.csv")
print("saved test_output.mid / test_output.csv")
