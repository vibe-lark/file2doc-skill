---
name: file2doc
version: 3.0.2
description: "通过线上 File2Doc 服务把离线附件解析成 Agent 友好的 Markdown、缩略图、页面截图、视频帧、转写和 media index，再继续创建或改写飞书云文档。Use when 用户说「转成文档」「改写成飞书云文档」「把附件/PDF/PPT/Word/音频/视频转成云文档」「解析这个文件」「附件转写」「操作手册转文档」；调用方只需上传文件流。"
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
3. 设置 File2Doc 访问参数。默认入口是 AI-knowledge 代理，会在服务端注入 File2Doc 鉴权：

```bash
export FILE2DOC_BASE_URL="${FILE2DOC_BASE_URL:-https://api.prd.solutionsuite.cn/api/file2doc}"
```

直连内部 File2Doc 服务时，才额外设置 Bearer token；默认代理入口不要让 Agent 处理 token。

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
- 必须读取 manifest；不能只用 Markdown 创建最终文档。
- 先看 Markdown 和缩略图快速理解，再按需下载逐页截图或视频帧，避免把 Agent 上下文撑爆。
- PDF 操作手册、系统教程、产品演示类文档必须使用关键截图；纯文本搬运不合格。
- 以 manifest 为准，不要猜服务端文件路径。
- job 失败就停止取结果。

## 上传文件

```bash
SOURCE_FILE="./report.pdf"
CONTENT_TYPE="application/pdf"
BASE_URL="${FILE2DOC_BASE_URL:-https://api.prd.solutionsuite.cn/api/file2doc}"

curl -sS -X POST "$BASE_URL/parse-jobs/upload" \
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
curl -sS "$BASE_URL/parse-jobs/$JOB_ID" \
  -o /tmp/file2doc-job.json
```

轮询到以下终态之一：

- `completed`
- `completed_with_warnings`
- `failed`

需要更细的进度历史时：

```bash
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/events" \
  -o /tmp/file2doc-events.json
```

如果状态是 `failed`，读取 `error.code` 和 `error.message` 报告给用户，不要继续请求 manifest 或 artifacts。

## 获取 Markdown 和 Manifest

```bash
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/result" \
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
  -o /tmp/file2doc-content.md
```

Agent 应读取 `/tmp/file2doc-content.md` 作为文档改写基础，但最终排版必须同时参考 manifest，尤其是 `media_index`。

## 下载图片和媒体

从 `manifest.media_index` 选择需要的项，再用该项的 `artifact_id` 下载：

```bash
MEDIA_ARTIFACT_ID="art_page_or_frame"
curl -sS "$BASE_URL/parse-jobs/$JOB_ID/artifacts/$MEDIA_ARTIFACT_ID" \
  -o /tmp/file2doc-media.png
```

选择策略：

- PDF / OCR PDF：先下载 `kind=thumbnail` 快速浏览；对封面、目录、流程入口、表单填写、审批/结果示例、关键异常说明等页面下载 `kind=page_image`。
- PPT / Word：优先读 Markdown；如 manifest 有媒体项，再按需取图。
- 视频：优先读 `transcript` 和 `timeline`；只下载代表性 `video_frame`。
- 音频：优先读 Markdown 和 transcript artifacts，不需要图片。
- Excel：优先读 Markdown 表格/摘要；复杂工作簿需要人工复核。

最低插图要求：

- 操作手册 / 系统教程 / 培训材料：每个主要流程至少插入 1 张关键截图；长流程插入 2-3 张。
- 截图必须紧邻对应步骤说明，不要集中堆到文末。
- 如果 manifest 有 thumbnail/page_image 但最终飞书文档没有图片，必须先说明原因并征得用户认可。
- 不要逐页无脑插图；用缩略图筛选关键页，优先保留能帮助用户执行操作的截图。

示例筛选命令：

```bash
jq -r '.media_index[] | select(.kind=="thumbnail" or .kind=="page_image") | [.kind, .page, .artifact_id, (.title // "")] | @tsv' \
  /tmp/file2doc-manifest.json
```

## 重新获取更高 DPI 页面图

默认页面图 DPI 是 `144`，适合 Agent 快速理解。若某页看不清，可请求更高 DPI：

```bash
curl -sS -X POST "$BASE_URL/parse-jobs/$JOB_ID/assets/page-image" \
  -H "Content-Type: application/json" \
  -d '{"page": 3, "dpi": 216}' \
  -o /tmp/file2doc-page-image.json
```

支持 DPI：`144`, `216`, `288`。返回 JSON 中的 `artifact_id` 可继续用 artifact endpoint 下载。

## 文件类型处理策略

### PDF / OCR PDF

1. 上传 PDF。
2. 轮询到完成。
3. 读取 manifest 和 Markdown，确认 `media_index` 是否包含 thumbnails/page images。
4. 先用 thumbnails 建立全局结构，识别封面、目录、章节页、流程步骤页、示例页。
5. 下载关键页 page images，并让截图紧邻对应章节。
6. 清理 PDF 抽取噪声：合并错误断行，去除重复页眉页脚，修正因版式导致的词语断裂。
7. 重写重复标题。不要把连续页面都命名为同一个 H3，例如多个“客户准入流程”应改成“步骤 1：进入流程提报”“步骤 2：选择业务类型”“步骤 3：填写客户信息”。

操作手册专用要求：

- 不能只生成纯文本目录和段落；必须形成可执行 SOP。
- 每个流程应包含：适用场景、入口路径、操作步骤、关键字段/附件、提交后状态、注意事项。
- 表单字段、按钮名、状态名要保留原文；不确定的界面文字不要臆造。
- 有截图时，用“步骤说明 + 截图 + 补充说明”的顺序排版。

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
- 对操作手册，重复页面标题必须重写为步骤标题；不要保留一串同名小节。
- 清理 PDF 换行噪声后再写入飞书文档，避免出现“查 / 询”“详 / 细”等断词。
- 使用 callout、分栏、表格、引用块等飞书文档能力提升可读性。
- 严格区分源文件事实和整理者概括；不确定时先问用户。

交付前自检：

- 文档是否同时使用了 Markdown 和 manifest/media_index？
- PDF 操作手册是否插入了关键截图？
- 截图是否紧邻对应步骤，而不是堆在文末？
- 重复标题是否已改成可执行步骤？
- 是否清理了明显断行、页眉页脚和重复噪声？
- job 有 warnings 时，是否在文档或回复中说明了影响？

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
