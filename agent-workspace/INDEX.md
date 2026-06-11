# Task Router

| Task | Read Next | Then Inspect |
| --- | --- | --- |
| Change skill trigger, workflow, or Lark document-writing behavior | `skill/README.md` | `SKILL.md` |
| Update installation docs, CDN link, zip packaging, or public release flow | `release/README.md` | `README.md`, `.gitignore`, release zip contents |
| Review repository rules for future agents | `AGENTS.md` | Matching domain README |

## Avoid By Default

- Downloaded artifacts such as page images, thumbnails, frames, and transcripts
- Temporary conversion directories under `/tmp`
- Local media inputs, office files, PDFs, and spreadsheets
