# Agent Entry

This repository contains the canonical `file2doc-http` Agent Skill for parsing offline attachments through the File2Doc service.

## Read Order

1. Start here.
2. Open `agent-workspace/INDEX.md` and choose the task domain.
3. Read only the matching domain README.
4. Then inspect the relevant source file or script.

## Project Shape

| Area | Path | Purpose |
| --- | --- | --- |
| Skill instructions | `SKILL.md` | Trigger metadata, workflow, document-writing rules, and Lark formatting guidance. |
| Public docs | `README.md` | User-facing overview, install instructions, and stable download link. |
| Agent routing | `agent-workspace/` | Concise task routers for future agents. |

## Context Rules

- Treat `SKILL.md` as the contract for File2Doc service usage.
- Avoid reading generated media, downloaded artifacts, dependency caches, or local output directories.
- Keep agent-workspace files short and route to source paths instead of copying implementation details.

## Command Rules

- There is no package manager or test runner in this repo.
- For documentation-only changes, verify with text search and `git diff --stat`.

## Hard Rules

- Do not commit secrets, access tokens, local media inputs, generated output, or downloaded artifacts.
- Do not change the public CDN filename unless the README and release process are updated together.
- When editing `SKILL.md`, keep the frontmatter trigger description accurate and concise.
- When adapting instructions from another repo or template, replace all template-specific names, paths, commands, and package-manager assumptions.
