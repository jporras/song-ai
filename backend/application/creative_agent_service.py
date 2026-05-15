from __future__ import annotations

import re


class CreativeAgentService:
    FIELD_QUESTION_COPY = {
        "duration_seconds": "Cuanto quieres que dure la cancion? Por ejemplo, 90 o 120 segundos.",
        "voice_style": "Que tipo de voz imaginas: femenina suave, masculina calida, infantil o algun estilo especial?",
        "instruments": "Que instrumentos quieres sentir en la base? Puede ser piano, cuerdas, guitarra suave, pads, cajita musical u otros.",
        "bpm": "La prefieres muy lenta y arrulladora, o un poco mas moderada?",
        "key": "Quieres una tonalidad concreta, como C major, o dejamos que Qwen elija una tonalidad dulce?",
        "output_format": "Que formato final necesitas primero: wav, mp3 o ambos?",
        "structure": "Quieres una estructura clasica con intro, versos, coro, puente y outro?",
    }

    def build_initial_spec(self, user_message: str, existing_spec: dict[str, object] | None = None) -> dict[str, object]:
        spec = dict(existing_spec or {})
        text = user_message.strip()
        lower = text.lower()
        if text:
            spec["creative_brief"] = text
        if "title" not in spec:
            spec["title"] = self._title_from_message(text)
        if "recipient_name" not in spec:
            recipient = self._recipient_from_message(text)
            if recipient:
                spec["recipient_name"] = recipient
        if "language" not in spec:
            spec["language"] = "Spanish" if self._looks_spanish(lower) else "English"
        if "song_type" not in spec:
            spec["song_type"] = self._song_type(lower)
        if "emotion" not in spec:
            spec["emotion"] = self._emotion(lower)
        if "theme" not in spec:
            spec["theme"] = self._theme(lower)
        if "duration_seconds" not in spec:
            duration = self._duration_from_message(lower)
            if duration:
                spec["duration_seconds"] = duration
        if "voice_style" not in spec:
            voice_style = self._voice_style(lower)
            if voice_style:
                spec["voice_style"] = voice_style
        if "instruments" not in spec:
            instruments = self._instruments(lower)
            if instruments:
                spec["instruments"] = instruments
        if "bpm" not in spec:
            bpm = self._bpm(lower)
            if bpm:
                spec["bpm"] = bpm
        if "key" not in spec and any(word in lower for word in ("c major", "do mayor", "tonalidad")):
            spec["key"] = "C major"
        if "structure" not in spec and any(word in lower for word in ("intro", "coro", "chorus", "puente", "bridge")):
            spec["structure"] = ["intro", "verse_1", "chorus", "verse_2", "bridge", "final_chorus", "outro"]
        if "output_format" not in spec:
            if "mp3" in lower and "wav" in lower:
                spec["output_format"] = "wav+mp3"
            elif "mp3" in lower:
                spec["output_format"] = "mp3"
            elif "wav" in lower:
                spec["output_format"] = "wav"
        return spec

    def compose_user_response(self, qwen_result: dict[str, object]) -> str:
        status = str(qwen_result.get("status", "missing_information"))
        if status == "ready_for_generation":
            return (
                "Ya tengo una especificacion musical completa. Qwen la aprobo para iniciar el pipeline: "
                "primero letra cantable, luego revision tecnica, plan musical y MIDI base."
            )
        questions = [str(item) for item in qwen_result.get("questions_for_user", [])]
        if not questions:
            questions = ["Que detalle emocional o musical quieres ajustar antes de continuar?"]
        return "Para cuidar bien la cancion, necesito afinar esto contigo:\n" + "\n".join(
            f"- {question}" for question in questions
        )

    def friendly_questions(self, missing_fields: list[str]) -> list[str]:
        return [self.FIELD_QUESTION_COPY.get(field, f"Puedes aclarar {field}?") for field in missing_fields]

    def _title_from_message(self, text: str) -> str:
        recipient = self._recipient_from_message(text)
        if recipient:
            return f"Cancion para {recipient}"
        return "Nueva cancion"

    def _recipient_from_message(self, text: str) -> str:
        patterns = [
            r"para\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+)",
            r"a\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""

    def _looks_spanish(self, lower: str) -> bool:
        return any(word in lower for word in ("cancion", "canción", "quiero", "para", "dulce", "cuna"))

    def _song_type(self, lower: str) -> str:
        if any(word in lower for word in ("cuna", "arrullo", "lullaby")):
            return "lullaby"
        if any(word in lower for word in ("cumple", "birthday")):
            return "birthday_song"
        if any(word in lower for word in ("balada", "ballad")):
            return "ballad"
        return "personal_song"

    def _emotion(self, lower: str) -> str:
        if any(word in lower for word in ("tierna", "tierno", "dulce", "suave", "calida", "cálida")):
            return "tender"
        if any(word in lower for word in ("alegre", "feliz")):
            return "joyful"
        if any(word in lower for word in ("nostalg", "triste")):
            return "nostalgic"
        return "warm"

    def _theme(self, lower: str) -> str:
        themes = []
        for word, theme in (
            ("dormir", "sleep"),
            ("sueño", "sleep"),
            ("amor", "love"),
            ("prote", "protection"),
            ("familia", "family"),
        ):
            if word in lower:
                themes.append(theme)
        return ", ".join(dict.fromkeys(themes)) or "love, care, emotional dedication"

    def _duration_from_message(self, lower: str) -> int | None:
        minutes = re.search(r"(\d+)\s*(min|minutos|minute|minutes)", lower)
        if minutes:
            return int(minutes.group(1)) * 60
        seconds = re.search(r"(\d+)\s*(seg|segundos|seconds)", lower)
        if seconds:
            return int(seconds.group(1))
        return None

    def _voice_style(self, lower: str) -> str:
        if "femenina" in lower or "female" in lower:
            return "soft female vocal"
        if "masculina" in lower or "male" in lower:
            return "warm male vocal"
        if "infantil" in lower or "child" in lower:
            return "gentle childlike vocal"
        return ""

    def _instruments(self, lower: str) -> list[str]:
        instruments = []
        for word, instrument in (
            ("piano", "soft piano"),
            ("cuerda", "warm strings"),
            ("strings", "warm strings"),
            ("guitarra", "soft guitar"),
            ("pad", "light ambient pad"),
            ("cajita", "music box"),
        ):
            if word in lower:
                instruments.append(instrument)
        return list(dict.fromkeys(instruments))

    def _bpm(self, lower: str) -> int | None:
        bpm = re.search(r"(\d+)\s*bpm", lower)
        if bpm:
            return int(bpm.group(1))
        if any(word in lower for word in ("muy lenta", "arrulladora", "lento")):
            return 70
        if any(word in lower for word in ("moderada", "medio")):
            return 90
        return None
