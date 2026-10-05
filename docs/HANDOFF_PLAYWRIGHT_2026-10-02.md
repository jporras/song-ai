# Handoff para 5.5 Sol: errores detectados con Playwright MCP

Fecha inicial: 2026-10-02 (America/Bogota). Auditoria ampliada el 2026-10-03. Las primeras trazas UTC corresponden al 3 de octubre.

## Alcance y estado

Auditoria inicial ejecutada con **Playwright MCP real**, sobre FastAPI en `http://127.0.0.1:8011` y el frontend compilado disponible en `frontend/dist`. Se inspecciono tambien el codigo para localizar las causas probables. Este documento complementa `HANDOFF_5_5_SOL.md`. La seccion siguiente registra la implementacion posterior; las reproducciones originales se conservan como evidencia historica.

## Implementacion posterior (2026-10-03)

| ID | Cambio | Comprobacion |
| --- | --- | --- |
| PW-01 | Biblioteca prepara los tres drafts mock y conserva seleccion explicita | Playwright: DB vacia, tres preparaciones, brief editado a 83 BPM y set activo |
| PW-02 | Guardar y continuar espera exito y deja el modal abierto con `role=alert` | Playwright: HTTP 500 simulado, ruta Intent y BPM editado intactos |
| PW-03 | Descartar restaura el baseline del proyecto y las dependencias | Playwright: BPM 99 descartado, vuelve BPM 77; Voice pasa de 3 a 4 capas y vuelve a 3 al descartar |
| PW-04 | Asistente maneja errores, timeout y respuestas de otro contexto | Playwright: red abortada, Enviar habilitado y pregunta conservada |
| PW-05 | Fases de ejemplo sin proyecto no figuran completas; Lyrics distingue ejemplo y guardado | Playwright: biblioteca vacia sin checkmarks |
| PW-06 | CPU es una estimacion cuando no hay task; runtime ausente se describe como no disponible | Playwright: Production sin proyecto no anuncia ejecucion CPU ni `Enviado`; faltan pruebas con runtime CPU/GPU reales |
| PW-07 | `popstate` pasa por el modal y `beforeunload` protege recarga/cierre | Playwright: Atras abre modal; descartar navega; recarga abre dialogo nativo |
| PW-08 | BPM de 48 a 240 validado en backend y reflejado en inputs | Playwright: -20 rechazado con error visible; unit tests: limites e invalidos sin reemplazar DB |
| PW-09 | Tres selectores envian IDs al backend y el set persiste la terna elegida | Unit test: segunda terna en SQLite y `set.json`; Playwright: IDs de la segunda terna coinciden en `/api/sets/{id}` |
| PW-10 | Bloqueo de doble clic y `request_id` idempotente | Playwright: doble clic produce un POST; unit test: mismo ID devuelve un set |

La regresion de Playwright se hizo en `http://127.0.0.1:8012` con SQLite temporal `song-ai-handoff-fix-*`, sin tocar `data/` ni ejecutar modelos/audio. La auditoria original y esta implementacion conviven en el arbol local con cambios previos sin confirmar.

Verificacion final: `SONG_AI_RESOURCE_MONITOR_ENABLED=false` con `python -m unittest discover -s tests -q`: **50 pruebas, OK, 386.871 s**. `python -m compileall -q backend tests`, `npm run build` y `git diff --check` terminaron sin error. No se verifico generacion real de audio ni runtime CPU/GPU.

Se uso SQLite y artefactos temporales en `C:\Users\jorge\AppData\Local\Temp\song-ai-playwright-t16pgxkr`. No se modificaron canciones de `data/`. Se deshabilitaron el arranque de LLM, bootstrap de dependencias, monitor de recursos y comandos de generacion de audio. No se llamaron APIs reales de modelos ni se genero audio.

La continuacion del 2026-10-03 uso otra raiz temporal, `C:\Users\jorge\AppData\Local\Temp\song-ai-playwright-pzkj35ps`, con las mismas protecciones. Los IDs `QA` citados abajo solo existieron en esas bases temporales.

