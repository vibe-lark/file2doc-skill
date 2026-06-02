---
name: attachment-to-doc-local
version: 2.1.0
description: "通用附件转飞书文档（纯本地版）：将 PDF、PPT、Word、视频、音频、图片、Excel、飞书表格/多维表格等附件转换或改写为高质量排版的飞书云文档。所有处理在本地完成，无需远程服务。当用户说「转成文档」「改写成飞书云文档」「帮我把这个附件转成飞书文档」「把 PDF/PPT/视频 转成云文档」「解析这个文件」「附件转写」时触发。"
metadata:
  requires:
    bins: ["ffmpeg", "python3"]
    capabilities: ["飞书 CLI 工具（用于文档创建和排版）"]
    services: []
---

# 通用附件转飞书文档（纯本地版）

将任意类型的附件文件转换为高质量排版的飞书云文档。**所有处理在本地完成，零远程服务依赖。**

**架构**: 本地脚本处理（帧提取/PDF渲染/ASR转写/文档解析/Excel读取） + 飞书 CLI 工具高级排版。

> **前置条件:**
> 1. 确保你的飞书 CLI 工具已完成认证登录（支持 user 或 bot 身份）。
> 2. 本 Skill 的 `scripts/` 目录下包含全部辅助脚本。
> 3. 系统需安装 `ffmpeg` 和 `python3`，其余 Python 依赖由脚本自动安装。

---

## 处理能力总览

| 类型 | 扩展名 | 处理脚本 | 自动安装的依赖 |
|------|--------|---------|--------------|
| PDF | `.pdf` | `render-pdf-pages.py` | pymupdf |
| PPT | `.ppt` `.pptx` | `convert-office.sh` + `render-pdf-pages.py` | LibreOffice, pymupdf |
| Word | `.doc` `.docx` `.rtf` | `convert-office.sh` + `render-pdf-pages.py` | LibreOffice, pymupdf |
| 视频 | `.mp4` `.mov` `.avi` `.mkv` `.webm` | `extract-video-frames.sh` + `local-asr.py` | sherpa-onnx, Paraformer 模型(~223MB) |
| 音频 | `.mp3` `.wav` `.m4a` `.aac` `.ogg` `.flac` | `local-asr.py` | sherpa-onnx, Paraformer 模型(~223MB) |
| 图片 | `.png` `.jpg` `.gif` `.bmp` `.webp` `.svg` | 无需脚本 | 无 |
| Excel/CSV | `.xls` `.xlsx` `.csv` | `read-excel.py` | openpyxl |
| 飞书表格 | URL `/sheets/` | `local-parse.py` | bytedance-lark-parser (*) |
| 多维表格 | URL `/base/` | `local-parse.py` | bytedance-lark-parser (*) |
| 飞书文档 | URL `/docx/` `/wiki/` | `local-parse.py` | bytedance-lark-parser (*) |

> (*) `bytedance-lark-parser` 是字节内部包，需在字节内网环境下自动安装。外部用户应使用远程版 Skill (`attachment-to-doc`)。

---

## 环境依赖检查（首次使用前执行）

请逐项检查以下依赖是否可用:

1. **ffmpeg**: 运行 `command -v ffmpeg` 确认已安装。未安装时: macOS `brew install ffmpeg` / Linux `apt install ffmpeg`。
2. **python3**: 运行 `command -v python3` 确认已安装。
3. **飞书 CLI 工具**: 确认你的飞书 CLI 工具已安装并完成认证登录。
4. **LibreOffice**（仅 PPT/Word 转换需要）: 运行 `command -v soffice` 确认。macOS: `brew install --cask libreoffice` / Linux: `apt install libreoffice`。
5. **Python 依赖**（脚本会自动安装，也可提前手动安装加速首次运行）: `pip3 install pymupdf openpyxl sherpa-onnx`
6. **ASR 模型**: 首次运行 `local-asr.py` 时自动下载 ~223MB，也可提前运行 `python3 scripts/local-asr.py --help` 触发下载。

---

## 完整工作流

