# Scripts Domain

## Scope

Use this domain for local preprocessing helpers used by `SKILL.md`.

## Key Paths

| Script | Purpose | Main External Dependency |
| --- | --- | --- |
| `scripts/render-pdf-pages.py` | Render each PDF page to PNG and write page metadata. | `pymupdf` |
| `scripts/convert-office.sh` | Convert PPT/Word/RTF files to PDF with LibreOffice. | `soffice` or `libreoffice` |
| `scripts/extract-video-frames.sh` | Extract fixed-interval video frames and write frame metadata. | `ffmpeg`, `ffprobe`, `bc` |
| `scripts/local-asr.py` | Convert audio/video to WAV and transcribe locally. | `ffmpeg`, `sherpa-onnx`, Paraformer model |
| `scripts/read-excel.py` | Convert Excel/CSV sheets to Markdown tables. | `openpyxl` for `.xlsx` |
| `scripts/local-parse.py` | Parse Lark/Feishu online documents to Markdown. | Lark CLI, `bytedance-lark-parser` |

## Constraints

- Scripts write logs to stderr and data/results to stdout where documented.
- Preserve existing CLI argument shape unless `SKILL.md` is updated at the same time.
- Do not add a repo-level dependency manager just for one helper script.
- Be careful with auto-install behavior. If adding a dependency, document first-run impact in `SKILL.md` and `README.md` when user-facing.

## Narrow Checks

Basic parser checks:

```bash
python3 scripts/render-pdf-pages.py --help
python3 scripts/read-excel.py --help
python3 scripts/local-asr.py --help
python3 scripts/local-parse.py --help
bash scripts/convert-office.sh 2>/dev/null || true
bash scripts/extract-video-frames.sh 2>/dev/null || true
```

Run real conversions only when the task includes sample files or changes conversion behavior.