El repositorio ya tenia numerosos cambios locales. Conservarlos; no hacer reset ni reemplazar archivos completos. La auditoria corresponde a ese estado local, no a una release publicada.

## Orden propuesto

| ID | Prioridad | Problema | Estado |
| --- | --- | --- | --- |
| PW-01 | Alta | No hay recorrido visible para obtener los drafts iniciales | Confirmado en biblioteca vacia |
| PW-02 | Alta | Guardar y continuar navega aunque falle el guardado | Confirmado con HTTP 500 simulado |
| PW-03 | Alta | Perder cambios conserva los valores editados | Confirmado con proyecto temporal |
| PW-04 | Alta | El asistente queda bloqueado tras un fallo de red | Confirmado con peticion abortada |
| PW-05 | Media | Fases completas y letra guardada sin persistencia | Confirmado sin proyecto |
| PW-06 | Baja | Production anuncia CPU en ejecucion con runtime no disponible | Confirmado sin generacion |
| PW-07 | Alta | Atras, Adelante y Recargar evitan el control de cambios | Confirmado con proyecto temporal |
| PW-08 | Alta | Se persiste un BPM negativo sin validacion | Confirmado tras recarga |
| PW-09 | Alta | El set toma los primeros drafts sin permitir seleccionarlos | Confirmado con dos drafts por tipo |
| PW-10 | Media | Doble clic crea dos proyectos iguales | Confirmado en Biblioteca |

## PW-01 — Completar el arranque desde una biblioteca vacia

**Reproduccion:** abrir `/library` con DB nueva. `GET /api/drafts` devuelve `{"ok":true,"data":[]}`. Los tres indicadores muestran `pendiente` y `Crear proyecto` esta deshabilitado. Visitar Intent, Lyrics, Instrumental y Voice: no hay una accion visible para crear los tres drafts iniciales; `Guardar letra` esta deshabilitado sin proyecto. Guardar una fase requiere un proyecto ya existente.

**Impacto:** el usuario nuevo no encuentra como alcanzar el primer set valido. No resolverlo permitiendo sets incompletos.

**Pistas verificadas:** `frontend/index.html`, formulario Nuevo proyecto; `frontend/src/app.js`, `canCreateSet`, `savePhaseData`, `saveLyricsDraft`, `createInstrumental`, `createMelody`, `saveIntentAsDrafts`. Existen endpoints POST `/api/instrumentals`, `/api/melodies` y `/api/lyrics`; crear un draft de cada tipo por API desbloqueo el boton y permitio crear el proyecto desde la UI.

**Cambio propuesto:** agregar acciones explicitas para preparar instrumental, melodia y letra desde el brief y los editores correspondientes, antes de crear el set. Mostrar que parte falta y conservar la intencion de cada asset. Usar providers mock cuando no haya modelos configurados; no insertar silenciosamente una cancion de demostracion.

**Aceptacion:** desde DB vacia y sin consola/API manual, completar los tres drafts y crear un set; persistir manifest/intent de cada asset; informar errores por asset y permitir reintento; mantener bloqueados sample/cancion sin set valido y cancion completa sin sample. No acoplar providers con builders ni explorers.

## PW-02 — No avanzar si el guardado falla y mostrar el error

**Reproduccion:** con un set activo, guardar Intent con BPM 77. Editarlo a 99, pulsar Lyrics y luego `Guardar y continuar`. Interceptar solo PUT `/api/projects/*/phases/intent` y responder HTTP 500 con `{"ok":false,"detail":"QA: fallo de guardado simulado"}`.

**Resultado observado:** URL `/lyrics`, modal cerrado y mensaje de error ausente del texto visible de la pagina. El fallo fue inyectado de forma controlada; no se atribuye al servidor un 500 espontaneo.

**Causa localizada:** `savePhaseData` devuelve `false`, pero `saveCurrentPhase` no propaga el resultado y `saveAndContinue` navega incondicionalmente. Los mensajes operativos no tienen una salida visible general en las pantallas de edicion.

