#!/usr/bin/env python3
# =============================================================================
# 本地飞书文档解析脚本（bytedance-lark-parser）
# =============================================================================
# 用途: 将飞书在线文档（电子表格/多维表格/云文档/知识库/妙记）解析为 Markdown
# 依赖:
#   - bytedance-lark-parser（脚本自动安装，字节内部用户通过 code.byted.org 安装）
#   - 飞书 CLI 工具（lark-cli 或 larksuite-cli，用于获取 access_token）
# 用法:
#   python3 local-parse.py <飞书文档URL>
#   python3 local-parse.py <飞书文档URL> --token <access_token>
# 示例:
#   python3 local-parse.py "https://xxx.feishu.cn/sheets/shtcnXXX"
#   python3 local-parse.py "https://xxx.feishu.cn/docx/doxcnXXX" --token t-xxx
# 输出: JSON 格式（markdown + title + doc_type）输出到 stdout
# 注意:
#   - 日志输出到 stderr，结果数据输出到 stdout
#   - 需要飞书 CLI 工具已登录（用于获取 access_token）
#   - 字节内部网络环境才能安装 bytedance-lark-parser
# =============================================================================

import sys
import os
import json
import subprocess
import argparse
import time
import re


def log_info(msg):
    sys.stderr.write(f"[INFO] {msg}\n")


