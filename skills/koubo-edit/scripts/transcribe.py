#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["mlx-whisper>=0.4.3", "static-ffmpeg>=3.0", "numpy"]
# ///
"""口播视频本机转写：抽音轨 → MLX Whisper → 带时间戳的字幕素材 JSON。

用法（任意目录，依赖由 uv 按上方内联声明自动解决）：
    uv run ~/.claude/skills/koubo-edit/scripts/transcribe.py <口播视频> -o <输出.json>

输出 JSON 结构：
    {
      "metadata": {"duration_ms", "width", "height", "fps"},
      "transcript": "整段口播文字",
      "segments": [{"start_ms", "end_ms", "text"}],   # whisper 原生分段
      "words":    [{"w", "start_ms", "end_ms"}]        # 词级时间戳，用于精细分页
    }
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def ffmpeg_paths() -> tuple[str, str]:
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        return ffmpeg, ffprobe
    from static_ffmpeg import run as static_run

    return static_run.get_or_fetch_platform_executables_else_raise()


def probe(path: Path) -> dict:
    _ffmpeg, ffprobe = ffmpeg_paths()
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,avg_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=40,
    )
    payload = json.loads(proc.stdout or "{}")
    video = next((s for s in payload.get("streams", []) if s.get("codec_type") == "video"), {})
    duration = float(payload.get("format", {}).get("duration") or 0)
    rate = video.get("avg_frame_rate") or "30/1"
    try:
        num, den = rate.split("/")
        fps = round(float(num) / float(den or 1), 3)
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    if not video or duration <= 0:
        sys.exit("错误：读不到视频画面或时长，请确认是正常的 MP4/MOV/WebM 文件")
    return {
        "duration_ms": int(duration * 1000),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": fps,
    }


def extract_wav(video: Path, wav: Path) -> None:
    ffmpeg, _ = ffmpeg_paths()
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(wav)],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0 or not wav.exists() or wav.stat().st_size == 0:
        sys.exit(f"错误：抽取音轨失败：{(proc.stderr or '')[-300:]}")


def transcribe(wav: Path, model: str) -> dict:
    import mlx_whisper
    import numpy as np

    # mlx-whisper 收到路径时会去 shell 调全局 ffmpeg；直接喂标准化后的
    # 16kHz 单声道 PCM 采样，保持自包含（与 fanout video_editor 同一做法）。
    with wave.open(str(wav), "rb") as source:
        audio = np.frombuffer(
            source.readframes(source.getnframes()), dtype="<i2"
        ).astype(np.float32) / 32768.0
    return mlx_whisper.transcribe(
        audio, path_or_hf_repo=model, language="zh", task="transcribe",
        word_timestamps=True, verbose=False,
        initial_prompt="以下是普通话中文短视频口播，请使用简体中文准确转写产品名、数字和关键词。",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("-o", "--out", type=Path, required=True)
    parser.add_argument("--model", default="mlx-community/whisper-small-mlx",
                        help="识别不准时可换 mlx-community/whisper-large-v3-turbo")
    args = parser.parse_args()
    if not args.video.exists():
        sys.exit(f"错误：找不到视频 {args.video}")

    metadata = probe(args.video)
    with tempfile.TemporaryDirectory(prefix="koubo-edit-") as tmp:
        wav = Path(tmp) / "speech.wav"
        extract_wav(args.video, wav)
        result = transcribe(wav, args.model)

    segments, words = [], []
    for seg in result.get("segments", []) or []:
        text = str(seg.get("text") or "").strip(" ，,。！？!?；;\n\t")
        if not text:
            continue
        segments.append({
            "start_ms": int(float(seg.get("start") or 0) * 1000),
            "end_ms": int(float(seg.get("end") or 0) * 1000),
            "text": text,
        })
        for word in seg.get("words", []) or []:
            token = str(word.get("word") or "").strip()
            if token:
                words.append({
                    "w": token,
                    "start_ms": int(float(word.get("start") or 0) * 1000),
                    "end_ms": int(float(word.get("end") or 0) * 1000),
                })

    payload = {
        "metadata": metadata,
        "transcript": str(result.get("text") or "").strip(),
        "segments": segments,
        "words": words,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"转写完成：{len(segments)} 段 / {len(words)} 词，"
          f"时长 {metadata['duration_ms'] / 1000:.1f}s，"
          f"画幅 {metadata['width']}x{metadata['height']} → {args.out}")


if __name__ == "__main__":
    main()