**Cambio propuesto:** propagar un resultado de guardado consistente, incluida Production. Cerrar el modal y navegar solo al confirmar persistencia. Mostrar error en el modal o junto al guardado con `role="alert"`; conservar cambios y permitir reintentar sin perder el destino solicitado.

**Aceptacion:** repetir con HTTP 500, red interrumpida y timeout; permanecer en Intent con BPM 99 editable, DB en 77 y error visible. Al reintentar con exito, navegar y recuperar BPM 99 tras recarga. Evitar doble envio mientras guarda.

## PW-03 — Descartar debe restaurar la ultima version guardada

**Reproduccion:** guardar BPM 77 en Intent y recargar (se recupera 77). Cambiarlo a 155, pulsar Lyrics, elegir `Perder cambios` y volver a Intent.

**Resultado observado:** el campo sigue en **155**, aunque se eligio descartar. No se observo escritura de ese valor a DB en esta accion; el defecto confirmado es que queda en el editor como si se hubiera descartado.

**Causa localizada:** `discardAndContinue` limpia `dirty`/`dirtyPhase` y navega, sin restaurar el contenido. Revisar tambien `outdatedPhases`, porque `markDirty` altera dependencias.

**Cambio propuesto:** restaurar la fase y sus indicadores desde el estado persistido del proyecto activo; definir un estado inicial explicito para fases nunca guardadas. Restaurar colecciones con copias independientes para evitar referencias compartidas.

**Aceptacion:** volver a Intent muestra 77; las dependencias recuperan su estado correcto; recargar confirma 77. Repetir con texto de Lyrics y una coleccion de Voice o Instrumental. Cancelar conserva la edicion; guardar la persiste. No sobrescribir otras fases.

## PW-04 — Recuperar el asistente despues de fallos de transporte

**Reproduccion:** interceptar `**/api/assistant/gemma` con `route.abort('failed')`, pulsar `Enviar`.

**Resultado observado:** boton deshabilitado `Pensando...`, sin error en el footer. Restaurar la red no libera por si mismo el estado de carga. Se recargo la pagina para continuar la auditoria.

**Causa localizada:** `askGemmaAssistant` en `frontend/src/app.js` activa `loading`, espera `fetch`/`response.json()` y solo despues lo desactiva; no tiene `try/catch/finally`.

**Cambio propuesto:** gestionar error de transporte/HTTP/JSON, liberar `loading` en `finally` y establecer timeout cancelable. Mostrar error recuperable en el propio asistente; conservar pregunta y contexto. Al responder tarde, verificar que proyecto y fase siguen correspondiendo a la consulta antes de aplicar un patch.

**Aceptacion:** red abortada, HTTP 500, respuesta no JSON y timeout vuelven a habilitar Enviar; pregunta conservada y error visible; reintento exitoso. La respuesta tardia no modifica otro proyecto. Este ultimo caso es una cobertura propuesta, no un fallo reproducido en esta auditoria.

## PW-05 — Distinguir ejemplos, edicion y contenido persistido

**Reproduccion:** con DB vacia y sin proyecto activo, visitar `/library` y `/lyrics`.

**Resultado observado:** sidebar con `✔` en Intent, Lyrics, Music Plan, MIDI, Instrumental y Voice. Lyrics muestra tres secciones de ejemplo, 27 palabras y `Guardado`. Simultaneamente Biblioteca indica todos los drafts pendientes. Despues de crear un set los indicadores pasaron a vacios, reforzando la inconsistencia inicial.

**Causa localizada:** `phaseStatus` considera los valores de ejemplo de `data()` como `READY` cuando no hay proyecto. El indicador de Lyrics en `frontend/index.html` usa ausencia de `dirty` como sinonimo de guardado.

