# OpenVINO aislado y evaluación NPU — 2026-10-07

## Alcance

Evaluar Qwen3 4B Q4_K_M en OpenVINO NPU y Gemma2 2B Q4_K_M en Vulkan GPU en el Core Ultra 5 125U con 16 GB. Una distribución entre aceleradores es candidata, no una garantía de menor latencia. El contexto completo, el esquema de 49 campos, el steering y las restricciones creativas deben mantenerse para aceptar un cambio en Song AI.

## Configuración preparada

`tools/setup_openvino_exploration.py` descarga fuentes llama.cpp **b9442 / d4c8e2c29**, SDK OpenVINO **2026.0.0**, OpenCL SDK **v2026.05.29** y compila Release con MSVC, Ninja y cuatro trabajos. Genera `llama-bench`, `llama-cli` y `llama-server`. La compilación terminó correctamente. La descarga de OpenVINO verificó su checksum oficial; URL, tamaño y SHA-256 quedan registrados por paquete.

Todo está bajo `data/tools/llm-exploration/openvino-b9442`. `runtime.json` proporciona ejecutables, rutas DLL y variables del proceso hijo. No se instala un runtime global ni se cambia `.env`, providers, SQLite o el orquestador. El script reutiliza archivos verificados al repetir la preparación.

Windows identifica **Intel AI Boost** con estado OK. Esto acredita presencia del dispositivo, no rendimiento del modelo. El backend local b9442 puede recurrir a CPU si el dispositivo solicitado falta; el runner identifica ese aviso y no acepta el resultado como ejecución del acelerador.

Driver NPU observado mediante `Win32_PnPSignedDriver`: **32.0.100.3717**, fecha2025-06-01. No se actualizó el driver. OpenVINO recomienda el driver compatible más reciente; la antigüedad observada es un dato para investigar, no prueba suficiente de la causa del fallo.

| Dispositivo solicitado | `GGML_OPENVINO_DEVICE` | `GGML_OPENVINO_STATEFUL_EXECUTION` |
|---|---|---|
| GPU | `GPU` | `1` |
| NPU | `NPU` | `0` |

NPU requiere un solo slot. Las pruebas de contexto pequeño son diagnósticas: no autorizan reducir los 8192 tokens del servidor ni el contexto real de Song AI. `llama-bench` OpenVINO exige Flash Attention activado; su control Vulkan debe activar el mismo parámetro. No comparar esa nueva serie directamente con la anterior con Flash Attention desactivado.

## Primera prueba NPU

Qwen, pp128/tg16, dos repeticiones, seis threads, batch512/ubatch256, Flash Attention activado, límite180s. El log confirma **`OpenVINO: using device NPU`**. Tras **135,34 s**, el proceso terminó con código1: `failed to decode prompt batch, res = -3`, durante warmup. No hay medición de tokens/s ni evidencia de calidad. Ese error por sí solo no identifica una causa de driver, memoria o arquitectura.

Evidencia: `data/diagnostics/openvino-20261007/npu-smoke/report.json` y logs. El diagnóstico con CLI usa contexto512, un slot, sin warmup y logging detallado para obtener la causa real. La comparación GPU se conserva por separado.

El diagnóstico CLI cargó37/37 capas bajo OPENVINO0, contexto512 y un slot, pero terminó al comenzar un prompt de13 tokens: código Windows **3221225477 (`0xC0000005`, violación de acceso)**, tras122,11s. No produjo texto útil. No se identifica el módulo causante con ese código; tampoco se atribuye automáticamente al driver. Evidencia: `npu-diagnostic/report.json`, stdout y stderr.

Se preparó una segunda instalación oficial Windows **llama.cpp b11476 / OpenVINO2026.4.1** con `tools/setup_openvino_prebuilt.py`, aislada en `openvino-b11476`. El ZIP verificó el digest publicado por GitHub: `c62c59a6c2b871b85162c7d59307946cd28ee456f1d551bf86bdf68660b6f6c3`. Esta actualización permite comprobar compatibilidad sin tocar el sistema. Su rendimiento requeriría un control Vulkan de la misma versión para atribuir diferencias al backend.

## Segunda instalación y ajustes NPU

