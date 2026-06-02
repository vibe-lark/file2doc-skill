#!/usr/bin/env bash
# =============================================================================
# PPT/Word 转 PDF 脚本
# =============================================================================
# 用途: 使用 LibreOffice headless 模式将 PPT/Word 文档转换为 PDF
# 依赖: LibreOffice (soffice)
# 用法: bash convert-office.sh <PPT/Word文件> <输出目录>
# 示例: bash convert-office.sh presentation.pptx /tmp/output
# 输出: 转换后的 PDF 文件路径输出到 stdout
# 注意: 日志输出到 stderr，结果数据输出到 stdout
# =============================================================================

set -euo pipefail

# --- 日志函数，统一输出到 stderr ---
log_info() {
    echo "[INFO] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

# --- 参数检查 ---
if [ $# -lt 2 ]; then
    log_error "参数不足"
    echo "用法: bash $0 <PPT/Word文件> <输出目录>" >&2
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"

# --- 校验输入文件 ---
if [ ! -f "$INPUT_FILE" ]; then
    log_error "输入文件不存在: $INPUT_FILE"
    exit 1
fi

# --- 校验文件类型 ---
EXTENSION="${INPUT_FILE##*.}"
EXTENSION_LOWER=$(echo "$EXTENSION" | tr '[:upper:]' '[:lower:]')

case "$EXTENSION_LOWER" in
    pptx|ppt|docx|doc|odt|odp|rtf)
        log_info "文件类型: .$EXTENSION_LOWER"
        ;;
    *)
        log_error "不支持的文件类型: .$EXTENSION_LOWER (支持: pptx, ppt, docx, doc, odt, odp, rtf)"
        exit 1
        ;;
esac

# --- 自动检测 LibreOffice 路径 ---
detect_libreoffice() {
    # macOS 典型路径
    local macos_paths=(
        "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        "$HOME/Applications/LibreOffice.app/Contents/MacOS/soffice"
    )

    # 先检查 PATH 中是否有 soffice
    if command -v soffice &>/dev/null; then
        echo "soffice"
        return 0
    fi

    # 再检查 libreoffice 命令 (Linux 常见)
    if command -v libreoffice &>/dev/null; then
        echo "libreoffice"
        return 0
    fi

    # macOS 特定路径检测
    for p in "${macos_paths[@]}"; do
        if [ -x "$p" ]; then
            echo "$p"
            return 0
        fi
    done

    return 1
}

SOFFICE_BIN=$(detect_libreoffice) || {
    log_error "未找到 LibreOffice，请先安装"
    log_error "  macOS: brew install --cask libreoffice"
    log_error "  Linux: sudo apt install libreoffice / sudo yum install libreoffice"
    exit 1
}

log_info "LibreOffice 路径: $SOFFICE_BIN"

# --- 创建输出目录 ---
mkdir -p "$OUTPUT_DIR"

# --- 获取输入文件的绝对路径 ---
INPUT_ABS=$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")
OUTPUT_ABS=$(cd "$OUTPUT_DIR" && pwd)

# --- 执行转换 ---
BASENAME=$(basename "$INPUT_FILE")
BASENAME_NO_EXT="${BASENAME%.*}"

log_info "开始转换: $BASENAME -> ${BASENAME_NO_EXT}.pdf"

"$SOFFICE_BIN" --headless --convert-to pdf \
    --outdir "$OUTPUT_ABS" \
    "$INPUT_ABS" \
    >&2 2>&2

# --- 校验输出文件 ---
EXPECTED_PDF="$OUTPUT_ABS/${BASENAME_NO_EXT}.pdf"

if [ ! -f "$EXPECTED_PDF" ]; then
    log_error "转换失败，未生成 PDF 文件: $EXPECTED_PDF"
    exit 1
fi

FILE_SIZE=$(stat -f%z "$EXPECTED_PDF" 2>/dev/null || stat -c%s "$EXPECTED_PDF" 2>/dev/null || echo "unknown")
log_info "转换成功: $EXPECTED_PDF (${FILE_SIZE} bytes)"

# --- 将 PDF 路径输出到 stdout ---
echo "$EXPECTED_PDF"