**Cambio propuesto:** mostrar `Sin proyecto`/`Ejemplo sin guardar` cuando corresponda y derivar confirmacion de guardado del estado persistido. Una fase configurada tampoco debe anunciar audio generado si solo contiene configuracion.

**Aceptacion:** DB vacia sin checkmarks de completado ni falsa confirmacion de guardado; guardar una fase y recargar confirma su estado; editarla muestra pendiente; cargar otro proyecto no hereda estados del anterior. Mantener SQLite como fuente activa y JSON como snapshots.

## PW-06 — Describir disponibilidad de CPU sin anunciar una ejecucion inexistente

**Reproduccion:** abrir Production sin proyecto, sin trabajo activo y con comando full song vacio; en la configuracion usada estaba permitido CPU.

**Resultado observado:** `ACE-Step esta corriendo en modo CPU lento.` junto a `Runtime: unavailable` y `Solicitado: 1m 28s / Enviado: 1m 28s`, sin haber enviado una generacion.

**Causa localizada:** `productionTimingEstimate.cpuSlow` considera `allow_cpu_full_song` suficiente; `frontend/index.html` convierte esa posibilidad de configuracion en una afirmacion de ejecucion.

**Cambio propuesto:** separar disponibilidad, dispositivo previsto, estimacion y trabajo realmente activo. Mostrar `Runtime no disponible` cuando corresponda, `Estimado en CPU` si solo es una previsión y reservar `Enviado`/`En ejecucion` para datos de un task real.

**Aceptacion:** comprobar runtime ausente, CPU configurado pero ocioso, CPU ejecutando y GPU/XPU disponible. Ningun mensaje anuncia generacion sin task activo.

## PW-07 — Proteger cambios ante Atras, Adelante y Recargar

**Reproduccion:** con un set activo, abrir Intent, cambiar BPM de 72 a 131 y pulsar Atras en el navegador. Biblioteca se abre sin modal. Pulsar Adelante vuelve a Intent con 131 porque el componente sigue en memoria, tambien sin modal. En otra corrida, guardar BPM 88, editarlo a 144 y recargar: vuelve 88 sin advertir que se perderia 144.

**Impacto:** el control de cambios solo cubre los botones laterales. Los controles nativos del navegador permiten salir o perder trabajo sin decision explicita del usuario.

**Causa localizada:** el listener `popstate` llama directamente a `activateFromPath`; no pasa por `requestNavigation`. No existe manejo `beforeunload` mientras `dirty` sea verdadero.

**Cambio propuesto:** centralizar la transicion de rutas y aplicar el mismo control a sidebar y `popstate`. Si se cancela Atras/Adelante, restaurar de forma segura la entrada de historial sin bucles. Registrar `beforeunload` solo mientras existan cambios sin guardar y retirarlo al guardar, descartar o desmontar la aplicacion.

**Aceptacion:** Atras y Adelante ofrecen Guardar, Perder cambios y Cancelar con el mismo comportamiento del sidebar; Recargar/cerrar activa la proteccion nativa cuando hay cambios. Sin cambios pendientes, la navegacion no muestra avisos. Agregar pruebas para evitar bucles de historial y listeners duplicados.

## PW-08 — Validar valores musicales antes de persistirlos

**Reproduccion:** en Intent escribir BPM `-20`. El control HTML informa `checkValidity() === true` porque no tiene `min`, `max` ni regla de dominio. Pulsar Guardar y recargar: `-20` sigue persistido en SQLite y vuelve al formulario.

**Impacto:** el estado activo puede contener una configuracion musical imposible y trasladarla a planes, manifests o providers. El backend contiene operaciones que asumen BPM positivo; el riesgo posterior se deduce del codigo y no se ejecuto generacion de audio con el dato invalido.

**Pistas verificadas:** los campos BPM de Intent y Music Plan en `frontend/index.html` no tienen limites. `savePhaseData` envia el payload sin validacion de dominio. Hay consumidores como `instrumental_generation_service.py` que calculan `60 / bpm`.

