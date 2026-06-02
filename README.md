# attachment-to-doc-local

`attachment-to-doc-local` 是一个面向 Codex/Agent 的飞书技能，用于把常见附件和飞书链接整理成结构化、排版良好的飞书云文档。

它的核心特点是本地优先：PDF 渲染、Office 转换、视频抽帧、音视频转写、Excel 读取等预处理都在本机完成，适合隐私敏感、离线处理或高频批量转换场景。

## 能做什么

- 将 PDF、PPT、Word 渲染为页面截图，并辅助整理成图文并茂的飞书文档。
- 从视频中提取关键帧，并使用本地 ASR 生成转写文本，适合沉淀培训视频、演示录屏和教程文档。
- 将会议录音、访谈音频等转写并整理成文档。
- 读取 Excel/CSV，输出 Markdown 表格，方便生成报告或数据说明。
- 解析飞书文档、电子表格、多维表格和知识库链接，并重新组织为新的飞书云文档。
- 指导 Agent 使用飞书文档高级排版能力，例如 callout、分栏、表格和画板。

## 适用场景

- 把报告 PDF 转成可编辑、可评论、可继续补充的飞书文档。
- 把产品演示视频整理成图文教程。
- 把会议录音整理成纪要、摘要或行动项文档。
- 把 Excel 数据表整理成带结论的业务报告。
- 把已有飞书文档或表格重新排版成更适合分享的云文档。

## 文件结构

```text
attachment-to-doc-local/
├── SKILL.md
└── scripts/
    ├── convert-office.sh
    ├── extract-video-frames.sh
    ├── local-asr.py
    ├── local-parse.py
    ├── read-excel.py
    └── render-pdf-pages.py
```

`SKILL.md` 是 Agent 读取的技能说明，包含触发条件、完整工作流和排版策略。`scripts/` 中的脚本负责稳定执行本地预处理任务。

## 依赖

基础依赖：

- `python3`
- `ffmpeg`
- 飞书 CLI 工具，并完成 user 或 bot 身份认证

按文件类型可选依赖：

- LibreOffice：用于 PPT、Word、RTF 等 Office 文件转 PDF。
- `pymupdf`：用于 PDF 页面渲染，脚本可自动安装。
- `openpyxl`：用于 Excel 读取，脚本可自动安装。
- `sherpa-onnx` 和 Paraformer 中文模型：用于本地音视频转写，脚本可自动安装并下载模型。
- `bytedance-lark-parser`：用于本地解析飞书在线文档、表格和多维表格。该依赖需要可访问对应安装源的环境；如果无法安装，飞书在线链接解析能力不可用，但本地附件处理能力不受影响。

## 安装

将本目录放到 Codex/Agent 的 skills 目录中，例如：

```bash
mkdir -p ~/.codex/skills
cp -R attachment-to-doc-local ~/.codex/skills/
```

确认系统依赖：

```bash
command -v python3
command -v ffmpeg
command -v soffice || command -v libreoffice
```

确认飞书 CLI 已登录：

```bash
lark-cli auth status --as user --format json
```

如果你的环境使用其他飞书 CLI 命令名，请以实际安装的 CLI 为准。

## 快速验证

渲染 PDF 页面：

```bash
python3 scripts/render-pdf-pages.py report.pdf /tmp/report-pages --dpi 288
```

转换 Office 文件：

```bash
bash scripts/convert-office.sh presentation.pptx /tmp/office-output
```

提取视频关键帧：

```bash
bash scripts/extract-video-frames.sh demo.mp4 /tmp/demo-frames 10
```

本地音频转写：

```bash
python3 scripts/local-asr.py meeting.mp3
```

读取 Excel：

```bash
python3 scripts/read-excel.py data.xlsx --max-rows 100
```

解析飞书链接：

```bash
python3 scripts/local-parse.py "https://example.feishu.cn/docx/xxxx"
```

## 使用方式

安装后，在 Agent 对话中直接描述目标即可触发该技能，例如：

```text
帮我把这个 PDF 转成飞书文档
把这个培训视频整理成图文教程
把这段会议录音整理成纪要
帮我解析这个 Excel 生成报告
```

Agent 会先根据输入类型调用对应脚本，得到页面截图、视频帧、转写文本或表格 Markdown，再通过飞书 CLI 创建和排版飞书云文档。

## 本地版边界

本技能强调本地处理，但仍有几个边界需要注意：

- 首次音视频转写会下载 ASR 模型，约 223MB。
- PPT、Word 转换依赖 LibreOffice 的渲染结果，复杂动画或特殊字体可能与原文件略有差异。
- 飞书在线文档解析依赖额外 parser，外部环境可能无法安装。
- 最终创建、更新飞书云文档仍需要访问飞书开放平台 API。
- 脚本会在首次运行时尝试安装 Python 依赖；生产或受控环境建议提前安装并固定依赖版本。

## Skill 触发范围

该技能适合在用户提出以下类型需求时使用：

- “转成文档”
- “把这个附件转成飞书文档”
- “把 PDF/PPT/视频转成云文档”
- “解析这个文件”
- “附件转写”

更完整的 Agent 执行流程和排版策略见 [SKILL.md](./SKILL.md)。
