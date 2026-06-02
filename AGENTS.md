# Agent Entry

This repository contains a Codex skill for converting local attachments and Lark/Feishu links into well-structured Lark documents.

## Read Order

1. Start here.
2. Open `agent-workspace/INDEX.md` and choose the task domain.
3. Read only the matching domain README.
4. Then inspect the relevant source file or script.

## Project Shape

| Area | Path | Purpose |
| --- | --- | --- |
| Skill instructions | `SKILL.md` | Trigger metadata, workflow, document-writing rules, and Lark formatting guidance. |
| Helper scripts | `scripts/` | Local processing for PDF, Office files, video frames, ASR, Excel/CSV, and Lark link parsing. |
| Public docs | `README.md` | User-facing overview, install instructions, and stable download link. |
| Agent routing | `agent-workspace/` | Concise task routers for future agents. |

## Context Rules

- Do not load all scripts by default. Pick the script that matches the file type or failure being investigated.
- Treat `SKILL.md` as the contract. Script changes should preserve its documented CLI behavior unless the contract is intentionally updated.
- Avoid reading generated media, extracted frames, rendered PDF pages, ASR models, dependency caches, or local output directories.
- Keep agent-workspace files short and route to source paths instead of copying implementation details.

## Command Rules

- There is no package manager or test runner in this repo.
- Shell helpers use `bash`; Python helpers use `python3`.
- Scripts may auto-install Python dependencies at runtime. For controlled environments, document dependency changes instead of silently adding new package managers.
- For documentation-only changes, do not run media conversion or ASR jobs.

## Hard Rules

- Do not commit secrets, access tokens, local media inputs, generated output, or downloaded ASR models.
- Do not change the public CDN filename unless the README and release process are updated together.
- When editing `SKILL.md`, keep the frontmatter trigger description accurate and concise.
- When adapting instructions from another repo or template, replace all template-specific names, paths, commands, and package-manager assumptions.
