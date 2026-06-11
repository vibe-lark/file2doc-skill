# file2doc

`file2doc` 是一个面向 Codex/Agent 的飞书技能，用于把离线附件通过线上 File2Doc 服务解析成 Agent 友好的 Markdown、媒体索引、缩略图、页面截图、视频帧和转写结果，再整理成飞书云文档。

调用方只需要能访问 File2Doc 服务并上传文件流。

本仓库名为 `file2doc-skill`；发布给 Agent 安装的技能目录名为 `file2doc`。

## 能做什么

- 将 PDF、PPT、Word 等文档类附件解析成 Markdown，并按需获取缩略图和关键页面截图。
- 将视频解析成 Markdown、转写、时间线和代表性视频帧。
- 将音频解析成转写文本、摘要基础材料和可排版 Markdown。
- 将 Excel/CSV 解析成 Markdown 表格或结构化内容；复杂工作簿需要人工复核。
- 指导 Agent 使用飞书文档能力继续创建、改写和排版云文档。

## 适用场景

- 把报告 PDF 转成可编辑、可评论、可继续补充的飞书文档。
- 把产品演示视频整理成图文教程。
- 把会议录音整理成纪要、摘要或行动项文档。
- 把 PPT、Word 或 Excel 附件整理成结构化业务材料。
- 让远程 VM / K8S / Agent 环境通过文件流上传完成解析。

## 依赖

默认工作流只需要：

- `curl`
- 可访问 File2Doc 服务的网络环境
- File2Doc Bearer Token，由运行环境注入
- 飞书 CLI、`lark-doc` 或 `lark-drive` 技能，用于最终创建和排版飞书云文档

## 安装

始终下载最新版本：

```text
https://lf3-static.bytednsdoc.com/obj/eden-cn/jvw_uvpabsvz_ph_ryhs/ljhwZthlaukjlkulzlp/AISolutionSkills/file2doc.zip
```

将本目录放到 Codex/Agent 的 skills 目录中，例如：

```bash
mkdir -p ~/.codex/skills
cp -R file2doc ~/.codex/skills/
```

配置 File2Doc 服务参数：

```bash
export FILE2DOC_BASE_URL="${FILE2DOC_BASE_URL:-https://api.prd.solutionsuite.cn/file2doc}"
export FILE2DOC_BEARER_TOKEN="<从运行环境注入，不要写入文档或代码>"
```

确认飞书 CLI 已登录：

```bash
lark-cli auth status --as user --format json
```

如果你的环境使用其他飞书 CLI 命令名，请以实际安装的 CLI 为准。

## 快速验证

上传离线文件：

```bash
SOURCE_FILE="./report.pdf"
CONTENT_TYPE="application/pdf"
BASE_URL="${FILE2DOC_BASE_URL:-https://api.prd.solutionsuite.cn/file2doc}"
AUTH_HEADER=()
if [ -n "${FILE2DOC_BEARER_TOKEN:-}" ]; then
  AUTH_HEADER=(-H "Authorization: Bearer ${FILE2DOC_BEARER_TOKEN}")
fi

curl -sS -X POST "$BASE_URL/parse-jobs/upload" \
  "${AUTH_HEADER[@]}" \
  -F "file=@${SOURCE_FILE};type=${CONTENT_TYPE}" \
  -F "parser_profile=agent" \
  -F "retention=short" \
  -o /tmp/file2doc-upload.json
```

轮询进度：

```bash
JOB_ID="job_abc123"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID" "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-job.json
```

终态包括：

- `completed`
- `completed_with_warnings`
- `failed`

获取 manifest：

```bash
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/result" "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-manifest.json
```

下载 Markdown 或媒体 artifact：

```bash
ARTIFACT_ID="art_xxx"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/artifacts/$ARTIFACT_ID" \
  "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-content.md
```

如需更高 DPI 的页面图，可按页重新生成：

```bash
curl -sS -X POST "$BASE_URL/parse-jobs/$JOB_ID/assets/page-image" \
  "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"page": 3, "dpi": 216}' \
  -o /tmp/file2doc-page-image.json
```

支持 DPI：`144`, `216`, `288`。默认优先使用 `144`，看不清时再按页请求更高 DPI。

## 使用方式

安装后，在 Agent 对话中直接描述目标即可触发该技能，例如：

```text
帮我把这个 PDF 转成飞书文档
把这个培训视频整理成图文教程
把这段会议录音整理成纪要
帮我解析这个 Excel 生成报告
```

Agent 的默认流程：

1. 确认输入是调用方机器上的离线文件。
2. 通过 `POST /parse-jobs/upload` 上传文件流。
3. 轮询 `GET /parse-jobs/{job_id}`，必要时读取 `GET /parse-jobs/{job_id}/events` 查看进度。
4. 通过 `GET /parse-jobs/{job_id}/result` 获取 manifest。
5. 使用 manifest 中的 `artifact_id` 下载 Markdown、缩略图、页面截图、视频帧或转写产物。
6. 基于 Markdown 和媒体索引用飞书 CLI / `lark-doc` / `lark-drive` 创建或改写云文档。

## 边界

- 仅支持离线文件。网页 URL、飞书云文档 URL、网盘 URL 等需要先由上游 Agent 下载成文件。
- `local_path` 指调用方机器上的路径；File2Doc 服务不会主动读取调用方文件系统。
- 服务端缓存有有效期；结果过期后需要重新上传。
- job `failed` 时应直接报告 `error.code` 和 `error.message`。
- 缩略图用于快速理解，逐页截图和视频帧应按需下载，避免占用过多 Agent 上下文。
- 最终创建、更新飞书云文档仍需要访问飞书开放平台 API。

## Skill 触发范围

该技能适合在用户提出以下类型需求时使用：

- “转成文档”
- “把这个附件转成飞书文档”
- “把 PDF/PPT/视频转成云文档”
- “解析这个文件”
- “附件转写”

更完整的 Agent 执行流程和排版策略见 [SKILL.md](./SKILL.md)。
