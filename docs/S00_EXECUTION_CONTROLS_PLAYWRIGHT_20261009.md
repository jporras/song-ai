# S00: opciones de ejecucion en Playwright — 2026-10-09

QA aislada data/qa_user_controls_20261009, song_ca3835a63b0f. Modelos desactivados. Seleccion inicial mediante proxy Vue; controles visibles usados para editar, guardar y confirmar.

## Resultado

Ruta high_level_lm, seed24680, inference_steps32, guidance_scale5, shift1.5. PATCH HTTP200 conserva valores y marca revision pendiente. Confirmacion crea revision spec_rev_aceea63050bb. Consulta posterior y preview API conservan los cinco valores con explicit_user_control.

LM 1.7B mostrado inicialmente y seleccionado sin cambio no se envio en PATCH: preview usa el mismo modelo como system_default, no como decision USER. Esta prueba no acredita edicion/persistencia del selector LM; para hacerlo falta elegir un valor diferente. No se cargaron pesos.

Al elegir cover con high_level_lm, guardar se deshabilita y explica elegir Directa o API sin LM para edicion. No reescribe la ruta ni seed24680; control de LM deja de aplicarse. No se guarda la combinacion invalida.

## Limites

No inferencia/audio ni todos los modos/fuentes. Preview por API; no generacion por UI. La fixture usa ficha preparada y sin set vinculado; seleccion/recuperacion inicial de proyecto por Vue, no Biblioteca. S00-03 sigue parcial: fuentes, intervalos, selector LM cambiado, letra/editor y chat por completar. Servidor QA y navegador cerrados.
