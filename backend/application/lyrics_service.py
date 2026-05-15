from __future__ import annotations

from pathlib import Path

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class LyricsService:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def generate(self, song_id: str, spec: dict[str, object]) -> dict[str, object]:
        sections = self._sections_from_spec(spec)
        lyrics_payload = {
            "song_id": song_id,
            "title": str(spec.get("title", "Nueva cancion")),
            "language": str(spec.get("language", "Spanish")),
            "structure": [section["id"] for section in sections],
            "sections": sections,
            "cantable": True,
            "notes": "Letra generada por Gemma para canto; pendiente revision tecnica de Qwen.",
        }
        markdown = self.to_markdown(lyrics_payload)
        return self.write(song_id, lyrics_payload, markdown, "Letra cantable generada por Gemma.")

    def get(self, song_id: str) -> dict[str, object]:
        lyrics_json_path, lyrics_md_path = self.paths(song_id)
        if not lyrics_md_path.exists():
            raise ValueError("Este proyecto aun no tiene lyrics.md profesional.")
        payload = self.storage.read_json(lyrics_json_path) if lyrics_json_path.exists() else {}
        return {
            "song_id": song_id,
            "lyrics": payload,
            "markdown": lyrics_md_path.read_text(encoding="utf-8"),
            "lyrics_json_path": str(lyrics_json_path),
            "lyrics_md_path": str(lyrics_md_path),
        }

    def update_markdown(self, song_id: str, content: str) -> dict[str, object]:
        if not content.strip():
            raise ValueError("La letra no puede quedar vacia.")
        existing = self.get(song_id)
        lyrics_payload = self.from_markdown(
            song_id=song_id,
            title=str(dict(existing.get("lyrics", {})).get("title", "Letra editada")),
            markdown=content,
        )
        return self.write(song_id, lyrics_payload, content.rstrip() + "\n", "Letra editada por el usuario.")

    def write(
        self,
        song_id: str,
        lyrics_payload: dict[str, object],
        markdown: str,
        message: str,
    ) -> dict[str, object]:
        lyrics_json_path, lyrics_md_path = self.paths(song_id)
        self.storage.write_json(lyrics_json_path, lyrics_payload)
        lyrics_md_path.parent.mkdir(parents=True, exist_ok=True)
        lyrics_md_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
        json_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_lyrics_json",
            song_id=song_id,
            phase=SongPhase.LYRICS_GENERATION.value,
            artifact_type="lyrics_json",
            file_path=str(lyrics_json_path),
            metadata={"sections": list(lyrics_payload.get("structure", [])), "editable": True},
        )
        md_artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_lyrics_md",
            song_id=song_id,
            phase=SongPhase.LYRICS_GENERATION.value,
            artifact_type="lyrics_markdown",
            file_path=str(lyrics_md_path),
            metadata={"editable": True, "source": "gemma_or_user"},
        )
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.LYRICS_GENERATION.value,
            status=SongPhaseStatus.COMPLETED.value,
            progress=100,
            message=message,
            active_model="gemma",
            payload={"lyrics_json": str(lyrics_json_path), "lyrics_md": str(lyrics_md_path)},
            artifact_id=str(md_artifact["artifact_id"]),
        )
        project = self.storage.update_song_project_phase(
            song_id,
            SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            SongPhaseStatus.READY.value,
        )
        return {
            "project": project,
            "lyrics": lyrics_payload,
            "markdown": markdown.rstrip() + "\n",
            "artifacts": [json_artifact, md_artifact],
        }

    def paths(self, song_id: str) -> tuple[Path, Path]:
        project_dir = self.storage.data_dir / "projects" / song_id
        return project_dir / "lyrics.json", project_dir / "lyrics.md"

    def to_markdown(self, lyrics_payload: dict[str, object]) -> str:
        lines = [f"# {lyrics_payload.get('title', 'Letra')}", ""]
        for section in list(lyrics_payload.get("sections", [])):
            section_dict = dict(section)
            lines.append(f"## {section_dict.get('label', section_dict.get('id', 'section'))}")
            lines.extend(str(line) for line in list(section_dict.get("lines", [])))
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def from_markdown(self, song_id: str, title: str, markdown: str) -> dict[str, object]:
        sections: list[dict[str, object]] = []
        current: dict[str, object] | None = None
        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if line.startswith("# "):
                title = line.lstrip("#").strip()
                continue
            if line.startswith("## "):
                if current is not None:
                    sections.append(current)
                label = line.lstrip("#").strip()
                current = {"id": self._section_id(label), "label": label, "lines": []}
                continue
            if line and current is not None:
                current_lines = current["lines"]
                if isinstance(current_lines, list):
                    current_lines.append(line)
        if current is not None:
            sections.append(current)
        if not sections:
            sections = [{"id": "verse_1", "label": "Verse 1", "lines": [markdown.strip()]}]
        return {
            "song_id": song_id,
            "title": title,
            "language": "Spanish",
            "structure": [str(section["id"]) for section in sections],
            "sections": sections,
            "cantable": True,
            "notes": "Letra actualizada desde editor.",
        }

    def _sections_from_spec(self, spec: dict[str, object]) -> list[dict[str, object]]:
        recipient = str(spec.get("recipient_name", "mi amor"))
        emotion = str(spec.get("emotion", "tender"))
        theme = str(spec.get("theme", "love, care"))
        structure = list(spec.get("structure", [])) or [
            "intro",
            "verse_1",
            "chorus",
            "verse_2",
            "bridge",
            "final_chorus",
            "outro",
        ]
        sections = []
        for section_id in [str(item) for item in structure]:
            sections.append(
                {
                    "id": section_id,
                    "label": self._section_label(section_id),
                    "lines": self._lines_for(section_id, recipient, emotion, theme),
                }
            )
        return sections

    def _lines_for(self, section_id: str, recipient: str, emotion: str, theme: str) -> list[str]:
        if "intro" in section_id:
            return [f"Duermete suave, {recipient},", "la noche empieza a cantar."]
        if "chorus" in section_id:
            return [f"{recipient}, mi luz pequena,", "cierro el cielo alrededor,", "cada estrella te acompana,", "cada latido es amor."]
        if "bridge" in section_id:
            return ["Si la sombra se despierta,", "mi voz te vuelve a abrazar,", "con ternura y calma abierta,", "todo vuelve a descansar."]
        if "outro" in section_id:
            return [f"Suena bonito, {recipient},", "manana el sol vendra."]
        return [
            f"{recipient}, respira despacito,",
            f"mi cancion te cuida en {emotion},",
            "va dejando en tu camita,",
            f"{theme} para sonar.",
        ]

    def _section_label(self, section_id: str) -> str:
        return section_id.replace("_", " ").title()

    def _section_id(self, label: str) -> str:
        return label.strip().lower().replace(" ", "_")
