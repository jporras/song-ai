# Exploración rápida de backends Intel — 2026-10-07

Actualización posterior: OpenVINO ya está preparado en Windows. Los primeros casos no completaron inferencia; ver [configuración y diagnóstico NPU/GPU](OPENVINO_CONFIGURATION_20261007.md). La tabla siguiente conserva la serie original con Flash Attention desactivado.

## Objetivo y aislamiento

Detectar problemas de carga y alternativas poco prometedoras antes de ejecutar fichas completas. El runner externo `tools/benchmark_llm_backends.py` recibe ejecutables por configuración y usa los GGUF existentes. No modifica providers, prompts, SQLite activa, `.env` ni el orquestador. No genera audio ni acredita fidelidad de respuestas.

Las pruebas corrieron secuencialmente, con un modelo por proceso, en el Core Ultra 5 125U / Intel Graphics del equipo. Protocolo: `pp512`, `tg32`, dos repeticiones, seis threads, batch 512, ubatch 256, Flash Attention desactivado, caché KV f16 y offload solicitado de todas las capas. Cada caso tiene límite de 90 segundos; el runner detiene únicamente su propio proceso al vencerlo.

`llama-bench` usa entradas sintéticas y generación breve. Estos valores no predicen directamente una ficha de 49 campos, una conversación de 3500 tokens ni calidad musical. Una prueba rápida permite priorizar candidatos; no sustituye aceptación de aplicación ni mide estabilidad prolongada.

## Resultados

Tokens por segundo; mayor es mejor:

| Ejecutable | Modelo Q4_K_M | Lectura pp512 | Generación tg32 | Tiempo total del proceso |
|---|---|---:|---:|---:|
| **Vulkan b9442, actual** | Qwen3 4B | **155,53** | **10,37** | 31,38 s |
| SYCL b5377 | Qwen3 4B | 149,29 | 4,89 | 38,89 s |
| Vulkan b5377, control | Qwen3 4B | 53,13 | 9,86 | 43,70 s |
| **Vulkan b9442, actual** | Gemma2 2B | **294,19** | 14,32 | 16,80 s |
| SYCL b5377 | Gemma2 2B | 250,89 | 7,35 | 24,98 s |
| Vulkan b5377, control | Gemma2 2B | 98,33 | **15,24** | 24,12 s |
| OpenVINO | Ambos | Sin medición | Sin medición | Falta preparación |

Los seis casos medidos completaron carga y benchmarks sin cierre espontáneo. Sus resultados identifican Intel Graphics y backend Vulkan o SYCL. El tiempo total incluye inicialización y warmup; para comparar las etapas se usan las columnas pp/tg, no solo la duración del proceso.

## Decisiones

- **Conservar Vulkan b9442 en Song AI.** Superó al paquete SYCL disponible en lectura y generación de ambos modelos. Vulkan b5377 generó ligeramente más rápido con Gemma, pero leyó mucho más lento; no aporta evidencia para sustituir la instalación actual.
- **No continuar fichas completas con SYCL b5377 como reemplazo inmediato.** Su generación fue aproximadamente la mitad de la de Vulkan, incluso controlando versión b5377. En cambio, su lectura superó a Vulkan b5377: no se declara que SYCL sea inferior en todas las etapas.
- **SYCL moderno/FP16 sigue sin evaluar.** No se infiere su rendimiento desde este paquete anterior ni se confirma el modo FP16 de este binario. Las diferencias entre versiones y builds limitan la generalización.
- **OpenVINO no se descarta por rendimiento.** No había runtime/ejecutable instalado. La release b9442 dispone de paquete OpenVINO Ubuntu, pero no Windows. Su backend requiere OpenVINO, OpenCL y toolchain de compilación; prepararlo merece una tarea separada de esta exploración rápida.

## Procedencia y reproducción

Vulkan actual: b9442 / `d4c8e2c29`. Los paquetes oficiales SYCL y Vulkan b5377 reportaron el mismo commit `24e86cae`, permitiendo el control de versión. Se descargaron en `data/tools/llm-exploration/`; los originales siguen en `data/tools/llama.cpp/`. Se guardaron URL, tamaño y SHA-256 de cada archivo descargado en esa carpeta. No se copian ni alteran modelos.

Ejemplo:

```powershell
python tools/benchmark_llm_backends.py --backend vulkan=data/tools/llama.cpp/llama-bench.exe --backend sycl=data/tools/llm-exploration/sycl-b5377/llama-bench.exe --output data/diagnostics/llm-exploration-20261007
```

La medición original está en `data/diagnostics/llm-exploration-20261007/report.json`, stdout/logs por caso y `same-version-control/report.json`. El paquete ausente se registra como `setup_missing`, separado de fallo, timeout y medición completada. La compilación Python del runner pasó.

Fuentes primarias: [paquetes b5377](https://github.com/ggml-org/llama.cpp/releases/tag/b5377), [paquetes b9442](https://github.com/ggml-org/llama.cpp/releases/tag/b9442), [SYCL para Windows](https://github.com/ggml-org/llama.cpp/blob/master/docs/backend/SYCL.md), [backend OpenVINO b9442](https://github.com/ggml-org/llama.cpp/blob/b9442/ggml/src/ggml-openvino/CMakeLists.txt).

La siguiente evaluación útil requiere un SYCL reciente/FP16 o preparar OpenVINO Windows en otra carpeta, conservando Vulkan como referencia. Solo candidatos compatibles y competitivos pasarían a prompts reales, esquema JSON completo, restricciones musicales y pruebas de memoria con ambos roles.
