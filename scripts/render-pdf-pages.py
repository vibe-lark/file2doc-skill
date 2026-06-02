#!/usr/bin/env python3
# =============================================================================
# PDF 页面渲染为高清 PNG 脚本
# =============================================================================
# 用途: 将 PDF 每页渲染为高清 PNG 图片，并生成页面信息 JSON
# 依赖: pymupdf (fitz)，缺少时自动安装
# 用法: python3 render-pdf-pages.py <PDF文件> <输出目录> [--dpi DPI(默认288)]
# 示例: python3 render-pdf-pages.py report.pdf /tmp/pages --dpi 288
# 输出:
#   - 页面图片: page_001.png, page_002.png, ...
#   - 页面信息: pages_info.json
# 注意: 日志输出到 stderr，结果数据输出到 stdout
# =============================================================================

import sys
import os
import json
import subprocess
import argparse

# --- 自动检测并安装 pymupdf ---
try:
    import fitz  # pymupdf
except ImportError:
    sys.stderr.write("[INFO] pymupdf 未安装，正在自动安装...\n")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet", "pymupdf"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.stderr.write("[INFO] pymupdf 安装完成\n")
    import fitz


def log_info(msg):
    """日志输出到 stderr"""
    sys.stderr.write(f"[INFO] {msg}\n")


def log_error(msg):
    """错误输出到 stderr"""
    sys.stderr.write(f"[ERROR] {msg}\n")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="PDF 页面渲染为高清 PNG"
    )
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("output_dir", help="输出目录")
    parser.add_argument(
        "--dpi", type=int, default=288,
        help="渲染 DPI，默认 288 (即 2x 高清)"
    )
    return parser.parse_args()


def render_pdf(pdf_path, output_dir, dpi):
    """
    渲染 PDF 每页为 PNG 图片
    - pdf_path: PDF 文件路径
    - output_dir: 输出目录
    - dpi: 渲染分辨率
    返回页面信息列表
    """
    # 校验输入文件
    if not os.path.isfile(pdf_path):
        log_error(f"PDF 文件不存在: {pdf_path}")
        sys.exit(1)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    log_info(f"输出目录: {output_dir}")

    # 打开 PDF
    log_info(f"正在打开 PDF: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        log_error(f"无法打开 PDF 文件: {e}")
        sys.exit(1)

    page_count = len(doc)
    if page_count == 0:
        log_error("PDF 文件无页面内容")
        sys.exit(1)

    log_info(f"PDF 共 {page_count} 页，渲染 DPI: {dpi}")

    # 计算缩放因子: DPI / 72 (PDF 默认 72 DPI)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)

    pages_info = []

    for page_idx in range(page_count):
        page = doc[page_idx]
        page_num = page_idx + 1
        filename = f"page_{page_num:03d}.png"
        output_path = os.path.join(output_dir, filename)

        log_info(f"渲染第 {page_num}/{page_count} 页...")

        # 渲染页面为 pixmap
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(output_path)

        # 获取页面尺寸 (原始 PDF 点数)
        rect = page.rect

        pages_info.append({
            "index": page_num,
            "file": filename,
            "width_px": pix.width,
            "height_px": pix.height,
            "width_pt": round(rect.width, 2),
            "height_pt": round(rect.height, 2),
        })

    doc.close()
    log_info(f"成功渲染 {page_count} 页")

    return pages_info


def write_pages_info(output_dir, pdf_path, dpi, pages_info):
    """
    生成页面信息 JSON 文件
    - output_dir: 输出目录
    - pdf_path: 源 PDF 路径
    - dpi: 渲染 DPI
    - pages_info: 页面信息列表
    返回 JSON 文件路径
    """
    info = {
        "source": os.path.basename(pdf_path),
        "dpi": dpi,
        "page_count": len(pages_info),
        "pages": pages_info,
    }

    json_path = os.path.join(output_dir, "pages_info.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    log_info(f"页面信息已保存: {json_path}")
    return json_path


def main():
    args = parse_args()

    # DPI 校验
    if args.dpi <= 0:
        log_error(f"DPI 必须为正整数: {args.dpi}")
        sys.exit(1)

    # 渲染 PDF
    pages_info = render_pdf(args.pdf_path, args.output_dir, args.dpi)

    # 输出 JSON
    json_path = write_pages_info(
        args.output_dir, args.pdf_path, args.dpi, pages_info
    )

    # 将 JSON 路径输出到 stdout，方便管道操作
    print(json_path)


if __name__ == "__main__":
    main()