```
用户提供附件（文件/URL）
  |
  v
如文档主题、目标读者或改写方向无法从用户请求和源文件中判断，先向用户提问确认
  |
  v
判断类型 + 运行对应的本地脚本:
  |
  |-- PDF      -> python3 scripts/render-pdf-pages.py input.pdf /tmp/pages
  |-- PPT/Word -> bash scripts/convert-office.sh input.pptx /tmp/out
  |                -> python3 scripts/render-pdf-pages.py /tmp/out/input.pdf /tmp/pages
  |-- 视频     -> bash scripts/extract-video-frames.sh input.mp4 /tmp/frames 10
  |                -> python3 scripts/local-asr.py input.mp4
  |-- 音频     -> python3 scripts/local-asr.py input.mp3
  |-- 图片     -> 无需预处理
  |-- Excel    -> python3 scripts/read-excel.py input.xlsx > /tmp/table.md
  |-- 飞书 URL -> python3 scripts/local-parse.py "https://..."
  |
  v
获取结构化数据（截图/文本/Markdown）
  |
  v
用 Agent 自身 LLM 理解内容，规划文档结构
  |
  v
通过飞书 CLI 工具创建高质量排版的飞书文档
  （充分利用高亮块、分栏、画板等高级块）
```

---

## 第一部分: 脚本使用指南

所有脚本位于 `scripts/` 目录下。日志输出到 stderr，结果数据输出到 stdout。

### 1. PDF 页面渲染

```bash
python3 scripts/render-pdf-pages.py report.pdf /tmp/pages --dpi 288
# 输出: /tmp/pages/page_001.png, page_002.png, ...
# 输出: /tmp/pages/pages_info.json
# 首次运行自动安装 pymupdf
```

### 2. PPT/Word 转 PDF 后渲染

```bash
bash scripts/convert-office.sh presentation.pptx /tmp/output
# 输出: /tmp/output/presentation.pdf
# 需要 LibreOffice

python3 scripts/render-pdf-pages.py /tmp/output/presentation.pdf /tmp/pages
```

### 3. 视频帧提取

```bash
bash scripts/extract-video-frames.sh video.mp4 /tmp/frames 10
# 输出: /tmp/frames/frame_001.jpg, frame_002.jpg, ...
# 输出: /tmp/frames/frames_info.json
# 需要 ffmpeg
```

### 4. 音视频 ASR 转写

```bash
python3 scripts/local-asr.py meeting.mp3
# 首次运行自动安装 sherpa-onnx + 下载 Paraformer 模型(~223MB)
# 模型缓存在 ~/.cache/sherpa-models/，后续运行秒级启动
# 输出 JSON: { "text": "...", "segments": [...], "engine": "sherpa-onnx-local" }

# 视频也支持（自动提取音轨）
python3 scripts/local-asr.py tutorial.mp4

# 指定模型目录
python3 scripts/local-asr.py audio.wav --model-dir /path/to/models
```

### 5. Excel/CSV 读取

```bash
python3 scripts/read-excel.py data.xlsx
# 输出 Markdown 表格到 stdout
# 首次运行自动安装 openpyxl

python3 scripts/read-excel.py data.csv --max-rows 100
```

### 6. 飞书文档解析

```bash
# 使用当前登录用户的身份解析（推荐）
python3 scripts/local-parse.py "https://xxx.feishu.cn/sheets/shtcnXXX"
# 自动通过飞书 CLI 工具获取 user_access_token
# 首次运行自动安装 bytedance-lark-parser（需字节内网）

# 指定 token
python3 scripts/local-parse.py "https://xxx.feishu.cn/docx/doxcnXXX" --token t-xxx

# 使用 bot 身份
python3 scripts/local-parse.py "https://xxx.feishu.cn/base/bascnXXX" --as-bot
```

---

## 第二部分: 高质量文档排版指南

### 基础操作

通过飞书 CLI 工具执行以下文档操作:

