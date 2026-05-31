from __future__ import annotations

import argparse
from dataclasses import replace
import json
import math
import os
import sys
import wave
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

for candidate in (
    PROJECT_ROOT / "data" / "tools" / "ffmpeg" / "bin",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-8.1.1-full_build-shared" / "bin",
    Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-8.1.1-full_build" / "bin",
):
    if (candidate / "ffmpeg.exe").exists():
        os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
        break

from application.song_service import SongService
from config.settings import Settings
from core.storage import StorageManager


LYRICS = """[es]
[verse]
Luz pequena junto a mi
duerme suave hasta el sol

[verse]
La ventana guarda paz
y mi voz cuida tu amor
"""


def write_fast_full_song_source(path: Path, duration_seconds: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 44100
    duration = max(4, int(duration_seconds))
    progression = [261.63, 329.63, 392.0, 523.25]
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for index in range(sample_rate * duration):
            second = index / sample_rate
            note = progression[int(second // 2) % len(progression)]
            carrier = math.sin(2 * math.pi * note * second)
            harmony = 0.45 * math.sin(2 * math.pi * (note * 1.5) * second)
            envelope = min(1.0, second / 0.15, (duration - second) / 0.3)
            sample = int(max(-1.0, min(1.0, (carrier + harmony) * 0.28 * envelope)) * 32767)
            wav_file.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea una cancion pequena y recorre el flujo local de Song AI.")
    parser.add_argument("--duration", type=int, default=20, help="Duracion objetivo para ACE-Step si se ejecuta Mastering.")
    parser.add_argument("--run-master", action="store_true", help="Ejecuta Mastering full-song con ACE-Step si el pipeline esta listo.")
    parser.add_argument(
        "--fast-full-song-provider",
        action="store_true",
        help="Usa un provider local rapido de prueba para generar WAV/MP3/FLAC sin ejecutar ACE-Step.",
    )
    parser.add_argument(
        "--allow-procedural-master",
        action="store_true",
        help="Permite masterizar la guia procedural cuando ACE-Step no esta listo. No es voz cantada real.",
    )
    args = parser.parse_args()

    os.environ["SONG_AI_MAX_FULL_SONG_DURATION_SECONDS"] = str(args.duration)
    os.environ["SONG_AI_BOOTSTRAP_ON_START"] = os.getenv("SONG_AI_BOOTSTRAP_ON_START", "false")

    settings = Settings.load()
    if args.fast_full_song_provider:
        source_wav = PROJECT_ROOT / "data" / "diagnostics" / "smoke" / "fast_full_song_source.wav"
        write_fast_full_song_source(source_wav, args.duration)
        settings = replace(
            settings,
            local_models=replace(
                settings.local_models,
                full_song_command=(
                    f'"{sys.executable}" "{PROJECT_ROOT / "tools" / "use_audio_file.py"}" '
                    f'--input "{source_wav}" --output "{{output_path}}"'
                ),
            ),
        )
    storage = StorageManager(settings.data_dir)
    service = SongService(storage, settings)
    service.bootstrap()

    pipeline = service.local_pipeline_status()
    print("Pipeline local:")
    print(json.dumps(pipeline, indent=2, ensure_ascii=False))

    if args.run_master and not pipeline.get("ready") and not args.allow_procedural_master:
        print("")
        print("No ejecuto Mastering porque el pipeline local no esta listo para cancion completa real.")
        print("Ejecuta: scripts\\install-local-prereqs.ps1 -InstallFfmpeg")
        return 2

    instrumental = service.create_instrumental(
        {
            "genre": "lullaby",
            "mood": "tender",
            "bpm": 72,
            "key": "C major",
            "instruments": ["acoustic guitar", "soft pad"],
            "energy": "low",
        }
    )
    melody = service.create_melody(
        {
            "vocal_style": "soft female vocal",
            "range_hint": "medium",
            "structure": "verse, verse",
            "mood": "tender",
            "energy": "low",
        }
    )
    lyrics = service.create_lyrics(
        {
            "language": "Spanish",
            "tone": "tender",
            "theme": "short lullaby",
            "structure": "verse, verse",
            "placeholders": {"name": "Luna"},
        }
    )
    service.update_lyrics(lyrics["id"], {"content": LYRICS})

    set_path = service.set_builder.create_from_asset_ids(
        instrumental_id=instrumental["id"],
        melody_id=melody["id"],
        lyrics_id=lyrics["id"],
        project_name="Prueba local dos estrofas",
        description="Cancion pequena de dos estrofas para validar el flujo local sin Docker.",
        rule="local_smoke_two_verses",
    )
    set_id = set_path.name

    service.save_project_phase_data(
        set_id,
        "intent",
        {
            "data": {
                "intent": {
                    "language": "Spanish",
                    "genre": "lullaby",
                    "mood": "tender",
                    "bpm": 72,
                    "key": "C major",
                    "duration_seconds": args.duration,
                }
            }
        },
    )
    service.save_project_phase_data(
        set_id,
        "lyrics",
        {
            "data": {
                "lyricsEditor": {"content": LYRICS},
                "lyrics": {"language": "Spanish", "theme": "short lullaby", "tone": "tender"},
                "lyricSections": [
                    {"type": "verse", "text": "Luz pequena junto a mi\nduerme suave hasta el sol"},
                    {"type": "verse", "text": "La ventana guarda paz\ny mi voz cuida tu amor"},
                ],
            }
        },
    )
    service.save_project_phase_data(
        set_id,
        "music-plan",
        {
            "data": {
                "musicPlan": {
                    "bpm": 72,
                    "key": "C major",
                    "timeSignature": "4/4",
                    "genre": "lullaby",
                    "mood": "tender",
                    "duration": args.duration,
                    "instruments": ["acoustic guitar", "soft pad"],
                    "structure": ["verse", "verse"],
                    "references": ["tender Spanish lullaby, soft female vocal, acoustic guitar"],
                }
            }
        },
    )
    service.save_project_phase_data(set_id, "midi", {"data": {"melodyRole": "guide", "sections": ["verse", "verse"]}})
    service.save_project_phase_data(set_id, "instrumental", {"data": {"provider": "local-procedural", "duration": args.duration}})
    service.save_project_phase_data(
        set_id,
        "voice",
        {"data": {"voice": {"provider": "ACE-Step full-song", "style": "soft female vocal", "language": "Spanish"}}},
    )
    service.save_project_active_phase(set_id, {"phase": "production"})

    production = service.create_professional_project({"title": "Prueba local dos estrofas", "user_id": f"set:{set_id}"})
    song_id = str(production["project"]["id"])

    service.list_professional_projects()
    steps: list[tuple[str, object]] = [("seed_from_sqlite", service.get_professional_project(song_id))]
    steps.append(("midi", service.generate_professional_midi(song_id)))
    steps.append(("instrumental", service.generate_professional_instrumental(song_id)))
    steps.append(("vocals", service.generate_professional_vocals(song_id)))
    steps.append(("voice_conversion", service.convert_professional_voice(song_id)))
    steps.append(("mix", service.mix_professional_song(song_id)))

    if args.run_master:
        steps.append(("master", service.master_professional_song(song_id)))
        steps.append(("export", service.export_professional_song(song_id)))

    summary = {
        "set_id": set_id,
        "song_id": song_id,
        "project_dir": str(settings.data_dir / "projects" / song_id),
        "ran_master": args.run_master,
        "steps": [name for name, _result in steps],
        "export": service.get_professional_export(song_id) if args.run_master else {},
    }
    print("")
    print("Resumen:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
