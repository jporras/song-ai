# Technical Specification

> **Documento histórico.** Conserva el diseño inicial; sus apartados sobre Docker y SQLite como índice de JSON no describen la arquitectura operativa actual. Para implementar, consultar [el mapa de documentación](README.md), [el flujo de información](PHASE_INFORMATION_FLOW.md) y el README de la raíz.

# Lenguaje

Python 3.11+

---

# Arquitectura

Arquitectura modular basada en providers.

La aplicacion evoluciona a arquitectura hexagonal:
- `application/`: casos de uso y servicios de aplicacion.
- `core/`, `models/`, `builders`, `providers`: dominio y puertos internos.
- `adapters/http/`: adaptador FastAPI para exponer API.
- `adapters/sqlite/`: persistencia SQLite para indexar rutas de configuraciones JSON.
- SQLite tambien indexa sets para consulta desde UI y gestion futura por IA.
- `frontend/`: interfaz Vue construida con Vite.
- Docker ejecuta backend y frontend en un unico contenedor con Python y Vue (Node.js).

La vision completa del sistema multi-modelo esta definida en `docs/MULTI_MODEL_MASTER_SPEC.md`.

---

# Arquitectura Multi-Modelo

El sistema debe funcionar como un estudio musical IA compuesto por modelos especializados.

Roles principales:
- Assistant Model: conversa con el usuario y guia el flujo.
- Intent Extractor: convierte conversacion en estructura, valida faltantes y genera metadata.
- Music Providers: generan instrumentales, variaciones, stems y renders.
- Voice Providers: generan voz guia, melodia vocal y voces finales.
- Lyrics Providers: generan o adaptan letras y placeholders.
- Audio Pipeline: mezcla, mastering, stems y exportacion.

Los modelos no deben comunicarse directamente entre si por prompts encadenados. Deben comunicarse por:
- SQLite,
- tasks,
- estados,
- `intent.json`,
- `manifest.json`,
- `set.json`.

La base de datos es la fuente activa de trabajo. Los JSON son snapshots/exportaciones regenerables.

---

# ModelOrchestrator

Debe existir un `ModelOrchestrator`.

Responsabilidades:
- activar y desactivar modelos,
- controlar memoria RAM,
- cargar modelos bajo demanda,
- descargar modelos al terminar,
- manejar handoffs,
- registrar tareas,
- registrar progreso,
- suspender y reactivar el assistant,
- persistir resultados en DB/JSON.

Estado actual:
- existe una primera implementacion mock para validar contratos.
- registra `tasks` y `model_runs` en SQLite.
- registra `project_events` como historico de pasos por proyecto/cancion.
- expone endpoints para estado, listado y simulacion de handoff.
- no carga modelos reales todavia.

Restriccion inicial:
- asumir equipos con 16 GB RAM,
- mantener solo un modelo pesado activo a la vez,
- no depender de memoria interna del modelo como fuente de estado.

---

# Handoff Entre Modelos

Flujo base:

```text
Assistant activo
  -> pide confirmacion
  -> se suspende
  -> ModelOrchestrator carga modelo especializado
  -> modelo especializado procesa
  -> resultado se persiste en SQLite/JSON
  -> modelo especializado se descarga
  -> assistant retoma conversacion
```

La UI debe mostrar:
- modelo activo,
- tarea actual,
- progreso,
- estado de suspension del assistant,
- posibilidad de cancelar.

---

# Estructura de carpetas

backend/
├── main.py
├── .env
├── requirements.txt
├── config/
├── core/
├── explorers/
├── builders/
├── providers/
├── audio/
├── models/
└── utils/

docs/

tests/

---

# Carpetas de datos

data/
├── drafts/
│   ├── instrumentals/
│   ├── melodies/
│   └── lyrics/
│
├── sets/
├── samples/
├── songs/
└── templates/

frontend/
└── src/
---

# Providers

## MusicProvider

Responsable de:
- generar instrumentales,
- generar stems,
- generar soundtrack final.

Implementaciones:
- LocalMusicProvider
- ProMusicProvider

---

## VoiceProvider

