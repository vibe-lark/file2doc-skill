# Release Domain

## Scope

Use this domain when updating the public README, packaging the skill zip, or maintaining the stable CDN download link.

The repository is named `file2doc-skill`. The released skill directory inside the zip is named `file2doc` because that is the Codex skill name.

## Key Paths

- `README.md`: install instructions and stable download link.
- `.gitignore`: excludes generated outputs, local media, local env files, and large artifacts.
- `SKILL.md`: the required skill file that must be included in the release zip.

## Stable Download Link

The README points users to a fixed CDN zip filename. Treat this as the primary
installation link for users, especially in China. GitHub Release assets are only
version records and fallback artifacts because they are often unreliable on
domestic networks.

```text
https://lf3-static.bytednsdoc.com/obj/eden-cn/jvw_uvpabsvz_ph_ryhs/ljhwZthlaukjlkulzlp/AISolutionSkills/file2doc.zip
```

Keep the filename stable. To publish a new version, rebuild the zip from the repository contents and upload it with the same filename so existing users download the latest package from the same URL.

Use these CDN API parameters for this team-space path:

```text
email=zhangchaopeng@bytedance.com
region=CN
dir=ljhwZthlaukjlkulzlp/lark_ai_solution_poc/AISolutionSkills
file=file2doc.zip
```

Do not pass the visible CDN path as `dir`; the API maps team-space names to CDN object prefixes.

## Packaging Checklist

1. Ensure the working tree contains only intended changes.
2. Build a zip that contains one top-level `file2doc/` directory.
3. Include `SKILL.md`.
4. Include only skill runtime resources if they exist: `agents/`, `scripts/`, `references/`, `assets/`.
5. Exclude repository-maintenance files such as `.git`, `.gitignore`, `README.md`, `CONTEXT.md`, `AGENTS.md`, `agent-workspace/`, virtualenvs, output directories, local media, and caches.
6. Download the CDN URL and compare checksums with the local zip.

Example local build shape:

```bash
rm -rf /tmp/file2doc-skill-release
mkdir -p /tmp/file2doc-skill-release/file2doc
cp SKILL.md /tmp/file2doc-skill-release/file2doc/
cd /tmp/file2doc-skill-release
zip -qr file2doc.zip file2doc
unzip -l file2doc.zip
```
