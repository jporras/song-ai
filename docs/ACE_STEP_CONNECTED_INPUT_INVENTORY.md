# Inventario de inputs ACE-Step conectados

Fecha: 2026-10-08. Alcance: wrapper conectado, no todas las firmas nativas. Contrato: ACE_STEP_CAPABILITIES.md y ACE_STEP_USER_INPUT_ACCEPTANCE.md.

| Inputs del request | Origen y control | Transformación/evidencia |
| --- | --- | --- |
| bpm, key_scale, time_signature, vocal_language, audio_duration | Ficha editable: BPM, tonalidad, compás, idioma y duración | Proyección y aliases declarados en input_trace |
| captions | Deseos musicales de MusicSpec | caption_join, fuentes de composición registradas; no notas DSP ejecutables |
| lyrics | Documento de letra/revisión o preview identificado | lyrics_identity; preview no confirmado no acredita USER |
| task_type, generation_api, lm_model_path | Acción y ruta elegidas en UI | LM solo text2music; incompatibilidad bloqueada sin cambiar elección |
| seed, inference_steps, guidance_scale, shift | Controles editables/delegación explícita | Valor USER o perfil declarado; límites backend |
| src_audio | source_artifact_id elegido en proyecto | Ruta SYSTEM; inspector verifica archivo; traza ID/checksum, hash del plan |
| reference_audio | reference_artifact_id opcional | Ruta SYSTEM; inspector verifica archivo; traza ID/checksum; no clonación |
| instruction | Pistas objetivo e instrucción revisable | lego/extract una pista; complete una o más; no autoguardado |
| repainting_start, repainting_end | Intervalo en segundos | Validación dentro de duración; -1 declarado para final |
| audio_cover_strength | Control Cover | Rango 0–1; no garantía porcentual de fidelidad |
| chunk_mask_mode | Compilador/SYSTEM | Regla SYSTEM explícita, no decisión atribuida al usuario |

Los 21 nombres emitidos se controlan mediante tests/test_ace_step_user_input_acceptance.py; argumentos nuevos sin regla de traza se rechazan. El modelo/configuración, target_tracks e IDs de artefactos son decisiones/contexto conservados; no inventar argumentos nativos adicionales.

## Evidencia y pendientes

2026-10-08: 4 pruebas aceptación (incluyen 13 combinaciones compatibles), 6 compilador, 6 revisión de plan aprobadas. Traces de audio verificado dejan de indicar pending: vinculan ID seleccionado, sha256 y ruta inspeccionada antes del hash. Caso WAV sintético registra checksum y detecta sustitución antes de aprobar. No acredita calidad musical ni ejecución real ACE-Step.

Pendiente S06-02: flujo de importación de nuevas fuentes y referencias (UI/puerto/adaptador/persistencia), cobertura extremo a extremo de todos los campos desde UI y contexto activo. Actualmente las opciones usan artefactos registrados del proyecto. S06-04/S10 conservan validación instalada y generación/escucha reales por modo.

## Importación implementada

WAV PCM hasta 64 MiB: permiso explícito, archivo original por UUID, registro en SQLite con checksum y evidencia, selección posterior por nombre original. Backend y upload UI QA comprobados; la cobertura integral de selección→request permanece pendiente. Otros formatos requieren conversión externa; no se anuncia soporte MP3 de importación.

## Recorrido integrado local verificado

2026-10-08: upload QA anterior seguido por selección UI de fuente/referencia, guardado pendiente USER, confirmación y plan Cover. ID y checksum preservados, fuerza 0,75. Traza separa elección USER del artefacto y ruta SYSTEM; recompilación API verificada tras corregir procedencia. S06-02 verificación local completada; aceptación y generación real permanecen pendientes.
