#!/usr/bin/env bash
# =============================================================================
# 视频关键帧提取脚本
# =============================================================================
# 用途: 从视频文件中按固定间隔提取帧图片，并生成帧信息 JSON
# 依赖: ffmpeg, ffprobe (通常系统已预装)
# 用法: bash extract-video-frames.sh <视频文件> <输出目录> [帧间隔秒数(默认10)]
# 示例: bash extract-video-frames.sh input.mp4 /tmp/frames 10
# 输出:
#   - 帧图片: frame_001.jpg, frame_002.jpg, ...
#   - 帧信息: frames_info.json
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
    echo "用法: bash $0 <视频文件> <输出目录> [帧间隔秒数(默认10)]" >&2
    exit 1
fi

INPUT_VIDEO="$1"
OUTPUT_DIR="$2"
INTERVAL="${3:-10}"

# --- 校验输入文件 ---
if [ ! -f "$INPUT_VIDEO" ]; then
    log_error "视频文件不存在: $INPUT_VIDEO"
    exit 1
fi

# --- 校验帧间隔为正整数或正浮点数 ---
if ! echo "$INTERVAL" | grep -qE '^[0-9]+\.?[0-9]*$' || [ "$(echo "$INTERVAL <= 0" | bc -l)" -eq 1 ]; then
    log_error "帧间隔必须为正数: $INTERVAL"
    exit 1
fi

# --- 检查依赖 ---
for cmd in ffmpeg ffprobe; do
    if ! command -v "$cmd" &>/dev/null; then
        log_error "缺少依赖: $cmd，请先安装 ffmpeg"
        exit 1
    fi
done

# --- 创建输出目录 ---
mkdir -p "$OUTPUT_DIR"
log_info "输出目录: $OUTPUT_DIR"

# --- 获取视频时长 ---
log_info "正在获取视频信息: $INPUT_VIDEO"
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$INPUT_VIDEO" 2>/dev/null)

if [ -z "$DURATION" ] || [ "$DURATION" = "N/A" ]; then
    log_error "无法获取视频时长，文件可能损坏或格式不支持"
    exit 1
fi

log_info "视频时长: ${DURATION}s，帧间隔: ${INTERVAL}s"

# --- 计算预计帧数 ---
EXPECTED_FRAMES=$(echo "($DURATION / $INTERVAL) + 1" | bc -l | awk '{printf "%d", $1}')
log_info "预计提取帧数: ~$EXPECTED_FRAMES"

# --- 使用 ffmpeg 提取帧 ---
log_info "开始提取帧..."
ffmpeg -v warning -i "$INPUT_VIDEO" \
    -vf "fps=1/$INTERVAL" \
    -q:v 2 \
    -start_number 1 \
    "$OUTPUT_DIR/frame_%03d.jpg" \
    2>&2

if [ $? -ne 0 ]; then
    log_error "ffmpeg 帧提取失败"
    exit 1
fi

# --- 统计实际提取的帧数 ---
FRAME_COUNT=0
for f in "$OUTPUT_DIR"/frame_*.jpg; do
    [ -f "$f" ] && FRAME_COUNT=$((FRAME_COUNT + 1))
done

if [ "$FRAME_COUNT" -eq 0 ]; then
    log_error "未提取到任何帧"
    exit 1
fi

log_info "成功提取 $FRAME_COUNT 帧"

# --- 生成 frames_info.json ---
log_info "生成帧信息 JSON..."

JSON_FILE="$OUTPUT_DIR/frames_info.json"

{
    echo "{"
    echo "  \"source\": \"$(basename "$INPUT_VIDEO")\","
    echo "  \"duration\": $DURATION,"
    echo "  \"interval\": $INTERVAL,"
    echo "  \"frame_count\": $FRAME_COUNT,"
    echo "  \"frames\": ["

    for i in $(seq 1 "$FRAME_COUNT"); do
        FRAME_NAME=$(printf "frame_%03d.jpg" "$i")
        TIMESTAMP=$(echo "($i - 1) * $INTERVAL" | bc -l | awk '{printf "%.2f", $1}')
        COMMA=","
        if [ "$i" -eq "$FRAME_COUNT" ]; then
            COMMA=""
        fi
        echo "    {\"index\": $i, \"file\": \"$FRAME_NAME\", \"timestamp\": $TIMESTAMP}$COMMA"
    done

    echo "  ]"
    echo "}"
} > "$JSON_FILE"

log_info "帧信息已保存: $JSON_FILE"

# --- 将 JSON 路径输出到 stdout，方便管道操作 ---
echo "$JSON_FILE"
