COMMON_AUDIO_EXPORTS = {
    "distribution": [
        {"extension": "mp3", "description": "Comprimido muy compatible para compartir, demos y reproduccion."},
        {"extension": "m4a", "description": "AAC comprimido, comun en moviles y buena calidad por tamano."},
        {"extension": "ogg", "description": "Comprimido abierto, util para web y apps."},
    ],
    "lossless_master": [
        {"extension": "wav", "description": "Sin compresion, comun para master, mezcla, stems y procesamiento."},
        {"extension": "flac", "description": "Lossless comprimido, alta calidad con menor tamano que WAV."},
        {"extension": "aiff", "description": "Sin compresion, usado en produccion musical y algunos DAWs."},
    ],
    "stems": [
        {"extension": "wav", "description": "Recomendado para stems por calidad y compatibilidad."},
        {"extension": "flac", "description": "Alternativa lossless para stems con menor tamano."},
    ],
    "metadata": [
        {"extension": "lyrics.md", "description": "Letra editable en Markdown."},
        {"extension": "manifest.json", "description": "Metadata tecnica y creativa del export."},
    ],
}


def planned_final_mix_exports() -> list[str]:
    return [
        "exports/final_mix.mp3",
        "exports/final_mix.m4a",
        "exports/final_mix.ogg",
        "exports/final_mix.wav",
        "exports/final_mix.flac",
        "exports/final_mix.aiff",
        "exports/lyrics.md",
        "exports/manifest.json",
    ]


def planned_stem_exports() -> list[str]:
    return [
        "stems/instrumental.wav",
        "stems/vocals.wav",
        "stems/melody_guide.wav",
        "stems/sung_voice.wav",
        "stems/drums.wav",
        "stems/bass.wav",
        "stems/music.wav",
        "stems/instrumental.flac",
        "stems/vocals.flac",
        "stems/demucs/separated_vocals.wav",
        "stems/demucs/separated_instrumental.wav",
    ]
