# S00: selector LM y letra persistida — 2026-10-09

## Selector

Playwright QA aislada, proyecto song_a22a472ef2ba: ruta high_level_lm y selector cambiado a acestep-5Hz-lm-0.6B, PATCH200 envia ambas decisiones. Confirmacion API y preview200 conservan el modelo y explicit_user_control en input_trace. No es recomendacion ni prueba de carga: LM0.6B incompleto localmente segun inventario, sin ejecucion ni descarga de pesos. Fuente SQLite QA independiente de proyectos habituales. Seleccion inicial mediante Vue; cambios/guardado mediante controles reales. Servidor/navegador cerrados.

## Letra

Nuevo caso test_saved_protected_unicode_lyrics_reopen_confirm_and_reach_wrapper: guarda por servicio de fase texto con José/canción/intención y linea protegida, reabre SQLite, rechaza cambio sin desbloqueo sin mutacion, confirma por servicio real, compila y conserva markdown exacto en archivo y contexto del wrapper. Otra letra en compilacion es rechazada. No usa confirmacion simulada en memoria. Preparacion fixture migrada con tres assets y proyecto vinculado; no modelos ni audio.

## Pendientes

Letra comprobada en servicio/persistencia/request, no nueva prueba editor visible. Chat y matriz de condiciones completa siguen pendientes; S00-03 V0.5, D/V88.9%. No se acredita obediencia del modelo ni fidelidad audible.

Lote dirigido: 28 pruebas backend aprobadas, sin omisiones.