1. **创建文档**: 使用文档创建命令，传入标题和 Markdown 内容，指定身份（user 或 bot）。
2. **追加内容**: 使用文档更新命令，指定文档 ID/URL，以 append 模式追加 Markdown 内容。适合长文档分段写入。
3. **插入图片**: 使用媒体插入命令，指定文档 ID/URL、本地图片文件路径、对齐方式和图片说明。注意图片只能追加到文档末尾。

### 高级块类型

以下均为 Lark-flavored Markdown 语法，在创建/更新文档时作为 Markdown 内容传入。

#### 高亮块 (Callout) -- 用于重点提示、注意事项、总结

```html
<callout emoji="icon_bulb" background-color="light-blue" border-color="blue">

**核心发现**: 需要重点关注的内容。

</callout>
```

可用颜色: `light-red` / `light-blue` / `light-green` / `light-yellow` / `light-orange` / `light-purple` / `pale-gray`

> callout 内**不支持**代码块、表格、图片。

#### 分栏布局 (Grid) -- 用于对比、并列展示

```html
<grid cols="2">
<column width="50">

### 优势

- 第一点
- 第二点

</column>
<column width="50">

### 劣势

- 第一点
- 第二点

</column>
</grid>
```

支持 2-5 列，`width` 为百分比，总和须为 100。

#### 画板 (Whiteboard) -- 用于架构图、流程图

```html
<whiteboard type="blank"></whiteboard>
```

创建空白画板后，通过飞书 CLI 工具的画板更新命令填充内容（传入文档 ID 和画板 token）。

#### 增强表格 (lark-table)

```html
<lark-table column-widths="200,300,200" header-row="true">
<lark-tr>
<lark-td>

**表头**

</lark-td>
</lark-tr>
</lark-table>
```

#### 引用容器

```html
<quote-container>

多段落引用内容

</quote-container>
```

#### 文字样式

```markdown
# 标题 {color="red" align="center"}
{color="blue"}蓝色文字
{align="center"}居中段落
- [ ] 待办
- [x] 已完成
---
```

---

## 第三部分: 按文件类型的排版策略

### 策略 A: 图文交替排版（PDF / PPT / Word）

**关键约束**: 图片插入只能追加到文档**末尾**。必须按 "写文字 -> 插图 -> 写文字 -> 插图" 的顺序交替操作，避免出现全文文字和全部图片分离排版。

**理解与事实要求**:

- 必须逐一阅读源文件的所有页面，先理解整体主题、章节关系、核心事实和每页承载的信息，再规划新文档结构。
- 尊重源文件事实，不得捏造源文件没有出现的结论、数据、实体、时间、因果关系或背景说明。
- 当文档主题、目标读者、改写重点或标题无法从源文件中可靠判断时，先向用户提问；不要自行编造主题。
- 需要尽量把 PDF 图片中的文字、图表、流程、页面结构和关键信息还原为可读文字；截图只作为辅助证据和视觉参照。
- 有选择地保留核心原始页面截图：优先保留含关键图表、流程图、架构图、复杂版式、重要表格或视觉证据的页面；纯文字页可用文字复述替代。
- 每张保留的截图必须与对应章节文字相邻排版，并在截图前后提供解释、摘要或引用说明，使用户无需离开上下文即可理解图片内容。
- 改写不是简单 OCR 堆叠：应把页面内容组织为标题、摘要、要点、表格、分栏对比、高亮块等更适合阅读的飞书文档结构。

#### 步骤:

1. **预处理**: 运行 `render-pdf-pages.py` 将 PDF 渲染为逐页截图。
2. **逐页阅读与规划**: 阅读所有页面截图，记录每页主题、事实、图表/表格、需要保留的原图和可文字化还原的内容；如果主题不确定，先向用户提问。
3. **创建文档 + 首段文字**: 通过飞书 CLI 创建文档，写入标题、概述（用 callout）、结构说明和第 1 页/第 1 组页面的改写内容。

   示例 Markdown 内容:
   ```markdown
   # 文档标题

   <callout emoji="icon_info" background-color="light-blue">

   **文档概述**: 基于 XX 报告整理，共 N 页。

   </callout>

   ## 第 1 页

   这一页展示了...。关键事实包括...
   ```

