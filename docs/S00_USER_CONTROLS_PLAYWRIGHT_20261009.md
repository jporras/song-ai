# S00: controles USER en Playwright — 2026-10-09

Base aislada data/qa_user_controls_20261009, proyecto song_0a7b4fc32005. Modelos desactivados. Seleccion inicial del proyecto preparada mediante proxy Vue; edicion, guardado y confirmacion mediante controles visibles reales.

## Valores introducidos

BPM 97; tonalidad D Major; compas 6/8; idioma Spanish; duracion 123 s; idea Una balada tierna para una persona querida.; instrumentos piano/cello; estructura verse/chorus; voz suave; formato wav.

PATCH /spec HTTP 200 conserva los diez campos y procedencia explicit_user_control. Nueva revision pendiente spec_rev_0285777415a2. Confirmacion por boton HTTP 200 crea spec_rev_4640d1c37c6e. Recarga y consulta conservan valores y confirmacion.

Preview solicitado por API, no por boton: caption balada; calma; piano, cello; voz suave; bpm97/key D Major/duracion123; Spanish→es y 6/8→6 trazados. Idea/estructura/formato retenidos con limitacion, no presentados como parametros ejecutables. Letra José, quédate aquí. fue argumento no confirmado de preview, no editor ni aprobacion de letra.

## Correccion

El preview todavia enumeraba representative_real_sample como pendiente. Retirado del compilador: sample opcional, sin alterar confirmaciones requeridas. 18 pruebas del bloque aprobadas despues del cambio. Servidor QA y navegador cerrados.

## Limites y harness

No inferencia/audio ni aprobacion creativa; no matriz completa chat, fuentes, todos los modos o UI→wrapper. La fixture inicial omitia campos requeridos: validacion HTML bloqueo correctamente guardado; se completaron usando controles visibles, sin omitir validacion. El localizador de Compas se adapto a label que incluye opciones. S00-03 permanece verificacion parcial.
