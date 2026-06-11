# Skill Domain

## Scope

Use this domain when changing how the skill is triggered, how an agent should reason about attachments, or how the final Lark document should be structured.

## Key Paths

- `SKILL.md`: required Codex skill file, including YAML frontmatter, File2Doc service workflow, Lark formatting guidance, and per-file-type strategies.
- `README.md`: user-facing summary that should remain consistent with `SKILL.md`.

## Contracts

- Frontmatter `name` must remain `file2doc`.
- Frontmatter `description` is trigger-critical. Keep it broad enough for file2doc tasks but not so broad that unrelated document work triggers it.
- The PDF/PPT/Word strategy requires reading all pages, preserving source facts, asking the user when the theme is uncertain, and keeping text near the corresponding image.
- Lark formatting examples in `SKILL.md` should remain executable as Lark-flavored Markdown through the Feishu/Lark CLI flow.

## Verification

For documentation-only changes:

```bash
rg -n "file2doc|File2Doc|改写成飞书云文档" SKILL.md README.md
git diff --stat
```

No runtime tests are expected unless scripts or executable examples changed.