Responsable de:
- voz preview,
- voz final,
- guía vocal.

Implementaciones:
- LocalVoiceProvider
- ElevenLabsProvider

---

## LyricsProvider

Responsable de:
- letras dinámicas,
- placeholders,
- variaciones.

Implementaciones:
- LocalLyricsProvider
- OpenAILyricsProvider

---

# Assets

## AssetDraft

Representa:
- instrumental,
- melodía,
- letra.

Debe tener:
- manifest.json,
- intent.json,
- metadata,
- files.

---

# SongSet

Representa:
- proyecto musical basado en una combinacion temporal de assets.

Incluye:
- project_name,
- created_at,
- description,
- instrumental_id,
- melody_id,
- lyrics_id,
- compatibility_data.

Persistencia:
- `data/sets/<set_id>/set.json` conserva la configuracion completa.
- SQLite indexa el set para que la UI lo liste como proyecto y pueda mostrar su configuracion cuando el usuario lo pida.
- La API permite crear sets con `project_name` y `description` desde `POST /api/sets`.
- La asistencia IA debe recordar que un set solo puede avanzar a sample/cancion completa cuando existen los tres drafts base: instrumental, melodia y letra.
- La API permite exportar sets desde SQLite hacia JSON con `POST /api/sets/export`; SQLite es la fuente de trabajo y el archivo JSON se sobrescribe si ya existe.
- La UI debe incluir una zona persistente de asistencia, como footer, para sugerir el siguiente paso correcto segun el estado de drafts y sets.

---

# Fases Del Pipeline

El pipeline completo se divide en:

0. Configuracion.
1. Conversacion inicial.
2. Extraccion estructurada.
3. Exploracion de assets.
4. Curaduria.
5. Ensamble de set.
6. Sample / preview.
7. Ajustes.
8. Preproduccion final.
9. Aprobacion del usuario.
10. Produccion completa local.
11. Produccion completa pro.
12. Mezcla y mastering.
13. Exportacion.
14. Plantilla reutilizable.

Reglas:
- sin aprobacion de set/sample no se puede generar produccion final.
- la produccion pro no rehace creatividad desde cero; reutiliza `intent.json`, `set.json`, prompts, estructura musical y assets aprobados.

---

# Intent System

El sistema debe almacenar intención musical estructurada.

NO depender únicamente del audio generado.

---

# intent.json

Debe incluir:
- BPM,
- key,
- mood,
- instruments,
- energy,
- vocal_style,
- lyrics_context,
- placeholders.

---

# Prompt builders

El sistema debe construir prompts automáticamente desde:
- intent.json,
- profile.json,
- lyrics.md.

---

# Modo exploratorio

Debe soportar:

## Instrumental
- random,
- prompt,
- profile variation.

## Melodía
- random,
- guided,
- profile-based.

## Lyrics
- markdown,
- placeholders,
- AI generated.

---

# Sample Builder

Debe:
- generar previews,
- usar versiones rápidas,
- reducir costo.

---

# Full Song Builder

Debe:
- expandir estructura,
- generar versión completa,
- mezclar assets.

---

# Audio pipeline

## Herramientas

- ffmpeg
- pydub

---

# Exportaciones

- mp3
- m4a
- ogg
- wav
- flac
- aiff
- stems
- lyrics.md
- manifests

---

# Compatibilidad futura

El sistema debe permitir:
- nuevos providers,
- UI web,
- API REST,
- workers,
- cola de tareas,
- orquestacion multi-modelo,
- handoffs,
- providers locales y pro,
- tasks persistidas,
- generación distribuida.

---

# Restricciones técnicas

NO:
- hardcodear providers,
- acoplar exploradores con builders,
- mezclar logica conversacional con logica tecnica,
- acoplar modelos entre si,
- tratar el audio como fuente de verdad,
- depender de un único modelo IA,
- guardar solo prompts sin intención estructurada.

---

# Documentacion viva

Cada avance debe registrarse en README.md.

README.md debe resumir:
- estado actual de sprints,
- funcionalidades disponibles,
- instrucciones de ejecucion,
- estructura vigente,
- pendientes principales.
