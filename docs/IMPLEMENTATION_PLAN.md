# Implementation Plan

> **Registro histórico de sprints 1 a 12.** Los estados «completado» incluyen entregas mock/local y no acreditan generación real ni el recorrido guiado actual. El trabajo pendiente está en [ROADMAPP.md](ROADMAPP.md); el estado ejecutable está en el README de la raíz.

## Sprint 1 - Base ejecutable

Estado: completado.

Objetivos:
- Crear estructura modular Python.
- Mantener `providers`, `explorers` y `builders` desacoplados.
- Crear sistema de carpetas de datos.
- Dejar un menu de consola funcional.
- Evitar dependencias externas y APIs reales.

Entregables:
- Paquete `song_ai`.
- Entrada CLI por `python backend/main.py`.
- Entrada web/API por `python backend/server.py`.
- `StorageManager` para preparar `data/`.
- Modelos base para `AssetDraft`, `MusicalIntent`, `Manifest` y `SongSet`.

## Sprint 2 - Persistencia JSON

Estado: completado.

Objetivos:
- Serializar y leer `manifest.json`.
- Serializar y leer `intent.json`.
- Validar que cada asset preserve intencion instrumental, vocal y lirica.

Entregables iniciales:
- `StorageManager.save_asset_draft`.
- Escritura de `manifest.json`, `intent.json` y `metadata.json`.

## Sprint 3 - Exploradores mock

Estado: completado.

Objetivos:
- Generar drafts mock de instrumental, melodia y letra.
- Guardar assets separados.
- Preparar menu de exploracion sin providers reales.

Entregables iniciales:
- Exploradores mock para instrumental, melodia y letra.
- Opciones de menu para crear y listar drafts.

## Sprint 4 - Curaduria

Estado: completado.

Objetivos:
- Marcar drafts favoritos.
- Listar favoritos.

## Sprint 5 - Set builder

Estado: completado.

Objetivos:
- Crear `set.json`.
- Validar que existan instrumental, melodia y letra antes de crear set.

## Sprint 6 - Sample builder

Estado: completado.

Objetivos:
- Generar preview mock desde el ultimo set valido.
- Mantener el requisito de set antes de sample.

## Sprint 7 - Full song builder mock

Estado: completado.

Objetivos:
- Generar cancion completa mock desde el ultimo sample.
- Bloquear generacion completa si no existe sample valido.

## Sprint 8 - Providers locales

Estado: completado en modo mock/local.

Objetivos:
- Implementar providers locales reemplazables.
- Mantener mocks como fallback ejecutable.

## Sprint 9 - Providers pro

Estado: completado como placeholder sin APIs reales.

Objetivos:
- Registrar providers pro futuros.
- Mantener el sistema ejecutable sin credenciales.

## Sprint 10 - Mezcla

Estado: completado en modo mock/local.

Objetivos:
- Preparar contrato de mezcla.
- Verificar disponibilidad de `ffmpeg`.
- Preparar estructura para stems.

## Sprint 11 - Exportaciones completas

Estado: completado en modo mock/local.

Objetivos:
- Registrar formatos comunes de audio.
- Preparar `exports/manifest.json`.
- Mantener placeholders hasta tener audio real.

## Sprint 12 - Plantillas reutilizables

Estado: completado.

Objetivos:
- Guardar sets como plantillas reutilizables.
- Preservar IDs de instrumental, melodia y letra.