**Cambio propuesto:** definir el rango soportado una sola vez en el dominio/configuracion y validarlo en backend; reflejarlo en los inputs mediante `min`, `max`, `step` y error visible. No confiar solo en HTML. Aplicar la misma regla a Intent, Music Plan, handoffs del asistente e importaciones/snapshots.

**Aceptacion:** cero, negativos, texto, vacio y valores fuera del rango acordado no se persisten; el usuario conserva su edicion y ve el motivo. Los limites validos se guardan y sobreviven la recarga. Un payload directo invalido recibe error 4xx y no modifica la fase anterior.

## PW-09 — Seleccionar los tres assets que componen el set

**Reproduccion:** crear un instrumental, una melodia y una letra; luego crear un segundo draft de cada tipo. Biblioteca solo muestra `listo`, sin IDs ni selectores. Crear `QA seleccion de assets`: el set usa los tres IDs antiguos y registra `rule: first_available_assets`, aunque los segundos drafts sean los recien creados.

**Impacto:** una cancion puede agrupar letra, melodia e instrumental de intentos anteriores sin que el usuario lo vea. Esto rompe la expectativa de que el set represente los assets seleccionados y dificulta preservar la intencion musical del proyecto activo.

**Causa localizada:** `SongService.create_set` ignora IDs de asset y llama `SetBuilder.create_first_valid_set`; el builder usa el elemento `[0]` de cada lista. El formulario no ofrece seleccion.

**Cambio propuesto:** mostrar un selector por tipo con identificador y resumen util de intent/fecha. Enviar los tres IDs al backend y usar `create_from_asset_ids`, manteniendo la validacion existente de tipo, manifest, intent y contenido. Si se desea una seleccion automatica inicial, debe ser visible y editable.

**Aceptacion:** con dos drafts por tipo, elegir explicitamente la segunda terna y comprobar los tres IDs en SQLite, `set.json` y proyecto cargado. Rechazar IDs inexistentes, tipos cruzados o assets incompletos. No crear set si falta una seleccion y no sustituirla silenciosamente por el primer draft.

## PW-10 — Evitar proyectos duplicados por doble envio

**Reproduccion:** con drafts validos, escribir `QA doble envio` y hacer doble clic sobre `Crear proyecto`. El numero de sets paso de 2 a 4 y aparecieron dos IDs distintos con el mismo nombre.

**Causa localizada:** `createSet` no tiene bandera de carga ni deshabilita el boton durante la peticion. Dos eventos `click` lanzan dos POST `/api/sets` concurrentes.

**Cambio propuesto:** bloquear el boton desde el primer envio hasta completar la carga del proyecto y mostrar `Creando...`. Como defensa adicional, aceptar una clave de idempotencia o un identificador de solicitud generado por el cliente para que reintentos equivalentes no creen otro set.

**Aceptacion:** doble clic y dos llamadas concurrentes con la misma clave producen un solo set; al fallar, el boton vuelve a habilitarse y permite reintentar. Dos creaciones deliberadas posteriores siguen permitidas. La proteccion no debe deduplicar solo por nombre.

## Evidencia y controles realizados

| Comprobacion Playwright MCP | Resultado |
| --- | --- |
| DB temporal, GET drafts inicial | Lista vacia |
| Preparar fixtures mediante los tres endpoints POST de drafts | HTTP 200 en los tres |
| Crear proyecto desde Biblioteca tras preparar fixtures | Set creado y activo |
| Guardar Intent BPM 77 y recargar | 77 persistido |
| Descartar BPM 155 y volver | 155 permanece: PW-03 |
| Guardar y continuar con 500 simulado | Navega a Lyrics sin mostrar error: PW-02 |
| Asistente con peticion abortada | Sigue Pensando y deshabilitado: PW-04 |
| Production a 390 × 844 | Sin desbordamiento horizontal detectado por bounding boxes; no equivale a una auditoria movil completa |
| Atras/Adelante con BPM 131 sin guardar | Cambia de ruta sin modal: PW-07 |
| Recargar con BPM 144 sin guardar, tras persistir 88 | Recupera 88 sin advertencia: PW-07 |
| Guardar y recargar BPM -20 | Valor invalido persistido: PW-08 |
| Crear set con dos drafts por tipo | Usa la primera terna y no ofrece selector: PW-09 |
| Doble clic en Crear proyecto | Dos POST efectivos, dos sets nuevos: PW-10 |

