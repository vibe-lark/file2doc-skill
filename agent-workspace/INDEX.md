# Task Router

| Task | Read Next | Then Inspect |
| --- | --- | --- |
| Change skill trigger, workflow, or Lark document-writing behavior | `skill/README.md` | `SKILL.md` |
| Fix or extend local PDF, Office, media, ASR, Excel, or Lark-link processing | `scripts/README.md` | Matching file under `scripts/` |
| Update installation docs, CDN link, zip packaging, or public release flow | `release/README.md` | `README.md`, `.gitignore`, release zip contents |
| Review repository rules for future agents | `AGENTS.md` | Matching domain README |

## Avoid By Default

- Rendered pages such as `page_001.png`
- Extracted frames such as `frame_001.jpg`
- Temporary conversion directories under `/tmp`
- Local media inputs, office files, PDFs, and spreadsheets
- ASR model caches such as `~/.cache/sherpa-models`
