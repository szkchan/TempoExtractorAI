# TempoExtractor AI

生演奏音源からテンポマップ(MIDI/.mid, CSV)を自動生成するツール。
madmom (RNN + DBN Downbeat Tracker) を解析エンジンとして使用。

## セットアップ (Windows)

madmomはCython拡張を含むため、ビルドに **Python 3.9** と **Visual Studio Build Tools (C++)**
が必要です。このマシンでは以下の構成で動作確認済みです。

- Python: `C:\Python39\python.exe`
- C++コンパイラ: Visual Studio 2022 Community (Desktop development with C++ ワークロード)

```bash
# venv作成 (Python 3.9)
C:\Python39\python.exe -m venv .venv

# ビルド前準備
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install "numpy<2" cython

# madmomはVC++環境をロードした上でインストール (PyPI版はnumpy新版と非互換のためGitHub版を使用)
# "VS 2022 Developer Command Prompt" を開き、その中で:
.venv\Scripts\python.exe -m pip install "git+https://github.com/CPJKU/madmom.git"

# 残りの依存関係
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

VS Build Toolsが無い場合は https://visualstudio.microsoft.com/downloads/
の「Build Tools for Visual Studio」から「C++によるデスクトップ開発」ワークロードを入れてください。

## 起動

```bash
# GUI
.venv\Scripts\python.exe main.py

# CLI
.venv\Scripts\python.exe main.py -i input.wav --out-mid out.mid --out-csv out.csv ^
    --time-signature 4/4 --min-bpm 60 --max-bpm 180 --resolution beat --smoothing Medium
```

## exe化 (ダブルクリックでGUI起動)

```bash
.venv\Scripts\python.exe -m pip install pyinstaller
build_exe.bat
```

`dist\TempoExtractorAI\TempoExtractorAI.exe` が生成されます。このフォルダごと配布してください
(`_internal` にmadmomの学習済みモデルやffmpegバイナリが同梱されているため、`exe`単体では動きません)。
ダブルクリックでGUIが起動し、コマンドライン引数を付けて実行するとCLIモードとして動作します
(`--windowed`ビルドのためCLI実行時のコンソール出力は表示されない点に注意)。

サイズは madmom の学習済みモデル・scipy・matplotlib込みで約350MB程度になります。

## GitHub Actionsによる自動ビルド

`v*` 形式のタグをpushすると `.github/workflows/build-release.yml` がWindows/macOS両方を
自動ビルドし、GitHub Releaseにzipを添付します（`workflow_dispatch`でタグ無しの手動実行も可能）。

- macOSビルドは未署名(Apple Developer証明書での署名・公証なし)です。初回起動時に
  Gatekeeperの警告が出るため、`.app`を右クリック→「開く」で許可するか、
  `xattr -cr TempoExtractorAI.app` でquarantine属性を外してください。

## 動作確認用テストスクリプト

```bash
.venv\Scripts\python.exe scripts\make_test_click.py   # 120BPMクリック音源を生成
.venv\Scripts\python.exe scripts\test_pipeline.py      # 解析→MIDI/CSV出力まで一気通貫でテスト
.venv\Scripts\python.exe scripts\test_postprocess.py   # 異常値除去/スムージングの単体テスト
```

## 構成

```
tempo_extractor/
  audio_io.py       # 音声デコード (ffmpeg経由, WAV/MP3/FLAC/AAC/M4A対応)
  analysis.py        # madmom RNN+DBNによる拍/小節頭検出
  postprocess.py       # オフセット補正 / スパイク除去 / 移動平均スムージング
  midi_export.py         # SMFテンポマップ出力 (480 TPQN, 0xFF 0x51)
  csv_export.py            # 解析レポートCSV出力
  pipeline.py                # 上記の統合オーケストレーション
  gui.py                       # tkinter GUI
main.py                         # GUI/CLI エントリポイント
```

## 既知の制約

- madmomはPython 3.9系＋VC++ビルド環境が前提。Python 3.10以降やビルドツール無し環境では動作しません。
- 6/8拍子は「1小節=6拍」として解析します（付点4分音符2拍単位の検出ではありません）。
- 極端なテンポ揺れ(生演奏の大きなルバート等)は誤検出が増える可能性があるため、
  スパイク除去フィルターとStart Offset手動調整を併用してください。
