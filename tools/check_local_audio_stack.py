from __future__ import annotations

import importlib.util
import argparse
import os
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description="Revisa requisitos del pipeline local final de Song AI.")
    parser.parse_args()

    checks = [
        ("ffmpeg", shutil.which("ffmpeg") is not None, "Instala ffmpeg o usa el contenedor Docker."),
        (
            "SONG_AI_SOUNDTRACK_COMMAND",
            bool(os.getenv("SONG_AI_SOUNDTRACK_COMMAND", "").strip()),
            "Configura el comando que genera stems/instrumental.wav.",
        ),
        (
            "SONG_AI_SINGING_VOICE_COMMAND",
            bool(os.getenv("SONG_AI_SINGING_VOICE_COMMAND", "").strip()),
            "Configura el comando que genera stems/vocals.wav.",
        ),
        (
            "transformers",
            importlib.util.find_spec("transformers") is not None,
            "Necesario si usas tools/musicgen_generate.py.",
        ),
        (
            "torch",
            importlib.util.find_spec("torch") is not None,
            "Necesario si usas tools/musicgen_generate.py.",
        ),
        (
            "scipy",
            importlib.util.find_spec("scipy") is not None,
            "Necesario para escribir WAV desde tools/musicgen_generate.py.",
        ),
    ]

    missing = []
    print("=== Song AI local audio stack ===")
    for name, ok, help_text in checks:
        status = "OK" if ok else "FALTA"
        print(f"{status:5} {name} - {help_text}")
        if not ok:
            missing.append(name)

    if missing:
        print("\nPipeline local final incompleto:", ", ".join(missing))
        return 1
    print("\nPipeline local final listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
