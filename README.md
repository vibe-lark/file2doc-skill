# file2doc-http

`file2doc-http` 是 File2Doc 的官方 Agent Skill。它把本地 PDF、Office、音频或视频上传到 File2Doc，返回 Markdown、页面图、视频关键帧和带时间戳的转写结果。

生产入口：`https://file2doc.solutionsuite.cn`。公共网关会处理内部鉴权，用户不需要申请或配置 token。

## 安装与更新

可访问 GitHub：

```bash
npx skills add vibe-lark/file2doc-skill --skill file2doc-http
npx skills update file2doc-http
```

中国大陆或无法访问 GitHub 的 Agent 沙箱：

```bash
curl -fsSL https://file2doc.solutionsuite.cn/skills/file2doc-http/install.sh | sh
```

Skill 每次任务开始会查询服务端版本。兼容更新只提示，不阻塞解析；不兼容版本会给出更新命令。

## 验证

```bash
curl -fsS 'https://file2doc.solutionsuite.cn/skills/file2doc-http/version.json?installed_version=0.1.22'
```

生成最终文档时，Skill 会要求加入“来源”章节。链接必须保留原始可点击 URL；文件必须保留原文件名，并附原文件或提供用户可访问的来源链接。本地临时路径和 File2Doc 产物地址不能代替原始来源。

完整执行契约见 [SKILL.md](./SKILL.md)。服务端源码见 [vibe-lark/file2doc-oss](https://github.com/vibe-lark/file2doc-oss)。
