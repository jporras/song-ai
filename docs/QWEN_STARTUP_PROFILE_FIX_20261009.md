# Qwen: perfil de arranque respetado — 2026-10-09

## Causa encontrada y corrección

Los scripts PowerShell leían parámetros del entorno del proceso, pero no cargaban .env. El backend sí lo hace mediante config.env. Un reinicio manual arrancaba con defaults de llama.cpp pese a mantener la configuración óptima guardada: log anterior n_batch=2048, n_ubatch=512, flash_attn=auto. Ese arranque produjo desconexiones en la revisión larga, incluso con Qwen aislado.

Nuevo scripts/llm-environment.ps1 compartido por start-local-llms.ps1 y stop-local-llms.ps1. Lee únicamente claves SONG_AI_ de .env como texto; respeta variables explícitas del proceso, sin evaluar comandos. Ambos scripts conocen ahora rutas y opciones guardadas. No se modificaron .env, pesos, backend Vulkan ni preferencias de rendimiento.

## Evidencia

- Reinicio administrado de ambos modelos con configuración guardada. Log actual Qwen: n_batch=512, n_ubatch=256, flash_attn=disabled; GPU --n-gpu-layers999.
- Prueba test_llm_environment aprobada: argumentos citados, precedencia del proceso, valores con = y sintaxis de comando tratados literalmente, claves ajenas ignoradas. Primeros intentos del harness no habilitaban ejecución del helper bajo la política PowerShell; corregido invocándolo con el mismo ExecutionPolicy Bypass usado por los scripts del proyecto.
- Repetida la misma revisión persistida, prompt6874tokens, con Gemma y Qwen cargados. Log completa prefill hasta6656 y muestreo sobre6874; ninguna desconexión.
- task_9195615b2e35, provider_handoff, provider_executed=true, provider_error=null; 109.67s totales. Respuesta Qwen reconoce que original/propuesta son iguales, conserva Alma, español, intención tierna y líneas0/2 protegidas. No aprueba audio ni al usuario.
- Steering document_sha256=f8a8bae3468d587438b8943eb0430380710463cdb59da69256e91662fc44208c. Resultado .playwright-mcp/qwen_retry_20261009.json. Es revisión del snapshot del caso previo, no otra aprobación de ficha vigente; sin edición creativa.

La corrección resolvió el fallo reproducido en esta solicitud; no acredita estabilidad universal ni un benchmark nuevo. Se conserva evidencia de fallos en tasks SQLite. S05-03 V0.5→1, regresión resuelta para este caso. Global89.9→90.5%. Gemma/Qwen quedan cargados con sus perfiles existentes. Audio real reservado para el último bloque; no nuevas canciones, aceptación ni commit/push.