4. **插入对应截图**: 通过飞书 CLI 的媒体插入命令，将需要保留的 `page_001.png` 居中插入；不要把图片集中放在文末。
5. **交替追加文字和图片**: 重复步骤 3-4 直到所有页面处理完毕。可按章节合并相邻页面，但必须保证每页事实已被阅读和覆盖。

### 策略 B: 视频教程文档（帧截图 + ASR）

#### 步骤:

1. **本地帧提取**: 运行 `extract-video-frames.sh` 提取关键帧。
2. **本地 ASR 转写**: 运行 `local-asr.py` 获取语音转写文本。
3. **综合分析**: 结合帧画面和转写内容，选择 5-8 帧最具代表性的。
4. **创建教程文档**: 通过飞书 CLI 创建文档。

   示例 Markdown 内容:
   ```markdown
   # 教程: XXX

   <callout emoji="icon_video" background-color="light-purple">

   **视频教程整理**: 本文档基于视频内容自动整理。

   </callout>

   ## 总览

   ...

   ## 第一步: 准备工作 (0:00 - 0:30)

   ...
   ```

5. **交替插入帧截图**: 通过飞书 CLI 的媒体插入命令添加代表性帧截图。

### 策略 C: 纯文本文档（音频 / Excel / 飞书文档）

1. **音频**: 运行 `local-asr.py` 转写，提取 text 字段整理成文档。
2. **Excel**: 运行 `read-excel.py` 获取 Markdown 表格，嵌入文档。
3. **飞书文档**: 运行 `local-parse.py` 解析，提取 markdown 字段重排版。

通过飞书 CLI 创建文档，参照第二部分的排版指南使用 callout、grid 等高级块。

---

## 内容写作指引

- 先读完全部页面再写最终结构；不要只看首页或目录就开始生成完整文档。
- 优先把图片中的内容还原成可扫描的文字、表格、步骤、定义、指标或结论，再决定是否保留原图。
- 严格区分源文件事实和整理者概括；如需推断，用“可理解为/可能表示”等谨慎表达，并避免加入外部事实。
- 当主题不确定、标题无法确定、目标读者不明或源文件缺失上下文时，先向用户提问确认。
- 充分利用飞书高级块: callout（重点提示）、grid（对比/指标卡）、lark-table（复杂表格）
- 每张截图前写 1-2 句引导语，并让截图紧跟其对应章节或段落
- 使用 `---` 分隔线划分章节
- 不要使用 emoji 字符
- 长文档分段写入: 先创建文档，再多次以 append 模式追加内容
- 视频帧选择: 从全部帧中选 5-8 帧最具代表性的

---

## 与远程版的区别

| 维度 | 本地版 (attachment-to-doc-local) | 远程版 (attachment-to-doc) |
|------|--------------------------------|---------------------------|
| 网络依赖 | 仅需网络下载模型（首次）和访问飞书 API | 需要访问远程预处理服务 |
| ASR | sherpa-onnx 本地运行 | 远程服务（sherpa-onnx） |
| 飞书文档解析 | 本地 lark-parser（需字节内网） | 远程服务（lark-parser） |
| 首次使用耗时 | 较长（需下载 ~223MB 模型） | 即用 |
| 磁盘占用 | ~300MB（模型+依赖） | 几乎为零 |
| 隐私性 | 全部本地处理 | 文件上传到远程服务 |
| 并发限制 | 无（取决于本地资源） | 每 IP 30次/分钟，并发上限 10 |
| 适用场景 | 隐私敏感、离线环境、高频使用 | 低频使用、不想装依赖 |

---

## 适用场景示例

> "帮我把这个 PDF 转成飞书文档"

> "把这个培训视频转成图文教程"

> "把这段会议录音整理成文档"

> "帮我解析这个 Excel 生成报告"

---

## 权限

| 操作 | 所需 scope |
|------|-----------|
| 创建云文档 | `docx:document:create` |
| 更新云文档 | `docx:document:write_only` |
| 插入图片 | `drive:file:upload_all` |
