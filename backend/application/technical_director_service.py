from __future__ import annotations

from application.creative_agent_service import CreativeAgentService


class TechnicalDirectorService:
    REQUIRED_SPEC_FIELDS = [
        "title",
        "recipient_name",
        "language",
        "song_type",
        "emotion",
        "duration_seconds",
        "bpm",
        "key",
        "voice_style",
        "instruments",
        "structure",
        "output_format",
    ]

    def __init__(self, creative_agent: CreativeAgentService) -> None:
        self.creative_agent = creative_agent

    def validate_song_spec(self, spec: dict[str, object]) -> dict[str, object]:
        normalized = self._normalize(spec)
        missing_fields = self._missing_fields(normalized)
        status = "ready_for_generation" if not missing_fields else "missing_information"
        return {
            "status": status,
            "missing_fields": missing_fields,
            "questions_for_user": self.creative_agent.friendly_questions(missing_fields),
            "song_spec": normalized,
            "approved_by_qwen": status == "ready_for_generation",
        }

    def _normalize(self, spec: dict[str, object]) -> dict[str, object]:
        normalized = dict(spec)
        if "structure" in normalized and isinstance(normalized["structure"], str):
            normalized["structure"] = [
                item.strip().lower().replace(" ", "_")
                for item in str(normalized["structure"]).split(",")
                if item.strip()
            ]
        if "instruments" in normalized and isinstance(normalized["instruments"], str):
            normalized["instruments"] = [
                item.strip()
                for item in str(normalized["instruments"]).split(",")
                if item.strip()
            ]
        if "duration_seconds" in normalized:
            normalized["duration_seconds"] = int(normalized["duration_seconds"])
        if "bpm" in normalized:
            normalized["bpm"] = int(normalized["bpm"])
        return normalized

    def _missing_fields(self, spec: dict[str, object]) -> list[str]:
        missing = []
        for field in self.REQUIRED_SPEC_FIELDS:
            value = spec.get(field)
            if value is None or value == "" or value == []:
                missing.append(field)
        return missing
