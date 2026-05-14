from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Adaptador local de voz cantada. Ejecuta un backend local real, por ejemplo ACE-Step, "
            "RVC/so-vits-svc o un script propio que produzca vocals.wav."
        )
    )
    parser.add_argument("--lyrics", required=True, help="Ruta a lyrics.md.")
    parser.add_argument("--prompt", required=True, help="Ruta al prompt musical.")
    parser.add_argument("--instrumental", required=True, help="Ruta al instrumental WAV.")
    parser.add_argument("--output", required=True, help="Ruta WAV de voz cantada esperada.")
    parser.add_argument(
        "--backend-command",
        required=True,
        help=(
            "Comando local real. Placeholders disponibles: {lyrics_path}, {prompt_path}, "
            "{instrumental_path}, {output_path}."
        ),
    )
    args = parser.parse_args()

    values = {
        "lyrics_path": str(Path(args.lyrics)),
        "prompt_path": str(Path(args.prompt)),
        "instrumental_path": str(Path(args.instrumental)),
        "output_path": str(Path(args.output)),
    }
    command = args.backend_command.format(**values)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, shell=True, check=True)

    output_path = Path(args.output)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise SystemExit(
            "El backend de voz cantada termino sin generar vocals.wav. "
            f"Salida esperada: {output_path}"
        )
    print(f"Voz cantada generada: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
