# Release Domain

## Scope

Use this domain when updating the public README, packaging the skill zip, or maintaining the stable CDN download link.

## Key Paths

- `README.md`: install instructions and stable download link.
- `.gitignore`: excludes generated outputs, local media, local env files, and large artifacts.
- `SKILL.md` and `scripts/`: contents that must be included in the release zip.

## Stable Download Link

The README points users to a fixed zip filename:

```text
https://lf3-static.bytednsdoc.com/obj/eden-cn/jvw_uvpabsvz_ph_ryhs/ljhwZthlaukjlkulzlp/AISolutionSkills/attachment-to-doc-local.zip
```

Keep the filename stable. To publish a new version, rebuild the zip from the repository contents and upload it with the same filename so existing users download the latest package from the same URL.

Use these CDN API parameters for this team-space path:

```text
email=zhangchaopeng@bytedance.com
region=CN
dir=ljhwZthlaukjlkulzlp/lark_ai_solution_poc/AISolutionSkills
file=attachment-to-doc-local.zip
```

Do not pass the visible CDN path as `dir`; the API maps team-space names to CDN object prefixes.

## Packaging Checklist

1. Ensure the working tree contains only intended changes.
2. Build a zip that contains one top-level `attachment-to-doc-local/` directory.
3. Exclude `.git`, virtualenvs, output directories, local media, and caches.
4. Verify the archive includes `README.md`, `SKILL.md`, `.gitignore`, and `scripts/`.
5. Download the CDN URL and compare checksums with the local zip.

Example local build shape:

```bash
rm -rf /tmp/attachment-to-doc-local-release
mkdir -p /tmp/attachment-to-doc-local-release/attachment-to-doc-local
rsync -a --exclude .git --exclude '.venv' --exclude tmp --exclude output --exclude outputs ./ /tmp/attachment-to-doc-local-release/attachment-to-doc-local/
cd /tmp/attachment-to-doc-local-release
zip -qr attachment-to-doc-local.zip attachment-to-doc-local
unzip -l attachment-to-doc-local.zip
```
