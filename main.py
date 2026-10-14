#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import noisereduce as nr
from tqdm import tqdm

SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wma", ".aiff", ".aif"
}


def decode_to_wav(source: Path, destination: Path, ffmpeg: str) -> None:
    command = [
        ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vn", "-acodec", "pcm_f32le", str(destination)
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or "FFmpegで音声を読み込めませんでした。"
        raise RuntimeError(message)


def process_file(source: Path, destination: Path, ffmpeg: str, strength: float) -> None:
    with tempfile.TemporaryDirectory(prefix="audio_denoise_") as temp_dir:
        decoded = Path(temp_dir) / "decoded.wav"
        decode_to_wav(source, decoded, ffmpeg)
        audio, sample_rate = sf.read(decoded, dtype="float32", always_2d=True)

        if audio.size == 0 or audio.shape[0] == 0:
            raise RuntimeError("音声データが空です。")

        cleaned_channels = []
        for channel_index in range(audio.shape[1]):
            channel = audio[:, channel_index]
            cleaned = nr.reduce_noise(
                y=channel,
                sr=sample_rate,
                stationary=False,
                prop_decrease=strength,
                n_fft=2048,
                win_length=512,
                hop_length=128,
                n_jobs=1,
            )
            cleaned_channels.append(cleaned)

        cleaned_audio = np.column_stack(cleaned_channels)
        cleaned_audio = np.nan_to_num(cleaned_audio, nan=0.0, posinf=0.0, neginf=0.0)
        cleaned_audio = np.clip(cleaned_audio, -1.0, 1.0)

        destination.parent.mkdir(parents=True, exist_ok=True)
        sf.write(destination, cleaned_audio, sample_rate, subtype="PCM_16")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="フォルダ内の音声ファイルを一括ノイズ除去し、WAV形式で出力します。"
    )
    parser.add_argument("input_dir", type=Path, help="処理する音声ファイルのフォルダ")
    parser.add_argument("output_dir", type=Path, help="処理済みファイルの保存先")
    parser.add_argument(
        "--strength", type=float, default=0.8,
        help="ノイズ除去の強さ（0.0〜1.0、初期値: 0.8）"
    )
    parser.add_argument(
        "--ffmpeg", default="ffmpeg",
        help="FFmpeg実行ファイルのパス（初期値: PATH上のffmpeg）"
    )
    parser.add_argument(
        "--recursive", action="store_true",
        help="入力フォルダ内のサブフォルダも再帰的に処理"
    )
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not input_dir.is_dir():
        parser.error(f"入力フォルダが存在しません: {input_dir}")
    if not 0.0 <= args.strength <= 1.0:
        parser.error("--strength は 0.0〜1.0 の範囲で指定してください。")
    if shutil.which(args.ffmpeg) is None and not Path(args.ffmpeg).is_file():
        parser.error("FFmpegが見つかりません。インストールするか --ffmpeg でパスを指定してください。")
    if input_dir == output_dir or input_dir in output_dir.parents:
        parser.error("出力先は入力フォルダの内部に指定できません。別のフォルダを指定してください。")

    iterator = input_dir.rglob("*") if args.recursive else input_dir.iterdir()
    files = sorted(
        path for path in iterator
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and output_dir not in path.parents
    )

    if not files:
        print("対応する音声ファイルが見つかりませんでした。", file=sys.stderr)
        return 1

    success = 0
    failures = []

    for source in tqdm(files, desc="ノイズ除去", unit="ファイル"):
        relative = source.relative_to(input_dir)
        destination = (output_dir / relative).with_suffix(".wav")
        try:
            process_file(source, destination, args.ffmpeg, args.strength)
            success += 1
        except Exception as exc:
            failures.append((source, str(exc)))
            tqdm.write(f"失敗: {source.name}: {exc}")

    print(f"\n完了: {success}/{len(files)} ファイル")
    print(f"保存先: {output_dir}")
    if failures:
        print("\n失敗したファイル:")
        for source, message in failures:
            print(f"- {source}: {message}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
