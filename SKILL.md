---
name: file2doc
version: 3.0.0
description: "通过线上 File2Doc 服务把离线附件解析成 Agent 友好的 Markdown、缩略图、页面截图、视频帧、转写和 media index，再继续创建或改写飞书云文档。Use when 用户说「转成文档」「改写成飞书云文档」「把附件/PDF/PPT/Word/音频/视频转成云文档」「解析这个文件」「附件转写」；调用方只需上传文件流。"
metadata:
  requires:
    bins: ["curl"]
    capabilities: ["飞书 CLI 或 lark-doc/lark-drive 技能（用于最终创建和排版云文档）"]
    services: ["File2Doc HTTP service"]
---

# File2Doc 附件转飞书文档

把调用方机器上的离线附件上传到 File2Doc 服务，获取 Markdown、manifest、缩略图、页面截图、视频帧和转写产物，再用飞书文档能力整理成高质量云文档。

## 前置条件

1. 调用方机器能访问 File2Doc 服务。
2. 待解析附件已经在调用方机器上；如果来源是飞书消息、网盘、URL 或其他远程位置，先由上游 Agent 下载成离线文件。
3. 设置 File2Doc 访问参数：

```bash
export FILE2DOC_BASE_URL="${FILE2DOC_BASE_URL:-https://api.prd.solutionsuite.cn/file2doc}"
export FILE2DOC_BEARER_TOKEN="<从运行环境注入，不要写入文档或代码>"
```

4. 如需创建或更新飞书云文档，先确保飞书 CLI / `lark-doc` / `lark-drive` 已完成认证。

## 核心流程

```text
离线附件文件
  -> POST /parse-jobs/upload 上传文件流
  -> GET /parse-jobs/{job_id} 轮询状态和进度
  -> GET /parse-jobs/{job_id}/result 获取 manifest
  -> 下载 content Markdown
  -> 按需下载 thumbnails / page images / video frames / transcript artifacts
  -> 用飞书文档能力创建或改写云文档
```

关键原则：

- 只上传文件流；`local_path` 指调用方机器上的路径，File2Doc 服务不会主动读取调用方文件系统。
- 只支持离线文件；不要把网页 URL、飞书云文档 URL、YouTube URL 等直接交给 File2Doc。
- 先看 Markdown 和缩略图快速理解，再按需下载逐页截图或视频帧，避免把 Agent 上下文撑爆。
- 以 manifest 为准，不要猜服务端文件路径。
- job 失败就停止取结果。

## 上传文件

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

上传响应会包含：

```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "poll_url": "/parse-jobs/job_abc123"
}
```

## 轮询进度

```bash
JOB_ID="job_abc123"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID" "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-job.json
```

轮询到以下终态之一：

- `completed`
- `completed_with_warnings`
- `failed`

需要更细的进度历史时：

```bash
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/events" "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-events.json
```

如果状态是 `failed`，读取 `error.code` 和 `error.message` 报告给用户，不要继续请求 manifest 或 artifacts。

## 获取 Markdown 和 Manifest

```bash
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/result" "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-manifest.json
```

manifest 的核心字段：

- `content.artifact_id`: 主 Markdown artifact。
- `media_index`: 页面截图、缩略图、视频帧、嵌入图等媒体索引。
- `artifacts`: artifact 列表。它是数组，不是 map。
- `transcript`: 音频/视频转写信息。
- `timeline`: 视频帧和时间锚点。

下载主 Markdown：

```bash
CONTENT_ARTIFACT_ID="art_xxx"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/artifacts/$CONTENT_ARTIFACT_ID" \
  "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-content.md
```

Agent 应优先读取 `/tmp/file2doc-content.md` 作为文档改写基础。

## 下载图片和媒体

从 `manifest.media_index` 选择需要的项，再用该项的 `artifact_id` 下载：

```bash
MEDIA_ARTIFACT_ID="art_page_or_frame"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/artifacts/$MEDIA_ARTIFACT_ID" \
  "${AUTH_HEADER[@]}" \
  -o /tmp/file2doc-media.png
```

选择策略：

- PDF / OCR PDF：先下载 `kind=thumbnail` 快速浏览；只对关键页下载 `kind=page_image`。
- PPT / Word：优先读 Markdown；如 manifest 有媒体项，再按需取图。
- 视频：优先读 `transcript` 和 `timeline`；只下载代表性 `video_frame`。
- 音频：优先读 Markdown 和 transcript artifacts，不需要图片。
- Excel：优先读 Markdown 表格/摘要；复杂工作簿需要人工复核。

## 重新获取更高 DPI 页面图

默认页面图 DPI 是 `144`，适合 Agent 快速理解。若某页看不清，可请求更高 DPI：

```bash
curl -sS -X POST "$BASE_URL/parse-jobs/$JOB_ID/assets/page-image" \
  "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"page": 3, "dpi": 216}' \
  -o /tmp/file2doc-page-image.json
```

支持 DPI：`144`, `216`, `288`。返回 JSON 中的 `artifact_id` 可继续用 artifact endpoint 下载。

## 文件类型处理策略

### PDF / OCR PDF

1. 上传 PDF。
2. 轮询到完成。
3. 读取 Markdown，确认 OCR 内容是否覆盖图片型页面。
4. 先用 thumbnails 建立全局结构。
5. 只下载关键页 page images，并让截图紧邻对应章节。

### PPT / Word / Office

1. 上传原始 Office 文件。
2. 读取 Markdown，整理标题层级、要点、表格和图示说明。
3. 如果 manifest 提供媒体项，按需下载关键图片。

### 视频

1. 上传视频文件。
2. 读取 Markdown、`transcript`、`timeline`。
3. 按时间线选择 5-8 个代表性帧下载。
4. 写成教程、会议回放、产品演示说明时，按“时间段 -> 要点 -> 对应帧”组织。

### 音频

1. 上传音频文件。
2. 读取 Markdown 和 transcript artifacts。
3. 整理为纪要、访谈摘要、行动项或结构化笔记。

### 图片

当前主要面向文档、Office、音视频。单张图片如需 OCR，可作为文档流程的补充输入；如果服务返回失败，按失败处理。

## 飞书云文档排版

File2Doc 只负责解析，不负责创建飞书云文档。最终创建和排版应使用飞书 CLI 或 `lark-doc` / `lark-drive` 技能。

排版要求：

- 先基于 Markdown 和缩略图规划结构，再创建文档。
- 不要把所有图片堆到文末；关键图片要紧邻对应解释。
- 优先把图片中的文字还原成可读文本，截图作为证据和视觉参照。
- 使用 callout、分栏、表格、引用块等飞书文档能力提升可读性。
- 严格区分源文件事实和整理者概括；不确定时先问用户。

常用块示例：

```markdown
<callout emoji="icon_info" background-color="light-blue">

**文档概述**: 基于上传附件整理，核心内容如下。

</callout>
```

```html
<grid cols="2">
<column width="50">

### 方案 A

- 优点
- 风险

</column>
<column width="50">

### 方案 B

- 优点
- 风险

</column>
</grid>
```

## 失败处理

常见失败：

- `empty_parse_result`: 源文件没有可用文本且 OCR 未能产生内容。
- `remote_ocr_failed`: 远程 OCR 调用失败或超时。
- `empty_transcript`: 音视频没有可用转写。
- `video_frame_extraction_failed`: 视频帧提取失败。
- `result_expired`: 服务端缓存已过期，需要重新上传。

处理规则：

1. job `failed` 时，停止读取 result/package/artifact。
2. 把 `error.code` 和 `error.message` 原样告诉用户。
