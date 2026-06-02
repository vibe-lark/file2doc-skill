#!/usr/bin/env python3
# =============================================================================
# 本地 ASR 转写脚本（sherpa-onnx + Paraformer 模型）
# =============================================================================
# 用途: 将音频/视频文件转写为文本（纯本地运行，零外部依赖）
# 依赖:
#   - ffmpeg（系统级，音频转换）
#   - sherpa-onnx-node 或 sherpa-onnx Python（脚本自动检测安装）
#   - Paraformer 中文模型（脚本自动下载，约 223MB）
# 用法: python3 local-asr.py <音频/视频文件> [--model-dir 模型目录]
# 示例: python3 local-asr.py meeting.mp3
#        python3 local-asr.py video.mp4 --model-dir ~/.cache/sherpa-models
# 输出: JSON 格式（text + segments）输出到 stdout
# 注意: 日志输出到 stderr，结果数据输出到 stdout
# =============================================================================

import sys
import os
import json
import subprocess
import argparse
import shutil
import tempfile
import time
import urllib.request
import tarfile


def log_info(msg):
    sys.stderr.write(f"[INFO] {msg}\n")


def log_error(msg):
    sys.stderr.write(f"[ERROR] {msg}\n")


# --- 默认模型目录 ---
DEFAULT_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "sherpa-models")
MODEL_NAME = "sherpa-onnx-paraformer-zh-2023-03-28"
MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{MODEL_NAME}.tar.bz2"


def parse_args():
    parser = argparse.ArgumentParser(description="本地 ASR 转写（sherpa-onnx + Paraformer）")
    parser.add_argument("audio_path", help="音频或视频文件路径")
    parser.add_argument(
        "--model-dir", default=DEFAULT_MODEL_DIR,
        help=f"sherpa-onnx 模型目录 (默认: {DEFAULT_MODEL_DIR})"
    )
    parser.add_argument(
        "--language", default="zh", choices=["zh", "en"],
        help="语言 (默认: zh)"
    )
    return parser.parse_args()


def check_ffmpeg():
    """检查 ffmpeg 是否可用"""
    if not shutil.which("ffmpeg"):
        log_error("缺少依赖: ffmpeg")
        log_error("  macOS: brew install ffmpeg")
        log_error("  Linux: sudo apt install ffmpeg")
        sys.exit(1)


