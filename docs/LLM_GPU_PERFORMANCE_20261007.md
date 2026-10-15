# Rendimiento local de Gemma y Qwen — 2026-10-07

## Alcance y método

Comparación real con llama.cpp b9442, Intel Graphics/Vulkan y modelos GGUF instalados. Se usaron prompts construidos por los componentes actuales de Song AI desde el proyecto SQLite de QA, junto con el steering ACE-Step y los roles. Las solicitudes se enviaron directamente a `/completion` en puertos aislados 8091/8092. Esta prueba no repite la auditoría de interfaz ni genera audio.

Por perfil se mantuvieron contexto 8192, un slot, todas las capas en GPU, temperatura 0,35, semilla 123 y límites de salida: Qwen 3072, Gemma 768. Qwen recibió el mismo JSON Schema de producción. Se guardaron fixtures, hashes, respuestas, tiempos nativos y logs. Cada proceso del ensayo fue cerrado al finalizar.

Primero se compararon perfiles con un modelo residente por vez. Cada solicitud tuvo una ejecución sin reutilización del prompt y otra con caché. La salida puede variar incluso con igual semilla por diferencias numéricas entre lotes y caché; no se interpreta un texto más corto como aceleración del motor. El comportamiento de caché y los controles siguen la [documentación oficial de llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

## Qwen: ampliar lotes, mantener Flash Attention desactivado

| Perfil | Ficha nueva | Repetición con caché | Validación |
|---|---:|---:|---|
| Base: batch 256 / ubatch 128, Flash off | 132,17 s | 199,48 s | Ambas válidas |
| batch 512 / ubatch 128, Flash off | 134,56 s | 75,95 s | Ambas válidas |
| **batch 512 / ubatch 256, Flash off** | **119,02 s** | **73,81 s** | Ambas válidas |
| batch 512 / ubatch 256, Flash on | 177,03 s | 96,64 s | Ambas válidas |

Se seleccionó 512/256 con Flash off: la ficha nueva bajó aproximadamente un 10%; la lectura pasó de 53,29 a 45,21 segundos y la escritura de 8,12 a 8,66 tokens/s. El tiempo elevado de la repetición base es una variación observada, con solo 3,21 tokens/s; no se atribuye a una causa comprobada ni se usa para anunciar una reducción general de 63%.

Las ocho fichas cubrieron los 49 campos y pasaron el validador de producción: tipos, opciones, conservación de valores persistidos, restricciones, campos obligatorios y compatibilidad estructural ACE-Step. Ninguna aprobación creativa ni calidad de audio se deduce de esa validación.

Configuración local seleccionada en `.env`:

```dotenv
SONG_AI_QWEN_GPU_ARGS=--n-gpu-layers 999
SONG_AI_QWEN_LLAMA_ARGS=--threads 6 --flash-attn off --batch-size 512 --ubatch-size 256 --fit off
```

## Gemma: conservar el perfil base y reutilizar el contexto

Se probaron dos pedidos: cuatro versos con «En casa encuentro paz» y cuatro versos con «Ana María»/«José», excluyendo noche/luna/cuna.

| Perfil | Solicitudes nuevas, casos 1 / 2 | Repeticiones, casos 1 / 2 | Decisión |
|---|---:|---:|---|
| Base, argumentos predeterminados | 26,11 / 26,19 s | 2,62 / 5,45 s | Conservar |
| 6 threads, batch 512 / ubatch 256, Flash auto | 27,83 / 27,22 s | 5,26 / 8,84 s | Sin mejora |
| Mismo perfil, Flash on | 27,59 / 26,50 s | 5,06 / 8,19 s | Sin mejora |
| Mismo perfil, Flash off | 21,47 / 21,77 s | 5,38 / 5,80 s | Descartar: una respuesta incumplió cuatro versos visibles |

La respuesta descartada añadió introducción y advertencia a sus cuatro versos. No se amplió el limpiador para ocultar ese incumplimiento. El perfil base seleccionó 12 threads automáticamente en este equipo; los ensayos de 6 threads y lotes menores no lo superaron de forma aceptable.

La mejora aplicada está en `_build_gemma_prompt`: el contexto estable del proyecto aparece primero y la pregunta actual aparece una sola vez al final. Conserva intenciones, assets, procedencia, restricciones y gates; no reduce la información creativa ni los límites de salida.

Comparación de dos preguntas distintas sobre el mismo proyecto, con el perfil base y dos ciclos:

| Prompt | Segunda pregunta, ciclo 1 / 2 | Tokens reutilizados | Tokens por procesar |
|---|---:|---:|---:|
| Original: pregunta al inicio y al final | 16,63 / 16,66 s | 1964 | 1501 |
| **Contexto primero; pregunta una vez al final** | **2,94 / 2,92 s** | **3384** | **37** |

Los ocho resultados de esta comparación conservaron cuatro versos, las frases/nombres solicitados y las exclusiones. Reducción de aproximadamente 82% para la segunda pregunta en estos casos. Las primeras solicitudes todavía necesitaron unos 23 segundos; cambios de proyecto, steering o contexto pueden reducir la reutilización. No se promete responder siempre en tres segundos ni se acredita calidad poética por el conteo de versos.

## Evidencia y límites

La comprobación final con ambos modelos residentes terminó sin cierre: Qwen compiló una ficha válida en **117,47 s** y Gemma entregó cuatro versos con los nombres/exclusiones en **26,11 s**, sin caché previa. Logs confirmaron **37/37 capas Qwen** y **27/27 Gemma** en GPU; Qwen usó lotes 512/256 y Flash desactivado. Ambos procesos seguían activos después de las respuestas y se cerraron al finalizar.

En total se completaron **34 solicitudes reales**: 33 cumplieron las comprobaciones y una incumplió el formato de versos, por lo que se descartó su perfil. No hubo cierres espontáneos en estos ensayos. Es evidencia acotada a estos casos, equipo y versión; no es una garantía de estabilidad para cualquier conversación ni una validación musical por escucha.

Artefactos locales en `.playwright-mcp/two-phase/gpu-profile-benchmark-20261007/`: `fixtures.json`, `results.json`, `gemma-off-results.json`, `gemma-prefix-results.json`, logs por perfil y comprobación final `selected-dual-results.json`.

Pruebas de regresión dirigidas: cinco de contexto/guía del assistant y tres de procedencia/presentación lírica aprobadas; compilación Python correcta. La suite general de 222 pruebas pertenece a la entrega anterior; no se presenta como una repetición posterior a este ajuste.

Los modelos, las intenciones y la arquitectura modular se conservan. Se cambiaron el perfil local de Qwen y el orden del contexto conversacional de Gemma. Las propuestas siguen pendientes de revisión/guardado explícito del usuario. No se generó audio ACE-Step.
