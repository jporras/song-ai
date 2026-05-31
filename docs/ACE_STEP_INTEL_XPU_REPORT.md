# ACE-Step Intel XPU Integration

## Objetivo

Song-AI debe intentar ejecutar ACE-Step sobre Intel XPU cuando Windows, PyTorch y el driver Intel lo permitan. El pipeline musical no cambia: se conserva la misma intención, letra, music plan, duración enviada, voz cantada, parámetros de inferencia y exportables.

## Compatibilidad Investigada

- ACE-Step 1.5 declara soporte para Intel XPU además de CUDA, ROCm, MPS y CPU.
- La documentación de ACE-Step 1.5 reporta prueba en una laptop Windows con Intel Ultra 9 285H integrated graphics.
- ACE-Step 1.5 documenta que `torchcodec` no está disponible para Intel XPU y que usa `soundfile` como fallback completo de audio I/O en Intel.
- PyTorch publica ruedas XPU para Windows y expone `torch.xpu.is_available()`, `torch.xpu.current_device()` y uso de tensores/modelos con `.to("xpu")`.
- PyTorch indica que primero debe estar instalado el driver Intel GPU; si `torch.xpu.is_available()` retorna `False`, el primer punto a revisar es el driver/stack XPU.

Fuentes:

- ACE-Step 1.5 install: https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md
- ACE-Step 1.5 API/env: https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md
- PyTorch Intel GPU/XPU: https://docs.pytorch.org/docs/2.12/notes/get_start_xpu.html

## Decisión Para Song-AI

Song-AI queda en modo local nativo. Docker no se usa para ACE-Step.

El wrapper `tools/acestep_generate.py` ahora acepta:

```powershell
--device auto|xpu|cuda|cpu
--require-device true|false
```

Modo recomendado:

```powershell
--device auto
```

Orden de selección:

1. Intel XPU si `torch.xpu.is_available()` es verdadero.
2. CUDA si `torch.cuda.is_available()` es verdadero.
3. CPU como fallback, dejando motivo explícito.

Para una validación estricta XPU:

```powershell
--device xpu --require-device true
```

En ese modo Song-AI falla con explicación si ACE-Step no puede activar XPU.

## Prerrequisitos

1. Windows nativo.
2. Driver Intel Graphics actualizado.
3. Python 3.11 en `.venv`.
4. PyTorch XPU instalado en `.venv`.
5. `soundfile` instalado para audio I/O en Intel XPU.
6. ACE-Step importable.
7. Modelos ACE-Step en `data/models/music/ace-step`.

Script preparado:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-intel-xpu-prereqs.ps1 -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-intel-xpu-prereqs.ps1
```

Verificación:

```powershell
.\.venv\Scripts\python.exe tools\check_xpu_stack.py --probe-tensor
```

## Métricas Registradas

Cada ejecución ACE-Step escribe `ace_step_diagnostics.json` con:

- dispositivo solicitado,
- dispositivo activo,
- motivo de fallback,
- versión de PyTorch,
- estado de `torch.xpu`,
- `torch.xpu.current_device()` cuando aplica,
- nombre del dispositivo XPU,
- disponibilidad CUDA,
- RAM, swap y CPU,
- muestras de uso Intel GPU cuando Windows entrega contadores,
- tiempo total,
- error y traceback si falla.

Production registra eventos con:

- provider activo: ACE-Step,
- dispositivo solicitado,
- dispositivo activo,
- tiempo transcurrido,
- RAM/swap/CPU durante generación,
- error técnico si el provider falla.

## Resultado Esperado De Validación

La prueba válida no debe recortar canción ni bajar calidad para terminar rápido. Debe ejecutarse desde el flujo real:

1. Intent.
2. Lyrics.
3. Music Plan.
4. Production.
5. Mastering / ACE-Step.
6. Export.

El criterio de éxito es que `ace_step_diagnostics.json` muestre:

```json
{
  "runtime": {
    "requested_device": "auto",
    "active_device": "xpu",
    "backend_active": "xpu"
  },
  "status": "completed"
}
```

Si falla, el diagnóstico debe indicar si el problema vino de PyTorch XPU, ACE-Step, driver Intel, dependencia de audio I/O o falta de hardware visible.

## Estado Actual

Integración permanente implementada:

- detección XPU compartida en backend,
- `tools/check_xpu_stack.py`,
- `scripts/install-intel-xpu-prereqs.ps1`,
- selección automática XPU/CUDA/CPU en `tools/acestep_generate.py`,
- soporte `soundfile` como alternativa a `torchcodec`,
- métricas y fallback en `ace_step_diagnostics.json`,
- UI de Production con provider, dispositivo, runtime y tiempo transcurrido.

Pendiente en el equipo local:

- ejecutar el script de instalación XPU,
- correr `tools/check_xpu_stack.py --probe-tensor`,
- generar una canción completa real con `--device auto` o `--device xpu --require-device true`,
- comparar tiempo contra CPU.
