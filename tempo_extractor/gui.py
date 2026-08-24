"""TempoExtractor AI - tkinter GUI"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .analysis import AnalysisParams
from .audio_io import SUPPORTED_EXTENSIONS
from .csv_export import save_csv
from .midi_export import save_midi
from .pipeline import TempoMapResult, filter_by_resolution, run_analysis
from .postprocess import PostProcessParams, SmoothingLevel


class TempoExtractorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TempoExtractor AI - Live Music Tempo Mapping Tool")
        self.geometry("760x680")
        self.minsize(700, 620)

        self.input_path: tk.StringVar = tk.StringVar()
        self.time_signature = tk.StringVar(value="4/4")
        self.min_bpm = tk.IntVar(value=60)
        self.max_bpm = tk.IntVar(value=180)
        self.resolution_mode = tk.StringVar(value="bar")
        self.remove_outliers = tk.BooleanVar(value=True)
        self.outlier_threshold = tk.IntVar(value=25)
        self.smoothing_enabled = tk.BooleanVar(value=True)
        self.smoothing_level = tk.StringVar(value=SmoothingLevel.MEDIUM.value)
        self.start_offset = tk.DoubleVar(value=0.0)
        self.status_text = tk.StringVar(value="Status: Ready")

        self._result: TempoMapResult | None = None
        self._progress_queue: queue.Queue[str] = queue.Queue()

        self._build_layout()

    # ---------------------------------------------------------------- UI --
    def _build_layout(self) -> None:
        pad = {"padx": 8, "pady": 4}

        file_frame = ttk.LabelFrame(self, text="Input File")
        file_frame.pack(fill="x", **pad)
        ttk.Entry(file_frame, textvariable=self.input_path).pack(
            side="left", fill="x", expand=True, padx=(8, 4), pady=6
        )
        ttk.Button(file_frame, text="Browse", command=self._browse_file).pack(
            side="left", padx=(0, 8), pady=6
        )

        settings_frame = ttk.LabelFrame(self, text="Analysis Settings")
        settings_frame.pack(fill="x", **pad)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", padx=8, pady=4)
        ttk.Label(row1, text="Time Signature:").pack(side="left")
        ttk.Combobox(
            row1,
            textvariable=self.time_signature,
            values=["4/4", "3/4", "6/8"],
            width=6,
            state="readonly",
        ).pack(side="left", padx=(4, 20))

        ttk.Label(row1, text="BPM Range:").pack(side="left")
        ttk.Spinbox(row1, from_=20, to=300, textvariable=self.min_bpm, width=5).pack(
            side="left", padx=(4, 2)
        )
        ttk.Label(row1, text="-").pack(side="left")
        ttk.Spinbox(row1, from_=20, to=300, textvariable=self.max_bpm, width=5).pack(
            side="left", padx=(2, 4)
        )

        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x", padx=8, pady=4)
        ttk.Label(row2, text="Analysis Mode:").pack(side="left")
        ttk.Radiobutton(
            row2, text="Bar-based", variable=self.resolution_mode, value="bar"
        ).pack(side="left", padx=(4, 8))
        ttk.Radiobutton(
            row2, text="Beat-based", variable=self.resolution_mode, value="beat"
        ).pack(side="left")

        pp_frame = ttk.LabelFrame(self, text="Post-Processing (Know-How)")
        pp_frame.pack(fill="x", **pad)

        row3 = ttk.Frame(pp_frame)
        row3.pack(fill="x", padx=8, pady=4)
        ttk.Checkbutton(
            row3, text="Remove Outlier Spikes  Threshold:", variable=self.remove_outliers
        ).pack(side="left")
        ttk.Spinbox(
            row3, from_=5, to=90, textvariable=self.outlier_threshold, width=4
        ).pack(side="left", padx=(4, 2))
        ttk.Label(row3, text="%").pack(side="left")

        row4 = ttk.Frame(pp_frame)
        row4.pack(fill="x", padx=8, pady=4)
        ttk.Checkbutton(
            row4, text="Apply Smoothing Filter:", variable=self.smoothing_enabled
        ).pack(side="left")
        ttk.Combobox(
            row4,
            textvariable=self.smoothing_level,
            values=[lvl.value for lvl in SmoothingLevel],
            width=10,
            state="readonly",
        ).pack(side="left", padx=(4, 20))
        ttk.Label(row4, text="Start Offset (sec):").pack(side="left")
        ttk.Spinbox(
            row4,
            from_=-10.0,
            to=10.0,
            increment=0.01,
            textvariable=self.start_offset,
            width=7,
        ).pack(side="left", padx=(4, 0))

        self.start_button = ttk.Button(
            self, text="Start Analysis", command=self._start_analysis
        )
        self.start_button.pack(pady=6)

        ttk.Label(self, textvariable=self.status_text).pack(anchor="w", padx=12)

        chart_frame = ttk.LabelFrame(self, text="Tempo Curve Preview")
        chart_frame.pack(fill="both", expand=True, **pad)
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Bar")
        self.ax.set_ylabel("BPM")
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        button_row = ttk.Frame(self)
        button_row.pack(pady=8)
        self.save_mid_button = ttk.Button(
            button_row, text="Save .MID (MIDI)", command=self._save_midi, state="disabled"
        )
        self.save_mid_button.pack(side="left", padx=6)
        self.save_csv_button = ttk.Button(
            button_row, text="Save .CSV", command=self._save_csv, state="disabled"
        )
        self.save_csv_button.pack(side="left", padx=6)

    # ------------------------------------------------------------ actions --
    def _browse_file(self) -> None:
        exts = " ".join(f"*{e}" for e in sorted(SUPPORTED_EXTENSIONS))
        path = filedialog.askopenfilename(
            title="Select audio file",
            filetypes=[("Audio files", exts), ("All files", "*.*")],
        )
        if path:
            self.input_path.set(path)

    def _start_analysis(self) -> None:
        input_path = self.input_path.get().strip()
        if not input_path:
            messagebox.showwarning("TempoExtractor AI", "音声ファイルを選択してください。")
            return
        if not Path(input_path).exists():
            messagebox.showerror("TempoExtractor AI", "指定されたファイルが見つかりません。")
            return
        if self.min_bpm.get() >= self.max_bpm.get():
            messagebox.showerror("TempoExtractor AI", "BPM範囲が不正です (Min < Max)。")
            return

        self.start_button.config(state="disabled")
        self.save_mid_button.config(state="disabled")
        self.save_csv_button.config(state="disabled")
        self.status_text.set("Status: Analyzing...")

        analysis_params = AnalysisParams(
            time_signature=self.time_signature.get(),
            min_bpm=float(self.min_bpm.get()),
            max_bpm=float(self.max_bpm.get()),
        )
        smoothing = (
            SmoothingLevel(self.smoothing_level.get())
            if self.smoothing_enabled.get()
            else SmoothingLevel.OFF
        )
        postprocess_params = PostProcessParams(
            start_offset_sec=float(self.start_offset.get()),
            remove_outliers=bool(self.remove_outliers.get()),
            outlier_threshold=float(self.outlier_threshold.get()) / 100.0,
            smoothing=smoothing,
        )

        thread = threading.Thread(
            target=self._run_analysis_worker,
            args=(input_path, analysis_params, postprocess_params),
            daemon=True,
        )
        thread.start()
        self.after(100, self._poll_progress)

    def _run_analysis_worker(self, input_path, analysis_params, postprocess_params) -> None:
        try:
            result = run_analysis(
                input_path,
                analysis_params,
                postprocess_params,
                on_progress=lambda msg: self._progress_queue.put(("progress", msg)),
            )
            self._progress_queue.put(("done", result))
        except Exception as exc:  # noqa: BLE001
            self._progress_queue.put(("error", str(exc)))

    def _poll_progress(self) -> None:
        try:
            while True:
                kind, payload = self._progress_queue.get_nowait()
                if kind == "progress":
                    self.status_text.set(f"Status: {payload}")
                elif kind == "done":
                    self._on_analysis_done(payload)
                    return
                elif kind == "error":
                    self._on_analysis_error(payload)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_progress)

    def _on_analysis_done(self, result: TempoMapResult) -> None:
        self._result = result
        self.status_text.set(
            f"Status: Analysis Complete! Generated {result.bar_count} bars."
        )
        self.start_button.config(state="normal")
        self.save_mid_button.config(state="normal")
        self.save_csv_button.config(state="normal")
        self._draw_tempo_curve(result)

    def _on_analysis_error(self, message: str) -> None:
        self.status_text.set("Status: Error")
        self.start_button.config(state="normal")
        messagebox.showerror("TempoExtractor AI", f"解析エラー:\n{message}")

    def _draw_tempo_curve(self, result: TempoMapResult) -> None:
        self.ax.clear()
        bars = [r.bar + r.beat / 100.0 for r in result.records]
        raw = [r.raw_bpm for r in result.records]
        smoothed = [r.smoothed_bpm for r in result.records]
        self.ax.plot(bars, raw, color="#bbbbbb", linewidth=1, label="Raw")
        self.ax.plot(bars, smoothed, color="#1f77b4", linewidth=2, label="Smoothed")
        self.ax.set_xlabel("Bar")
        self.ax.set_ylabel("BPM")
        self.ax.legend(loc="upper right", fontsize=8)
        self.canvas.draw()

    def _save_midi(self) -> None:
        if not self._result:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".mid", filetypes=[("MIDI file", "*.mid")]
        )
        if not path:
            return
        try:
            records = filter_by_resolution(self._result.records, self.resolution_mode.get())
            save_midi(records, Path(path), self._result.time_signature)
            messagebox.showinfo("TempoExtractor AI", f"MIDIを保存しました:\n{path}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("TempoExtractor AI", f"保存エラー:\n{exc}")

    def _save_csv(self) -> None:
        if not self._result:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")]
        )
        if not path:
            return
        try:
            records = filter_by_resolution(self._result.records, self.resolution_mode.get())
            save_csv(records, Path(path))
            messagebox.showinfo("TempoExtractor AI", f"CSVを保存しました:\n{path}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("TempoExtractor AI", f"保存エラー:\n{exc}")


def main() -> None:
    app = TempoExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
