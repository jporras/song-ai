# Preparación del lote final ACE-Step — 2026-10-09

## Observado en esta continuación

Contrato instalado inspeccionado sin importar motor: compatible, sin problemas detectados; Base declara seis modos requeridos y Turbo text2music/cover/repaint. Source hashes en salida de `tools/check_acestep_contract.py`.

Memoria física con psutil:994MB disponibles antes del cierre;8450MB después. Script administrado verificó ejecutable/modelos y detuvo solo Gemma pid12072 y Qwen pid25352. No se cerraron otras aplicaciones ni se cambiaron perfiles Vulkan. Los modelos quedan detenidos para el siguiente lote de audio.

PyTorch2.9.1+xpu detecta Intel(R) Graphics. Este probe no asigna tensores ni carga pesos. El primer inventario usó por error el default del CLI; corregido para derivar la ruta del perfil real: `data/models/music/acestep-1.5-2b-turbo`. Base/Turbo/VAE/embeddings tienen archivos requeridos y configs válidos. LM1.7B tiene prerrequisitos; LM0.6B no. No sustituir un LM confirmado silenciosamente: usar1.7B solo en request de prueba explícito, o informar falta de0.6B. Reporte `data/runtime/final_audio_preflight_20261009.json`.

## Lote final ordenado por dependencias

1. Cancelación con pesos cargados, hijo cerrado y memoria liberada; restauración Gemma/Qwen y comprobación física, volver a cerrar antes del siguiente audio (S04-02/03).
2. Turbo APIalto nivel sin LM: candidato corto y trazas request→nativo; contrastar ruta directa ya probada con Isabella (S00-04/S06-05/07).
3. Cover y Repaint con fuente verificada, intervalo y conservación registrados (S06-04/S10-02/03).
4. Base: Lego/Extract/Complete, una carga agrupada si el runner lo permite sin perder exclusividad y asociación por task; no repetir text2music aceptado (S10-04/05/06).
5. LM opcional1.7B solo con request explícito y presupuesto suficiente; controles efectivos/trazas.
6. Artefactos reales en Studio: reproducción A/B, feedback/corrección, recarga y descarga por checksum (S01-03/04/S04-04/S06-06/S10-07). Sample opcional, no requisito.

Ninguna generación nueva comenzó en esta continuación. Disponibilidad de memoria medida antes de carga no garantiza estabilidad durante generación. Sprints de pruebas reales conservan su estado; global90,8%. Piloto/aceptación con personas posterior y separado.
