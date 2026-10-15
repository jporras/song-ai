"""Compatibility projection of persisted set data, without generation or approvals."""
import re


class SetMusicSpecProjection:
    def __init__(self, storage):
        self.storage = storage

    def _assets_for_set(self, song_set: dict[str, object]) -> dict[str, dict[str, object]]:
        assets: dict[str, dict[str, object]] = {}
        for key, asset_key in (
            ("instrumental", "instrumental_id"),
            ("melody", "melody_id"),
            ("lyrics", "lyrics_id"),
        ):
            asset_id = str(song_set.get(asset_key, "")).strip()
            if asset_id:
                try:
                    assets[key] = self.storage.get_asset_draft_detail(asset_id)
                except ValueError:
                    assets[key] = {}
        return assets


    def _spec_from_set_data(
        self,
        song_set: dict[str, object],
        phase_data: dict[str, object],
        assets: dict[str, dict[str, object]],
        payload: dict[str, object],
    ) -> dict[str, object]:
        intent = self._dict_or_empty(self._phase_payload(phase_data, "intent").get("intent", {}))
        music_plan = self._dict_or_empty(self._phase_payload(phase_data, "music-plan").get("musicPlan", {}))
        voice = self._dict_or_text_style(self._phase_payload(phase_data, "voice").get("voice", {}))
        lyrics = self._dict_or_empty(self._phase_payload(phase_data, "lyrics").get("lyrics", {}))
        instrumental_intent = dict(dict(assets.get("instrumental", {})).get("intent", {}))
        melody_intent = dict(dict(assets.get("melody", {})).get("intent", {}))
        lyrics_intent = dict(dict(assets.get("lyrics", {})).get("intent", {}))

        title = str(payload.get("title") or song_set.get("project_name") or "Cancion")
        description = str(payload.get("description") or song_set.get("description") or "")
        language = self._first_text(
            lyrics.get("language"),
            intent.get("language"),
            lyrics_intent.get("language"),
            "Spanish",
        )
        structure = self._structure_from_editor(phase_data, music_plan, lyrics_intent)
        instruments = self._list_value(
            intent.get("instruments")
            or music_plan.get("instruments")
            or instrumental_intent.get("instruments")
            or instrumental_intent.get("instrumentation")
            or ["acoustic guitar", "soft pad"]
        )
        duration = self._duration_seconds(music_plan, intent)
        bpm = int(self._first_number(music_plan.get("bpm"), intent.get("bpm"), instrumental_intent.get("bpm"), 72))
        voice_style = self._normalize_voice_style(
            self._first_text(
                voice.get("mainVoice"),
                voice.get("style"),
                voice.get("vocalStyle"),
                intent.get("vocalType"),
                intent.get("voice_style"),
                melody_intent.get("vocal_style"),
                "soft female vocal",
            )
        )
        return {
            "title": title,
            "project_name": title,
            "description": description,
            "song_type": self._first_text(intent.get("song_type"), instrumental_intent.get("genre"), "personal_song"),
            "recipient_name": self._first_text(intent.get("recipient"), intent.get("recipient_name"), "persona querida"),
            "language": language,
            "theme": self._first_text(lyrics.get("theme"), intent.get("theme"), lyrics_intent.get("theme"), description, "cancion personal"),
            "emotion": self._first_text(intent.get("mood"), music_plan.get("mood"), instrumental_intent.get("mood"), "tender"),
            "voice_style": voice_style,
            "bpm": bpm,
            "key": self._first_text(music_plan.get("key"), intent.get("key"), instrumental_intent.get("key"), "C major"),
            "duration_seconds": duration,
            "structure": structure,
            "instruments": instruments,
            "output_format": self._first_text(intent.get("output_format"), "mp3"),
            "source_set_id": str(song_set["set_id"]),
            "source_of_truth": "sqlite_phase_data",
        }


    def _phase_payload(self, phase_data: dict[str, object], phase: str) -> dict[str, object]:
        record = dict(phase_data.get(phase, {}))
        data = dict(record.get("data", {}))
        nested = data.get("data")
        if isinstance(nested, dict):
            return dict(nested)
        return data


    def _dict_or_empty(self, value: object) -> dict[str, object]:
        return dict(value) if isinstance(value, dict) else {}


    def _dict_or_text_style(self, value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return dict(value)
        text = str(value).strip()
        return {"style": text} if text else {}


    def _lyrics_markdown_from_set(
        self,
        song_set: dict[str, object],
        phase_data: dict[str, object],
        assets: dict[str, dict[str, object]],
    ) -> str:
        lyrics_data = self._phase_payload(phase_data, "lyrics")
        editor = dict(lyrics_data.get("lyricsEditor", {}))
        content = self._lyrics_sections_markdown(song_set, lyrics_data)
        if not content:
            content = str(editor.get("content") or "").strip()
        if not content:
            content = str(dict(assets.get("lyrics", {})).get("content") or "").strip()
        if not content:
            content = (
                f"# {song_set.get('project_name', 'Letra')}\n\n"
                "## Verse 1\nPendiente de completar desde la fase Lyrics.\n"
            )
        return self._resolve_lyrics_placeholders(content, lyrics_data).rstrip() + "\n"


    def _lyrics_sections_markdown(self, song_set: dict[str, object], lyrics_data: dict[str, object]) -> str:
        sections = lyrics_data.get("lyricSections", [])
        if not isinstance(sections, list) or not sections:
            return ""
        lines = [f"# {song_set.get('project_name', 'Letra')}", ""]
        for section in sections:
            item = dict(section)
            label = str(item.get("type") or item.get("label") or "Verse").strip() or "Verse"
            text = str(item.get("text") or "").strip()
            if text:
                lines.extend([f"## {label}", text, ""])
        return "\n".join(lines).strip()


    def _resolve_lyrics_placeholders(self, content: str, lyrics_data: dict[str, object]) -> str:
        lyrics = self._dict_or_empty(lyrics_data.get("lyrics", {}))
        placeholders = self._dict_or_empty(lyrics.get("placeholders", {}))
        resolved = content
        for key, value in placeholders.items():
            resolved = resolved.replace("{" + str(key) + "}", str(value))
        return resolved


    def _normalize_voice_style(self, value: str) -> str:
        text = value.strip()
        lowered = text.lower()
        if any(token in lowered for token in ("femenina", "female", "mujer", "woman")):
            return "soft warm female lead vocal, consistent female singer"
        if any(token in lowered for token in ("masculina", "male", "hombre", "man", "tenor", "baritone")):
            return "soft warm male lead vocal, consistent male singer"
        return text


    def _structure_from_editor(
        self,
        phase_data: dict[str, object],
        music_plan: object,
        lyrics_intent: dict[str, object],
    ) -> list[str]:
        lyrics_data = self._phase_payload(phase_data, "lyrics")
        sections = lyrics_data.get("lyricSections", [])
        if isinstance(sections, list) and sections:
            return [self._section_id(str(dict(item).get("type") or "verse")) for item in sections]
        plan_sections = dict(music_plan).get("sections", []) if isinstance(music_plan, dict) else []
        if isinstance(plan_sections, list) and plan_sections:
            return [self._section_id(str(dict(item).get("name") or dict(item).get("section") or "verse")) for item in plan_sections]
        structure = lyrics_intent.get("structure", [])
        if isinstance(structure, str):
            return [self._section_id(item) for item in structure.split(",") if item.strip()]
        if isinstance(structure, list) and structure:
            return [self._section_id(str(item)) for item in structure]
        return ["intro", "verse_1", "chorus", "bridge", "outro"]


    def _duration_seconds(self, music_plan: object, intent: object) -> int:
        if isinstance(music_plan, dict):
            direct = self._first_number(music_plan.get("durationSeconds"), music_plan.get("duration_seconds"), 0)
            if direct:
                return int(direct)
            sections = music_plan.get("sections", [])
            if isinstance(sections, list) and sections:
                total = 0
                for section in sections:
                    item = dict(section)
                    total += int(self._first_number(item.get("duration"), item.get("duration_seconds"), 0))
                if total:
                    return total
        if isinstance(intent, dict):
            direct = self._first_number(intent.get("durationSeconds"), intent.get("duration_seconds"), 0)
            if direct:
                return int(direct)
        return 120


    def _section_id(self, label: str) -> str:
        return label.strip().lower().replace(" ", "_").replace("-", "_")


    def _list_value(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []


    def _first_text(self, *values: object) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""


    def _first_number(self, *values: object) -> float:
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number > 0:
                return number
        return 0
