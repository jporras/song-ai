from pathlib import Path

from core.storage import StorageManager
from models import AssetDraft, AssetType, Manifest, MusicalIntent
from utils.ids import generate_id


class MockExplorerSuite:
    def __init__(self, storage: StorageManager) -> None:
        self.instrumentals = MockInstrumentalExplorer(storage)
        self.melodies = MockMelodyExplorer(storage)
        self.lyrics = MockLyricsExplorer(storage)


class MockInstrumentalExplorer:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_random(self) -> Path:
        return self.create_from_intent(
            mood="tender",
            genre="lullaby",
            bpm=72,
            key="C major",
            instruments=["piano", "music box", "soft pad", "strings"],
            energy="low",
            mode="random",
        )

    def create_from_intent(
        self,
        mood: str,
        genre: str,
        bpm: int,
        key: str,
        instruments: list[str],
        energy: str,
        mode: str,
    ) -> Path:
        asset_id = generate_id("instrumental")
        intent = MusicalIntent(
            bpm=bpm,
            key=key,
            mood=mood,
            instruments=instruments,
            energy=energy,
            vocal_style="soft lead",
            lyrics_context=f"{genre} soundtrack for a complete personalized lullaby or emotional children song",
        )
        manifest = Manifest(asset_id=asset_id, asset_type=AssetType.INSTRUMENTAL.value, provider="mock-local")
        draft = AssetDraft(
            asset_id=asset_id,
            asset_type=AssetType.INSTRUMENTAL,
            manifest=manifest,
            intent=intent,
            metadata={"exploration_mode": mode, "genre": genre},
        )
        draft_path = self.storage.save_asset_draft(draft)
        (draft_path / "instrumental.txt").write_text(
            "Mock soundtrack/instrumental placeholder for a complete song.\n"
            f"Mode: {mode}\n"
            f"Genre: {genre}\n"
            f"Mood: {mood}\n"
            f"BPM: {bpm}\n"
            f"Key: {key}\n"
            f"Instruments: {', '.join(instruments)}\n"
            f"Energy: {energy}\n"
            "Goal: support a full tender song, not a short repetitive loop.\n",
            encoding="utf-8",
        )
        return draft_path


class MockMelodyExplorer:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_guided(self) -> Path:
        return self.create_from_intent(
            mood="tender",
            vocal_style="soft lullaby singing",
            range_hint="medium",
            structure="intro, verse 1, chorus, verse 2, final chorus, outro",
            energy="low",
            mode="guided",
        )

    def create_from_intent(
        self,
        mood: str,
        vocal_style: str,
        range_hint: str,
        structure: str,
        energy: str,
        mode: str,
    ) -> Path:
        asset_id = generate_id("melody")
        intent = MusicalIntent(
            bpm=96,
            key="C major",
            mood=mood,
            instruments=["voice guide"],
            energy=energy,
            vocal_style=vocal_style,
            lyrics_context=f"singable {structure} melody with {range_hint} vocal range for a complete lullaby",
        )
        manifest = Manifest(asset_id=asset_id, asset_type=AssetType.MELODY.value, provider="mock-local")
        draft = AssetDraft(
            asset_id=asset_id,
            asset_type=AssetType.MELODY,
            manifest=manifest,
            intent=intent,
            metadata={"exploration_mode": mode, "range_hint": range_hint, "structure": structure},
        )
        draft_path = self.storage.save_asset_draft(draft)
        (draft_path / "melody.txt").write_text(
            "Mock sung vocal melody guide placeholder.\n"
            f"Mode: {mode}\n"
            f"Vocal style: {vocal_style}\n"
            f"Range: {range_hint}\n"
            f"Structure: {structure}\n"
            f"Mood: {mood}\n"
            f"Energy: {energy}\n"
            "Goal: sung interpretation, not spoken TTS.\n",
            encoding="utf-8",
        )
        return draft_path


class MockLyricsExplorer:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def create_markdown(self) -> Path:
        return self.create_from_intent(
            theme="lullaby for {name}",
            language="Spanish",
            tone="tender",
            structure="intro, verse 1, chorus, verse 2, bridge, final chorus, outro",
            placeholders={"name": "Isabella", "image": "estrellita", "promise": "siempre cuidarte"},
            mode="markdown",
        )

    def create_from_intent(
        self,
        theme: str,
        language: str,
        tone: str,
        structure: str,
        placeholders: dict[str, str],
        mode: str,
    ) -> Path:
        asset_id = generate_id("lyrics")
        intent = MusicalIntent(
            bpm=96,
            key="C major",
            mood=tone,
            instruments=["lyrical phrasing"],
            energy="low",
            vocal_style="soft lullaby singing",
            lyrics_context=f"{language} complete emotional lyrics: {theme}",
            placeholders=placeholders,
        )
        manifest = Manifest(asset_id=asset_id, asset_type=AssetType.LYRICS.value, provider="mock-local")
        draft = AssetDraft(
            asset_id=asset_id,
            asset_type=AssetType.LYRICS,
            manifest=manifest,
            intent=intent,
            metadata={"exploration_mode": mode, "language": language, "structure": structure},
        )
        draft_path = self.storage.save_asset_draft(draft)
        (draft_path / "lyrics.md").write_text(
            "# Letra mock completa\n\n"
            f"Idioma: {language}\n\n"
            f"Tono: {tone}\n\n"
            f"Tema: {theme}\n\n"
            "## Intro\n"
            "Duerme suave, {name}, la noche ya llego.\n\n"
            "## Verso 1\n"
            "Una {image} baja despacio a tu balcon,\n"
            "trae luz en las manos y calma en la voz.\n\n"
            "## Coro\n"
            "{name}, mi cielo, respira sin temor,\n"
            "que en cada latido te guarda mi amor.\n\n"
            "## Verso 2\n"
            "Si el viento pregunta por donde andarás,\n"
            "le dire que en mis sueños aprendiste a volar.\n\n"
            "## Puente\n"
            "Y aunque el mundo sea grande, yo voy a cantar\n"
            "para {promise} hasta verte descansar.\n\n"
            "## Coro final\n"
            "{name}, mi cielo, la luna te abrazo,\n"
            "duerme entre canciones, mañana hay sol.\n\n"
            "## Outro\n"
            "Duerme suave, {name}, aqui estoy yo.\n",
            encoding="utf-8",
        )
        return draft_path