Los errores de herramientas (primer arranque de Chrome, intento de clicar Guardar letra deshabilitado y URL relativa invalida en `page.request`) se corrigieron durante la sesion y **no** se cuentan como fallos de la aplicacion.

No se verificaron generacion real, calidad de voz/audio, descargas finales, concurrencia entre proyectos, navegacion completa por teclado ni todos los anchos de pantalla. No se ejecuto nuevamente la suite Python ni el build en esta entrega documental. Los resultados historicos del otro handoff no certifican estos escenarios.

## Preparar una sesion aislada equivalente

Usar una terminal PowerShell desde la raiz. Compilar el frontend si cambio (`npm --prefix frontend run build`). Ejecutar el servidor temporal:

```powershell
$env:SONG_AI_LLM_AUTOSTART='false'
$env:SONG_AI_STOP_LLM_ON_EXIT='false'
$env:SONG_AI_BOOTSTRAP_ON_START='false'
$env:SONG_AI_RESOURCE_MONITOR_ENABLED='false'
$env:PYTHONPATH='backend'
@'
from dataclasses import replace
from pathlib import Path
import tempfile
from config.settings import Settings
s = Settings.load()
s = replace(s, data_dir=Path(tempfile.mkdtemp(prefix='song-ai-playwright-')),
    local_models=replace(s.local_models, llama_cpp_enabled=False,
        full_song_command='', soundtrack_command='', singing_voice_command=''))
print('QA_DATA_DIR=' + str(s.data_dir), flush=True)
Settings.load = classmethod(lambda cls: s)
import uvicorn
from adapters.http.fastapi_app import app
uvicorn.run(app, host='127.0.0.1', port=8011)
'@ | .\.venv\Scripts\python.exe -
```

Abrir la URL con Playwright MCP y un contexto limpio. Para pasar el bloqueo PW-01 en pruebas posteriores, preparar exclusivamente en ese servidor temporal los fixtures:

```javascript
async (page) => {
  for (const resource of ['instrumentals', 'melodies', 'lyrics']) {
    const response = await page.request.post(
      'http://127.0.0.1:8011/api/' + resource, { data: {} });
    if (!response.ok()) throw new Error(await response.text());
  }
  await page.reload();
  // Completar Nombre y pulsar Crear proyecto desde Biblioteca.
}
```

Inyeccion de errores usada (quitar cada route al terminar):

```javascript
await page.route('**/api/assistant/gemma', route => route.abort('failed'));
// Pulsar Enviar y verificar estado; luego unroute y recargar.
await page.route('**/api/projects/*/phases/intent', route =>
  route.request().method() === 'PUT'
    ? route.fulfill({ status: 500, contentType: 'application/json',
        body: JSON.stringify({ok: false, detail: 'QA: fallo de guardado simulado'}) })
    : route.continue());
```

## Entrega esperada del siguiente implementador

1. Resolver PW-01 a PW-04 y PW-07 a PW-09 primero, con cambios acotados y sin rediseñar pantallas ajenas.
2. Corregir estados, mensajes y doble envio de PW-05, PW-06 y PW-10, conservando providers intercambiables y las tres intenciones musicales.
3. Agregar regresiones para persistencia, descarte, navegacion, validacion, seleccion de assets y recuperacion de errores; repetir los recorridos MCP sobre datos aislados.
4. Ejecutar build y pruebas relevantes, anotar resultados exactos y limites. No certificar audio real usando mocks.
5. Actualizar README y este documento por ID con cambios, evidencia y pendientes. No marcar un hallazgo resuelto solo por modificar codigo.
