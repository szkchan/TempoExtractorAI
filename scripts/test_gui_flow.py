import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tempo_extractor.gui import TempoExtractorApp

app = TempoExtractorApp()
wav = Path(__file__).resolve().parent.parent / "test_click_120bpm.wav"
app.input_path.set(str(wav))
app.min_bpm.set(60)
app.max_bpm.set(180)

app._start_analysis()

deadline = time.time() + 60
while app._result is None and time.time() < deadline:
    app.update()
    time.sleep(0.05)

assert app._result is not None, "analysis did not complete in time"
print("status:", app.status_text.get())
print("save_mid button state:", app.save_mid_button["state"])
print("save_csv button state:", app.save_csv_button["state"])
print("bar_count:", app._result.bar_count)
assert str(app.save_mid_button["state"]) == "normal"
assert str(app.save_csv_button["state"]) == "normal"
print("GUI flow test PASSED")
app.destroy()
