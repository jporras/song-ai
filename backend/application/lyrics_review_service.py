from __future__ import annotations

from collections import Counter
from pathlib import Path

from core.storage import StorageManager
from models.song_workflow import SongPhase, SongPhaseStatus


class LyricsReviewService:
    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    def review(self, song_id: str, spec: dict[str, object], lyrics_payload: dict[str, object]) -> dict[str, object]:
        sections = [dict(section) for section in list(lyrics_payload.get("sections", []))]
        issues = self._issues(spec, sections)
        approved = not issues
        review_payload = {
            "song_id": song_id,
            "approved_by_qwen": approved,
            "status": "approved" if approved else "needs_revision",
            "issues": issues,
            "recommendations_for_gemma": self._recommendations(issues),
            "metrics": self._metrics(sections),
        }
        review_path = self.storage.data_dir / "projects" / song_id / "lyrics_approved.json"
        self.storage.write_json(
            review_path,
            {
                **review_payload,
                "lyrics": lyrics_payload if approved else None,
            },
        )
        artifact = self.storage.create_song_artifact(
            artifact_id=f"{song_id}_lyrics_approved",
            song_id=song_id,
            phase=SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            artifact_type="lyrics_approved_json",
            file_path=str(Path(review_path)),
            metadata={"approved_by_qwen": approved, "issue_count": len(issues)},
        )
        if approved:
            project = self.storage.update_song_project_phase(
                song_id,
                SongPhase.MUSIC_PLAN_GENERATION.value,
                SongPhaseStatus.READY.value,
            )
            status = SongPhaseStatus.COMPLETED.value
            progress = 100
            message = "El director tecnico aprobo la letra: estructura, repeticion y duracion son compatibles con la especificacion."
        else:
            project = self.storage.update_song_project_phase(
                song_id,
                SongPhase.LYRICS_GENERATION.value,
                SongPhaseStatus.WAITING_USER_INPUT.value,
            )
            status = SongPhaseStatus.WAITING_USER_INPUT.value
            progress = 60
            message = "El director tecnico encontro ajustes necesarios. Gemma debe ayudar a corregir la letra antes de continuar."
        self.storage.create_song_event(
            song_id=song_id,
            phase=SongPhase.LYRICS_TECHNICAL_REVIEW.value,
            status=status,
            progress=progress,
            message=message,
            active_model="qwen",
            payload=review_payload,
            artifact_id=str(artifact["artifact_id"]),
        )
        return {
            "project": project,
            "review": review_payload,
            "artifact": artifact,
        }

    def _issues(self, spec: dict[str, object], sections: list[dict[str, object]]) -> list[dict[str, object]]:
        issues: list[dict[str, object]] = []
        section_ids = [str(section.get("id", "")).lower() for section in sections]
        line_count = sum(len(list(section.get("lines", []))) for section in sections)
        duration_seconds = int(spec.get("duration_seconds", 120))
        expected_min_lines = max(8, duration_seconds // 18)
        required_markers = ["verse", "chorus"]

        if len(sections) < 4:
            issues.append(
                {
                    "code": "too_few_sections",
                    "message": "La letra necesita mas secciones para sentirse como cancion completa.",
                    "severity": "high",
                }
            )
        for marker in required_markers:
            if not any(marker in section_id for section_id in section_ids):
                issues.append(
                    {
                        "code": f"missing_{marker}",
                        "message": f"Falta una seccion tipo {marker}.",
                        "severity": "high",
                    }
                )
        if line_count < expected_min_lines:
            issues.append(
                {
                    "code": "too_short_for_duration",
                    "message": f"La letra tiene {line_count} lineas y parece corta para {duration_seconds} segundos.",
                    "severity": "medium",
                }
            )
        repeated_lines = self._repeated_lines(sections)
        if repeated_lines:
            issues.append(
                {
                    "code": "excessive_repetition",
                    "message": "Hay lineas repetidas en exceso que pueden hacer la cancion monotona.",
                    "severity": "medium",
                    "lines": repeated_lines,
                }
            )
        return issues

    def _metrics(self, sections: list[dict[str, object]]) -> dict[str, object]:
        lines = self._all_lines(sections)
        return {
            "section_count": len(sections),
            "line_count": len(lines),
            "unique_line_count": len(set(line.lower() for line in lines)),
        }

    def _recommendations(self, issues: list[dict[str, object]]) -> list[str]:
        if not issues:
            return ["La letra puede pasar al plan musical tecnico."]
        recommendations = []
        codes = {str(issue["code"]) for issue in issues}
        if "too_few_sections" in codes:
            recommendations.append("Agregar intro, verso, coro, segundo verso, puente y outro.")
        if "missing_verse" in codes:
            recommendations.append("Agregar al menos un verso narrativo con imagenes concretas.")
        if "missing_chorus" in codes:
            recommendations.append("Agregar un coro memorable, cantable y no demasiado largo.")
        if "too_short_for_duration" in codes:
            recommendations.append("Extender la letra para que respire mejor con la duracion aprobada.")
        if "excessive_repetition" in codes:
            recommendations.append("Reducir repeticiones y variar imagenes sin romper la intencion emocional.")
        return recommendations

    def _repeated_lines(self, sections: list[dict[str, object]]) -> list[str]:
        counter = Counter(line.lower() for line in self._all_lines(sections))
        return [line for line, count in counter.items() if count > 2]

    def _all_lines(self, sections: list[dict[str, object]]) -> list[str]:
        lines: list[str] = []
        for section in sections:
            for line in list(section.get("lines", [])):
                clean = str(line).strip()
                if clean:
                    lines.append(clean)
        return lines
