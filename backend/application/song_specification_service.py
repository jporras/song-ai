from __future__ import annotations

from typing import Any


class SongSpecificationService:
    """Builds the user-facing catalog and completion view for a song spec."""

    SCHEMA_VERSION = "1.1"
    QUALITY_FIELDS = {"duration_tolerance_seconds"}

    ENGINE_FIELDS = {
        "task_type": ("text2music", "cover", "repaint", "lego", "extract", "complete"),
        "ace_step_config": ("acestep-v15-base", "acestep-v15-turbo"),
        "source_artifact_id": (), "src_audio": (), "instruction": (),
        "target_tracks": (), "repainting_start": (), "repainting_end": (),
        "audio_cover_strength": (),
    }

    CATALOG: tuple[dict[str, Any], ...] = (
        {
            "id": "ace_step",
            "label": "Que quieres hacer con el audio",
            "description": "Entradas de ACE-Step; un plan preparado no demuestra generacion verificada.",
            "fields": (
                ("task_type", "Accion musical", "choice", False, "Crear, transformar, corregir, añadir, separar o completar audio."),
                ("ace_step_config", "Modelo de generacion", "choice", False, "Base admite las seis tareas; su carga y audio aun requieren verificacion."),
                ("source_artifact_id", "Audio del proyecto", "artifact", False, "Selecciona un audio registrado en este proyecto para editarlo."),
                ("src_audio", "Archivo fuente", "informational", False, "Debe coincidir con el artefacto seleccionado; no es una referencia de voz."),
                ("instruction", "Operacion sobre el audio", "text", False, "Indica las pistas objetivo; la traduccion tecnica debe revisarse."),
                ("target_tracks", "Parte a añadir o separar", "multi_choice", False, "Lego y Extract trabajan sobre una sola pista objetivo."),
                ("repainting_start", "Inicio de la parte", "seconds", False, "Segundos desde el comienzo del audio fuente."),
                ("repainting_end", "Final de la parte", "seconds", False, "Segundos del final; -1 significa hasta el final del audio."),
                ("audio_cover_strength", "Conservacion del audio fuente", "number", False, "Valor de 0 a 1 para Cover; no garantiza notas o identidad de voz."),
            ),
        },
        {
            "id": "idea",
            "label": "Idea y estilo",
            "description": "Que debe transmitir la cancion y para quien se crea.",
            "fields": (
                ("creative_brief", "Idea de la cancion", "text", True, "Describe la historia, ocasion o emocion en tus palabras."),
                ("title", "Titulo", "text", True, "Puedes usar un titulo temporal y cambiarlo despues."),
                ("recipient_name", "Destinatario", "text", False, "Solo hace falta cuando la cancion esta dedicada a alguien."),
                ("language", "Idioma", "choice", True, "Idioma principal de la letra y pronunciacion."),
                ("song_type", "Tipo o estilo", "choice", True, "Por ejemplo: balada, pop, nana o folk."),
                ("emotion", "Emocion principal", "choice", True, "La sensacion que debe conservar todo el arreglo."),
                ("theme", "Tema", "text", False, "La idea narrativa que desarrollara la letra."),
                ("duration_seconds", "Duracion", "duration", True, "La IA puede proponerla segun la estructura."),
            ),
        },
        {
            "id": "instrumental",
            "label": "Base musical y arreglo",
            "description": "Ritmo, armonia, instrumentos, estructura y energia.",
            "fields": (
                ("bpm", "Velocidad", "bpm", True, "Pulsos por minuto; tambien puedes elegir lenta, media o rapida."),
                ("key", "Tonalidad", "choice", True, "La IA propone una tonalidad compatible con la voz y el ambiente."),
                ("time_signature", "Compas", "choice", False, "Organiza el pulso, por ejemplo 4/4 o 6/8."),
                ("groove", "Movimiento ritmico", "choice", False, "Define si el pulso se siente recto, balanceado o con swing."),
                ("instruments", "Instrumentos", "multi_choice", True, "Selecciona los colores principales de la base."),
                ("structure", "Estructura", "ordered_list", True, "Orden de intro, versos, coros, puente y cierre."),
                ("dynamic_arc", "Evolucion de energia", "text", False, "Explica donde la cancion crece, descansa y termina."),
            ),
        },
        {
            "id": "voice",
            "label": "Melodia y voz",
            "description": "Como se canta, que rango usa y que identidad vocal se espera.",
            "fields": (
                ("voice_style", "Tipo de voz", "choice", True, "Caracter y color de la voz principal."),
                ("vocal_range", "Rango vocal", "choice", False, "La IA puede ajustarlo para que la melodia sea cantable."),
                ("vocal_expression", "Interpretacion", "text", False, "Energia, fraseo, articulacion y expresion deseada."),
                ("pronunciation", "Pronunciacion", "text", False, "Indicaciones para nombres, acentos y claridad."),
                ("vocal_layers", "Capas vocales", "multi_choice", False, "Voz principal, armonias, dobles o coros si el provider los soporta."),
                ("voice_profile_id", "Voz personalizada", "voice_profile", False, "Opcional y disponible solo con un provider de canto compatible."),
            ),
        },
        {
            "id": "lyrics",
            "label": "Letra",
            "description": "Tema, narrador, tono, secciones y contenido que debe conservarse.",
            "fields": (
                ("lyrical_tone", "Tono de la letra", "choice", False, "Por ejemplo: tierno, alegre, intimo o esperanzador."),
                ("narrator", "Quien cuenta la historia", "choice", False, "Primera persona, tercera persona o voz compartida."),
                ("required_phrases", "Frases o nombres obligatorios", "list", False, "Contenido que debe aparecer y cuya pronunciacion se revisara."),
                ("excluded_content", "Contenido que se debe evitar", "list", False, "Palabras, temas o recursos que no deben aparecer."),
                ("rhyme_preference", "Preferencia de rima", "choice", False, "La rima puede ser libre, suave o marcada."),
            ),
        },
        {
            "id": "production",
            "label": "Produccion y entrega",
            "description": "Como se generara, revisara y exportara el resultado.",
            "fields": (
                ("production_route", "Ruta de produccion", "capability", False, "Cancion integrada o stems, segun capacidades reales."),
                ("sample_duration_seconds", "Duracion del sample", "duration", False, "Fragmento suficiente para revisar voz, estilo y balance."),
                ("mix_balance", "Balance de voz y musica", "choice", False, "Indica si la voz debe sentirse al frente o integrada."),
                ("output_format", "Formato de entrega", "choice", True, "Formato principal solicitado; otros se ofrecen si estan verificados."),
                ("quality_profile", "Perfil de calidad", "choice", False, "Criterios tecnicos y de escucha aplicados al resultado."),
                ("duration_tolerance_seconds", "Margen aceptable de duracion", "number", False, "Segundos de diferencia aceptados; sin confirmacion no se declara cumplida la duracion."),
            ),
        },
    )

    def catalog(self, spec: dict[str, object] | None = None) -> dict[str, object]:
        values = dict(spec or {})
        provenance = dict(values.get("_provenance", {}))
        groups: list[dict[str, object]] = []
        totals = {"total": 0, "required": 0, "decided": 0, "required_decided": 0}
        for group in self.CATALOG:
            fields = []
            for key, label, control, required, help_text in group["fields"]:
                value = values.get(key)
                task = values.get("task_type", "text2music")
                applicable = True
                if key in {"source_artifact_id", "src_audio"}:
                    applicable = task != "text2music"
                elif key in {"instruction", "target_tracks"}:
                    applicable = task in {"lego", "extract", "complete"}
                elif key in {"repainting_start", "repainting_end"}:
                    applicable = task in {"repaint", "lego"}
                elif key == "audio_cover_strength":
                    applicable = task == "cover"
                decided = value not in (None, "", [])
                totals["total"] += 1
                totals["decided"] += int(decided)
                totals["required"] += int(required)
                totals["required_decided"] += int(required and decided)
                fields.append(
                    {
                        "id": key,
                        "label": label,
                        "control": control,
                        "required_for_spec": required,
                        "help": help_text,
                        "value": value,
                        "coverage_status": "decided" if decided else "to_review",
                        "source": str(dict(provenance.get(key, {})).get("source", "saved_spec" if decided else "not_set")),
                        "source_note": str(dict(provenance.get(key, {})).get("note", "")),
                        "applicable": applicable,
                        "required_for_task": applicable and key in {
                            "source_artifact_id", "src_audio", "instruction", "target_tracks"},
                        "options": list(self.ENGINE_FIELDS.get(key, ())),
                        "execution_status": "candidate_plan_only" if key in self.ENGINE_FIELDS else "specification_requirement",
                    }
                )
            groups.append(
                {
                    "id": group["id"],
                    "label": group["label"],
                    "description": group["description"],
                    "fields": fields,
                    "decided": sum(1 for item in fields if item["coverage_status"] == "decided"),
                    "total": len(fields),
                }
            )
        return {"schema_version": self.SCHEMA_VERSION, "groups": groups, "summary": totals}

    def compilation_status(self, missing_fields: list[str]) -> str:
        return "needs_information" if missing_fields else "complete_for_stage"

    def add_provenance(
        self,
        existing_spec: dict[str, object] | None,
        candidate_spec: dict[str, object],
        user_message: str,
    ) -> dict[str, object]:
        result = dict(candidate_spec)
        existing = dict(existing_spec or {})
        provenance = dict(existing.get("_provenance", {}))
        explicit_fields = {
            "creative_brief", "recipient_name", "duration_seconds", "voice_style", "instruments",
            "bpm", "key", "structure", "output_format",
        }
        interpreted_fields = {"title", "language", "song_type", "emotion", "theme"}
        for key, value in result.items():
            if key.startswith("_") or existing.get(key) == value:
                continue
            if key == "creative_brief":
                source = "user_message"
                note = "Texto original del ultimo mensaje del usuario."
            elif key in explicit_fields:
                source = "extracted_from_user_message"
                note = "Valor extraido por reglas; debe revisarse antes de confirmar la especificacion."
            elif key in interpreted_fields:
                source = "ai_interpretation"
                note = "Interpretacion o propuesta derivada del mensaje; no es una cita literal del usuario."
            else:
                source = "generated_proposal"
                note = "Propuesta tecnica pendiente de revision."
            provenance[key] = {"source": source, "note": note, "message": user_message}
        result["_provenance"] = provenance
        return result
