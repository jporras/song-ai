# Propuesta completa de letra — verificación 2026-10-08

## Alcance

S03-04: propuesta desde MusicSpec, revisión explícita en Letra y trazabilidad del guardado. Base QA `data/qa_consolidation_final_20261007`, servidor aislado 8015 sin autostart LLM ni monitor. Ninguna modificación a la base productiva; no inferencia real ni audio.

## Correcciones

- Backend reconoce sección bloqueada, líneas protegidas y dirección bloqueada antes de inferencia.
- Formato requiere Markdown por secciones, texto en cada sección y límite de 4096 caracteres incluyendo salto final; solicita ese límite al provider. No acepta explicación antes de primera sección.
- Respuesta tardía no carga propuesta si cambió ficha o borrador.
- Production dirige la acción Letra al editor para revisión y guardado explícito.
- Task fallida de letra comunica fallo de propuesta, sin llamarlo compilación.
- Traza registra resultado accepted o user_modified_or_editor_normalized junto con texto propuesto, hash guardado y transformaciones.

## Playwright MCP

Doble HTTP para respuesta de generación; tarea fixture persistida y guardado/consulta/recarga reales en SQLite QA. Fixture identificada `task_qa_full_lyrics_20261008`, mode=qa_fixture, provider_executed=false; no acredita ejecución Gemma.

1. Proponer mantiene revisión `spec_rev_30e67b82b0bd` y borrador sin cambios.
2. Incorporar deja dos secciones, dirty=true y misma revisión, sin persistencia.
3. Guardar genera revisión `spec_rev_986eddb97ba6`, dirty=false; letra y traza pertenecen a esa revisión.
4. Consulta API confirma explicit_user_save y transformaciones markdown_to_editor_sections_v1/reviewed_phase_save_v1.
5. Recarga conserva dos secciones y texto guardado.
6. Descartar nueva propuesta conserva texto y estado guardado.
7. Dirección protegida deshabilita solicitud de reemplazo completo.
8. Edición durante respuesta tardía se conserva; propuesta descartada con explicación.
9. Acción LYRICS_GENERATION de Production navega a /lyrics.

Sin pageerror durante proponer/incorporar/guardar. Un primer intento del harness leyó data.json_spec en vez de data.spec.json_spec; corregido sin cambio de producto. Se conservaron artefactos QA y su historial. Navegador/servidor cerrados al terminar.

## Verificación agrupada

21 pruebas backend aprobadas: full_lyrics_proposal, music_spec_phases, local_lyrics_access y local_lyrics_review. Duración 39,971 s. Build Vite y compileall correctos.

## Pendiente

Inferencia real de Gemma y evaluación de fidelidad creativa; audio real y aceptación del usuario. S03-04 sigue parcial por consumidores históricos restantes; global 65,7%.