def ensure_sherpa_onnx():
    """检测并安装 sherpa-onnx Python 包"""
    try:
        import sherpa_onnx
        return sherpa_onnx
    except ImportError:
        pass

    log_info("sherpa-onnx 未安装，正在安装 sherpa-onnx Python 包...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "sherpa-onnx"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        log_info("sherpa-onnx 安装完成")
        import sherpa_onnx
        return sherpa_onnx
    except Exception as e:
        log_error(f"sherpa-onnx 安装失败: {e}")
        log_error("请手动安装: pip install sherpa-onnx")
        sys.exit(1)


def ensure_model(model_dir):
    """确保模型文件存在，不存在则自动下载"""
    model_path = os.path.join(model_dir, "model.int8.onnx")
    tokens_path = os.path.join(model_dir, "tokens.txt")

    if os.path.isfile(model_path) and os.path.isfile(tokens_path):
        log_info(f"模型已就绪: {model_dir}")
        return model_path, tokens_path

    # 检查是否在子目录中
    sub_dir = os.path.join(model_dir, MODEL_NAME)
    model_path_sub = os.path.join(sub_dir, "model.int8.onnx")
    tokens_path_sub = os.path.join(sub_dir, "tokens.txt")
    if os.path.isfile(model_path_sub) and os.path.isfile(tokens_path_sub):
        log_info(f"模型已就绪: {sub_dir}")
        return model_path_sub, tokens_path_sub

    # 下载模型
    os.makedirs(model_dir, exist_ok=True)
    tar_path = os.path.join(model_dir, f"{MODEL_NAME}.tar.bz2")

    if not os.path.isfile(tar_path):
        log_info(f"正在下载 Paraformer 中文模型 (~223MB)...")
        log_info(f"URL: {MODEL_URL}")
        log_info("首次下载可能需要几分钟，模型会缓存到本地供后续使用。")

        try:
            # 带进度显示的下载
            def progress_hook(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, downloaded * 100 / total_size)
                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total_size / 1024 / 1024
                    sys.stderr.write(
                        f"\r[INFO] 下载进度: {percent:.1f}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"
                    )
                    if downloaded >= total_size:
                        sys.stderr.write("\n")

            urllib.request.urlretrieve(MODEL_URL, tar_path, reporthook=progress_hook)
            log_info("模型下载完成")
        except Exception as e:
            log_error(f"模型下载失败: {e}")
            log_error("请手动下载模型:")
            log_error(f"  curl -L -o {tar_path} {MODEL_URL}")
            if os.path.isfile(tar_path):
                os.unlink(tar_path)
            sys.exit(1)

    # 解压模型（只提取需要的文件）
    log_info("正在解压模型...")
    try:
        with tarfile.open(tar_path, "r:bz2") as tar:
            for member in tar.getmembers():
                basename = os.path.basename(member.name)
                if basename in ("model.int8.onnx", "tokens.txt"):
                    # 提取到 model_dir（扁平化）
                    member.name = basename
                    tar.extract(member, model_dir)
                    log_info(f"  已解压: {basename}")
        # 清理压缩包
        os.unlink(tar_path)
        log_info("模型解压完成，压缩包已清理")
    except Exception as e:
        log_error(f"模型解压失败: {e}")
        sys.exit(1)

    model_path = os.path.join(model_dir, "model.int8.onnx")
    tokens_path = os.path.join(model_dir, "tokens.txt")

    if not os.path.isfile(model_path) or not os.path.isfile(tokens_path):
        log_error("模型文件不完整，请重新运行脚本")
        sys.exit(1)

    return model_path, tokens_path


def convert_to_wav(input_path, output_dir):
    """用 ffmpeg 将音频/视频转换为 16kHz 单声道 WAV"""
    wav_path = os.path.join(output_dir, "audio_16k.wav")
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-f", "wav",
        wav_path
    ]
    log_info(f"转换为 16kHz WAV: {os.path.basename(input_path)}")
    try:
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            check=True, timeout=300
        )
    except subprocess.CalledProcessError as e:
        log_error(f"ffmpeg 转换失败: {e.stderr.decode() if e.stderr else 'unknown error'}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        log_error("ffmpeg 转换超时 (>5min)")
        sys.exit(1)

    if not os.path.isfile(wav_path):
        log_error("WAV 转换失败：输出文件不存在")
        sys.exit(1)

    size_mb = os.path.getsize(wav_path) / 1024 / 1024
    log_info(f"WAV 文件大小: {size_mb:.1f}MB")
    return wav_path


def transcribe(sherpa_onnx, model_path, tokens_path, wav_path):
    """使用 sherpa-onnx 进行 ASR 转写"""
    log_info("开始 ASR 转写...")
    start_time = time.time()

    try:
        recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
            paraformer=model_path,
            tokens=tokens_path,
            num_threads=4,
            sample_rate=16000,
            feature_dim=80,
        )
    except Exception as e:
        log_error(f"创建识别器失败: {e}")
        sys.exit(1)

    # 读取 WAV 文件
    import wave
    try:
        with wave.open(wav_path, "rb") as wf:
            assert wf.getnchannels() == 1, "必须是单声道"
            assert wf.getsampwidth() == 2, "必须是 16-bit"
            assert wf.getframerate() == 16000, "必须是 16kHz"
            frames = wf.readframes(wf.getnframes())
            n_frames = wf.getnframes()
    except Exception as e:
        log_error(f"读取 WAV 文件失败: {e}")
        sys.exit(1)

    # 转为浮点数组
    import array
    samples = array.array("h", frames)
    samples_float = [s / 32768.0 for s in samples]

    duration_sec = n_frames / 16000
    log_info(f"音频时长: {duration_sec:.1f}s")

    # 创建流并识别
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, samples_float)
    recognizer.decode_stream(stream)

    text = stream.result.text.strip()
    elapsed = time.time() - start_time

    log_info(f"转写完成 | 耗时: {elapsed:.1f}s | 文本长度: {len(text)} 字")

    # sherpa-onnx 离线模式不提供时间戳分段，返回完整文本
    result = {
        "text": text,
        "segments": [],
        "engine": "sherpa-onnx-local",
        "duration_sec": round(duration_sec, 2),
        "elapsed_ms": round(elapsed * 1000),
    }

    return result


def main():
    args = parse_args()

    # 1. 检查输入文件
    if not os.path.isfile(args.audio_path):
        log_error(f"文件不存在: {args.audio_path}")
        sys.exit(1)

    # 2. 检查 ffmpeg
    check_ffmpeg()

    # 3. 安装 sherpa-onnx
    sherpa_onnx = ensure_sherpa_onnx()

    # 4. 确保模型就绪
    model_path, tokens_path = ensure_model(args.model_dir)

    # 5. 转换为 WAV
    tmpdir = tempfile.mkdtemp(prefix="asr_")
    try:
        wav_path = convert_to_wav(args.audio_path, tmpdir)

        # 6. ASR 转写
        result = transcribe(sherpa_onnx, model_path, tokens_path, wav_path)

        # 7. 输出 JSON 到 stdout
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        # 清理临时文件
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