def log_error(msg):
    sys.stderr.write(f"[ERROR] {msg}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="飞书文档解析为 Markdown")
    parser.add_argument("feishu_url", help="飞书文档 URL")
    parser.add_argument(
        "--token", default=None,
        help="飞书 access_token（不提供则通过飞书 CLI 工具自动获取 user token）"
    )
    parser.add_argument(
        "--as-bot", action="store_true",
        help="使用 bot 身份获取 token（默认使用 user 身份）"
    )
    return parser.parse_args()


def ensure_lark_parser():
    """检测并安装 bytedance-lark-parser"""
    try:
        from bytedance.lark_parser import convert
        return convert
    except ImportError:
        pass

    log_info("bytedance-lark-parser 未安装，尝试安装...")

    # 优先从字节内部 git 仓库安装
    install_methods = [
        # 方法 1: 从内部 git 仓库（需内网环境）
        [sys.executable, "-m", "pip", "install", "--quiet",
         "git+https://code.byted.org/bytedance/lark_parser.git"],
        # 方法 2: 从 PyPI（可能是空壳包，但尝试一下）
        [sys.executable, "-m", "pip", "install", "--quiet", "bytedance-lark-parser"],
    ]

    for cmd in install_methods:
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
            from bytedance.lark_parser import convert
            log_info("bytedance-lark-parser 安装成功")
            return convert
        except Exception:
            continue

    log_error("bytedance-lark-parser 安装失败")
    log_error("该包是字节内部包，需在字节内网环境下安装:")
    log_error("  pip install git+https://code.byted.org/bytedance/lark_parser.git")
    log_error("")
    log_error("如果你不在字节内网，请使用远程版 Skill (attachment-to-doc)")
    log_error("该版本通过云端服务完成飞书文档解析。")
    sys.exit(1)


def find_lark_cli():
    """自动探测可用的飞书 CLI 工具名称（lark-cli / larksuite-cli 等）"""
    import shutil
    candidates = ["lark-cli", "larksuite-cli"]
    for name in candidates:
        if shutil.which(name):
            log_info(f"检测到飞书 CLI 工具: {name}")
            return name
    log_error("未找到飞书 CLI 工具，请先安装 lark-cli 或 larksuite-cli")
    sys.exit(1)


def get_access_token(as_bot=False):
    """通过飞书 CLI 工具获取 access_token"""
    cli = find_lark_cli()
    identity = "bot" if as_bot else "user"
    log_info(f"通过 {cli} 获取 {identity} access_token...")

    try:
        result = subprocess.run(
            [cli, "auth", "status", "--as", identity, "--format", "json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            log_error(f"{cli} auth status 失败: {result.stderr}")
            if as_bot:
                log_error(f"请确保已配置 bot: {cli} config init")
            else:
                log_error(f"请先登录: {cli} auth login")
            sys.exit(1)

        data = json.loads(result.stdout)

        # 根据身份提取不同的 token
        if as_bot:
            token = (
                data.get("data", {}).get("tenant_access_token", "") or
                data.get("data", {}).get("access_token", "")
            )
        else:
            token = (
                data.get("data", {}).get("user_access_token", "") or
                data.get("data", {}).get("access_token", "")
            )

        if not token:
            log_error(f"无法从 {cli} 获取 {identity} token，请检查认证状态")
            sys.exit(1)

        log_info(f"{identity} token 获取成功 | length={len(token)}")
        return token

    except FileNotFoundError:
        log_error(f"{cli} 未安装或不在 PATH 中")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log_error(f"{cli} 执行超时")
        sys.exit(1)
    except json.JSONDecodeError:
        log_error(f"{cli} 输出格式异常")
        sys.exit(1)


def detect_doc_type(url):
    """从 URL 推断飞书文档类型"""
    if "/sheets/" in url:
        return "sheets"
    elif "/base/" in url:
        return "bitable"
    elif "/docx/" in url:
        return "docx"
    elif "/wiki/" in url:
        return "wiki"
    elif "/minutes/" in url:
        return "minutes"
    elif "/doc/" in url:
        return "doc"
    else:
        return "unknown"


def extract_token_from_url(url):
    """从 URL 中提取文档 token"""
    # 匹配各种飞书 URL 格式中的 token
    patterns = [
        r"/sheets/(\w+)",
        r"/base/(\w+)",
        r"/docx/(\w+)",
        r"/wiki/(\w+)",
        r"/minutes/(\w+)",
        r"/doc/(\w+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def main():
    args = parse_args()

    # 1. 校验 URL
    url = args.feishu_url
    if not any(domain in url for domain in ["feishu.cn", "larksuite.com", "larkoffice.com"]):
        log_error("URL 必须是飞书文档链接（包含 feishu.cn、larksuite.com 或 larkoffice.com）")
        sys.exit(1)

    doc_type = detect_doc_type(url)
    doc_token = extract_token_from_url(url)
    log_info(f"文档类型: {doc_type} | token: {doc_token}")

    # 2. 获取 access_token
    token = args.token
    if not token:
        token = get_access_token(as_bot=args.as_bot)

    # 3. 安装 lark-parser
    convert = ensure_lark_parser()

    # 4. 调用 lark-parser 解析
    log_info(f"开始解析飞书文档: {url}")
    start_time = time.time()

    try:
        import asyncio

        async def do_convert():
            result = await convert(
                url=url,
                access_token=token,
                output_format="markdown",
            )
            return result

        # 兼容不同 Python 版本的事件循环
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = loop.run_in_executor(pool, lambda: asyncio.run(do_convert()))
        except RuntimeError:
            result = asyncio.run(do_convert())

    except Exception as e:
        log_error(f"文档解析失败: {e}")
        log_error("可能的原因:")
        log_error("  1. access_token 无权限访问该文档")
        log_error("  2. 文档 URL 格式不正确")
        log_error("  3. 网络连接问题")
        sys.exit(1)

    elapsed = time.time() - start_time

    # 5. 构造输出
    if isinstance(result, str):
        markdown = result
        title = ""
    elif isinstance(result, dict):
        markdown = result.get("markdown", result.get("content", str(result)))
        title = result.get("title", "")
    else:
        markdown = str(result)
        title = ""

    output = {
        "markdown": markdown,
        "title": title,
        "doc_type": doc_type,
        "doc_token": doc_token,
        "elapsed_ms": round(elapsed * 1000),
    }

    log_info(f"解析完成 | 耗时: {elapsed:.1f}s | markdown 长度: {len(markdown)} 字")

    # 6. 输出 JSON 到 stdout
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
