from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Usa un archivo de audio local como salida del pipeline. "
            "Si no es WAV compatible, intenta convertirlo con ffmpeg."
        )
    )
    parser.add_argument("--input", required=True, help="Archivo local de entrada: wav, mp3, flac, m4a, etc.")
    parser.add_argument("--output", required=True, help="Ruta WAV de salida esperada por Song AI.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise SystemExit(f"No existe el archivo de entrada: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if input_path.suffix.lower() == ".wav":
        shutil.copyfile(input_path, output_path)
        print(f"Audio WAV copiado: {output_path}")
        return 0

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise SystemExit("ffmpeg no esta disponible para convertir el audio de entrada a WAV.")

    subprocess.run(
        [
            ffmpeg_path,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_path),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(output_path),
        ],
        check=True,
    )
    print(f"Audio convertido a WAV: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