La build b11476 identifica **Intel AI Boost (NPU3720)**, además de CPU e Intel Graphics. La selección NPU fue real. El benchmark pp128/tg16 llegó al límite240s sin terminar. El primer intento CLI detectó un cambio de argumentos: `--no-conversation` ya no existe; el diagnóstico se corrigió a `--single-turn`. Ese rechazo de argumentos se conserva como fallo del harness, no del modelo.

El siguiente CLI quedó detenido consultando memoria durante el ajuste automático. Se detuvo únicamente ese proceso, verificando primero su PID/ruta, tras92,27s. El caso final aplicó `--fit off`, seis threads, un slot, contexto512, batch/ubatch128, sin warmup, `GGML_OPENVINO_MEMORY_OPTIMIZE=1`, chunk64 y caché NPU aislada. La carga terminó aproximadamente a105s; se detuvo después en construcción del contexto, antes de responder. Se solicitó un límite180s, pero la duración observada fue **481,50s**, incluido el retraso del cierre nativo. No presentar180s como su duración real. No produjo velocidades ni texto útil.

Evidencias bajo `data/diagnostics/openvino-20261007/b11476/`: `npu-smoke`, `npu-tuned` (argumento rechazado), `npu-tuned-compatible` (detención diagnóstica), `npu-fit-off`. Los procesos CLI y benchmark con carga real fueron cerrados. La prueba dual y la ficha de49 campos siguen pendientes: no se deben ejecutar como aceptación mientras falle el diagnóstico mínimo.

**Decisión:** conservar Vulkan activo. La combinación Qwen NPU + Gemma Vulkan no está validada. El driver instalado32.0.100.3717 es anterior al [driver oficial32.0.100.5540](https://www.intel.com/content/www/us/en/download/794734/intel-npu-driver-windows.html), que lista específicamente Core Ultra5 125U. Intel recomienda usar el driver soportado más reciente. Revisar/actualizar el driver y repetir el diagnóstico es el siguiente paso de compatibilidad; no garantiza una mejora ni demuestra que ese driver sea la causa única. Esta tarea cambia Windows y puede requerir administrador/reinicio: no se ejecutó como parte de la instalación aislada.

## Ensayo GPU

Con pp512/tg32 y Flash Attention activado, Qwen alcanzó el límite de180s y el runner detuvo su propio proceso. Gemma terminó con código1 tras30,25s, fallando también al decodificar warmup (`res = -3`). Ambos logs seleccionan GPU. Evidencia: `data/diagnostics/openvino-20261007/gpu/report.json`. Ninguno produjo velocidades comparables; no se declara que OpenVINO sea lento en general ni que la NPU carezca de soporte. Se necesita resolver la compatibilidad de esta instalación antes de evaluar rendimiento o cambiar el provider.

## Reproducción

```powershell
python tools/setup_openvino_exploration.py
python tools/benchmark_llm_backends.py --backend openvino-gpu=data/tools/llm-exploration/openvino-b9442/build/bin/llama-bench.exe --runtime data/tools/llm-exploration/openvino-b9442/runtime.json --device GPU --flash-attention on --timeout 180 --output data/diagnostics/openvino-20261007/gpu
python tools/probe_openvino_npu.py
python tools/setup_openvino_prebuilt.py
python tools/probe_openvino_npu.py --runtime data/tools/llm-exploration/openvino-b11476/runtime-npu-tuned.json --output data/diagnostics/openvino-20261007/b11476/npu-next --timeout 180
```

## Criterios para cambiar la aplicación

1. Confirmar el dispositivo real y descartar fallback.
2. Completar carga, lectura y generación con contexto completo.
3. Comparar perfiles equivalentes, distinguiendo compilación inicial, carga y respuesta.
4. Validar la ficha de 49 campos y respuestas Gemma contra las mismas restricciones.
5. Probar ambos residentes, memoria y cierre correcto de procesos.
6. Configurar cada rol mediante su adapter, sin acoplar modelos ni cambiar las fuentes de verdad.

Fuentes: [backend OpenVINO](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/OPENVINO.md), [inferencia NPU](https://docs.openvino.ai/2026/openvino-workflow-generative/inference-with-genai/inference-with-genai-on-npu.html), [dispositivo NPU](https://docs.openvino.ai/2026/openvino-workflow/running-inference/inference-devices-and-modes/npu-device.html). Las matrices documentadas usan otros equipos/versiones y no sustituyen estos ensayos locales. La ruta nativa GenAI con modelos IR es otra integración, no el mismo GGUF con una variable diferente.
