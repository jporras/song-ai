"""Explicit musical metadata patches on the existing SQLite revision pipeline."""
import math
import re
from application.ace_step_configuration import EditAceStepConfiguration
from application.ace_step_plan_compiler import AceStepPlanCompiler
from application.song_specification_service import SongSpecificationService


class EditMusicSpec(EditAceStepConfiguration):
    technical_review_mode = "musical_metadata_deterministic_edit"
    MUSICAL_FIELDS = {"bpm", "key", "time_signature", "language", "duration_seconds"}
    CREATIVE_FIELDS = {field for group in SongSpecificationService.CATALOG
                       for field, _, control, _, _ in group['fields']
                       if control in {'text', 'choice', 'multi_choice', 'ordered_list', 'list'}
                       and field not in SongSpecificationService.ENGINE_FIELDS} - MUSICAL_FIELDS
    LIST_FIELDS = {field for group in SongSpecificationService.CATALOG
                   for field, _, control, _, _ in group['fields']
                   if control in {'multi_choice', 'ordered_list', 'list'}} - set(SongSpecificationService.ENGINE_FIELDS)
    REQUIRED_FIELDS = {field for group in SongSpecificationService.CATALOG
                       for field, _, _, required, _ in group['fields'] if required}

    def editable_fields(self):
        return super().editable_fields() | self.MUSICAL_FIELDS | self.CREATIVE_FIELDS

    def execute(self, song_id, request):
        project = self.store.get_song_project(song_id)
        spec = (project or {}).get('spec', {}).get('json_spec', {})
        edits = request.get('values')
        for field, value in (edits.items() if isinstance(edits, dict) else []):
            if spec.get('_provenance', {}).get(field, {}).get('locked') is True and spec.get(field) != value:
                raise ValueError('Esta decision esta bloqueada; desbloqueala explicitamente antes de cambiarla.')
        return super().execute(song_id, request)

    def validate_edits(self, edits: dict) -> None:
        for field, value in edits.items():
            if field in self.CREATIVE_FIELDS:
                if field in self.LIST_FIELDS:
                    if not isinstance(value, list) or len(value) > 100 or any(not isinstance(item, str) or not item.strip() or len(item) > 500 for item in value):
                        raise ValueError(f'Revisa {field}: lista de textos no vacios, hasta 100 elementos.')
                    if field in self.REQUIRED_FIELDS and not value:
                        raise ValueError(f'Revisa {field}: la lista es obligatoria.')
                elif not isinstance(value, str) or len(value) > 4000 or (field in self.REQUIRED_FIELDS and not value.strip()):
                    raise ValueError(f'Revisa {field}: texto valido, hasta 4000 caracteres.')
                if field == 'output_format' and value not in {'mp3', 'wav', 'flac'}:
                    raise ValueError('Selecciona mp3, wav o flac como formato principal.')
                continue
            if field not in self.MUSICAL_FIELDS:
                continue
            if field in {"bpm", "duration_seconds"}:
                low, high = (30, 300) if field == "bpm" else (10, 600)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                    raise ValueError(f"Revisa {field}: valor entre {low} y {high}.")
                if field == "bpm" and int(value) != value:
                    raise ValueError("BPM debe ser entero; no se redondeara silenciosamente.")
            elif not isinstance(value, str) or not value.strip():
                raise ValueError(f"Revisa {field}: selecciona un valor valido.")
            elif field == "key" and not re.fullmatch(r"[A-Ga-g][#b]?(?:\s+(?:major|minor)|m)?", value.strip(), re.IGNORECASE):
                raise ValueError("Revisa la tonalidad, por ejemplo Am o C Major.")
            elif field == "time_signature" and value not in AceStepPlanCompiler.SIGNATURES and value not in {"2", "3", "4", "6"}:
                raise ValueError("Compas sin traduccion conectada a ACE-Step.")
            elif field == "language" and not re.fullmatch(r"[a-z]{2}", AceStepPlanCompiler.LANGUAGES.get(value.strip().lower(), value.strip().lower())):
                raise ValueError("Idioma sin codigo vocal valido.")
