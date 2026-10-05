
# Song AI Generator

> **Requisitos originales.** Este documento conserva la motivación y los tres assets base. El recorrido vigente para principiantes y sus criterios pendientes están en [AMATEUR_USER_FLOW_REVIEW.md](AMATEUR_USER_FLOW_REVIEW.md); consultar [el mapa de documentación](README.md) antes de tomar este flujo como contrato actual.

## Objetivo

Crear un sistema modular en Python capaz de generar canciones personalizadas usando IA mediante:

1. Instrumental base
2. Melodía vocal adaptable
3. Letra dinámica

El sistema debe permitir:

- exploración creativa,
- reutilización de perfiles,
- generación local,
- producción con modelos pro,
- previews,
- generación completa de canciones.

---

# Filosofía del proyecto

NO pensar en:

"generar una canción"

Sino en:

"generar assets musicales reutilizables"

---

# Assets principales

## 1. Instrumental base

Representa:

- ritmo,
- atmósfera,
- identidad sonora,
- BPM,
- tonalidad,
- instrumentación.

Debe poder:
- generarse aleatoriamente,
- generarse mediante prompts,
- derivarse desde perfiles base,
- guardarse como draft,
- reutilizarse.

---

## 2. Melodía vocal adaptable

Representa:
- guía melódica,
- rango vocal,
- intención emocional,
- estructura vocal.

Debe poder:
- adaptarse a distintas letras,
- mantenerse compatible con el instrumental,
- reutilizarse en múltiples canciones.

---

## 3. Letra dinámica

Representa:
- texto editable,
- placeholders dinámicos,
- idioma,
- estructura lírica.

Debe soportar:
- markdown,
- placeholders,
- variaciones automáticas,
- personalización por nombre/ocasión.

---

# Flujo del sistema

## FASE 0 — Configuración

Configurar:
- idioma,
- formato,
- providers,
- carpeta de salida.

---

## FASE 1 — Exploración

Explorar:
1. instrumental,
2. melodía,
3. letra.

Cada asset puede generarse:
- aleatoriamente,
- mediante IA,
- desde perfil base.

---

## FASE 2 — Curaduría

El usuario puede:
- listar drafts,
- escuchar previews,
- marcar favoritos,
- eliminar drafts.

---

## FASE 3 — Ensamble de set

Combinar:
- 1 instrumental,
- 1 melodía,
- 1 letra.

Generar:
- set temporal.

---

## FASE 4 — Sample / Preview

Generar:
- preview corto,
- coro,
- intro + coro,
- sample rápido.

Debe evitar consumo excesivo de modelos pro.

---

## FASE 5 — Ajustes

Modificar:
- BPM,
- tonalidad,
- instrumentos,
- letra,
- voz,
- duración,
- emoción.

---

## FASE 6 — Producción completa

Generar:
- canción completa,
- voz final,
- mezcla final.

---

## FASE 7 — Exportación

Exportar:
- mp3,
- wav,
- stems,
- instrumental,
- voz,
- lyrics.md,
- manifest.json.

---

## FASE 8 — Plantillas reutilizables

Guardar:
- perfiles,
- sets,
- prompts,
- intención musical.

Permitir reutilización futura.

---

# Modos del sistema

## Modo local

Usa:
- modelos locales,
- HuggingFace,
- mocks,
- generación rápida/barata.

---

## Modo pro

Usa:
- OpenAI,
- Stable Audio,
- ElevenLabs,
- providers profesionales.

Debe reutilizar:
- prompts,
- intención,
- perfiles,
- estructura creada localmente.

---

# Requisitos clave

## El sistema debe:

- ser modular,
- funcionar desde consola,
- soportar providers intercambiables,
- soportar generación local/pro,
- guardar manifests JSON,
- guardar intención musical estructurada,
- evitar pérdida de intención entre providers.

---

# Restricciones

## NO:
- copiar canciones existentes,
- usar melodías con copyright,
- acoplar providers directamente al core,
- mezclar lógica musical con lógica de UI.

---

# Objetivo técnico

Permitir:
- reemplazar providers,
- reutilizar assets,
- crear muchas canciones desde un mismo ADN musical.
