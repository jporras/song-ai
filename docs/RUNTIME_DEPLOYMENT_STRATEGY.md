# Runtime Deployment Strategy

Este documento es una guia de steering para elegir tecnologias y runtimes al inicio de un proyecto. Su objetivo es evitar decisiones por costumbre, especialmente la idea de que Docker, ejecucion nativa o un modo hibrido sean siempre la respuesta correcta.

La regla base es:

```text
Docker cuando simplifica.
Nativo cuando acelera.
Dual cuando conviene decidir por proyecto.
```

## Alcance

Esta guia sirve para proyectos que combinan aplicaciones, servicios auxiliares, modelos locales, audio/video, IA, bases de datos, workers o infraestructura temporal.

Debe usarse al definir:

- runtime de desarrollo,
- runtime de produccion local,
- providers de IA,
- servicios auxiliares,
- scripts de instalacion,
- preflight de prerequisitos,
- mensajes de error,
- documentacion operativa.

## Principios

1. No elegir Docker por inercia.
2. No elegir nativo por orgullo tecnico.
3. Aislar lo que Docker simplifica.
4. Ejecutar nativo lo que dependa de hardware, drivers o baja latencia.
5. Permitir modo dual solo cuando el costo de mantenerlo se justifica.
6. Declarar el runtime de cada componente, no esconderlo en scripts.
7. Expresar prerequisitos en scripts verificables.
8. Fallar con mensajes accionables, no genericos.
9. Mantener la fuente de verdad del proyecto separada del runtime.
10. Registrar la decision como parte de la arquitectura inicial.

## Modos De Runtime

### portable_docker

Todo lo posible corre en Docker.

Usar cuando el objetivo principal sea:

- instalacion simple,
- portabilidad,
- aislamiento,
- reproducibilidad,
- apagado facil de infraestructura temporal.

Aceptar como trade-off:

- menor eficiencia,
- acceso mas dificil a GPU/iGPU/NPU,
- dependencia de Docker Desktop, WSL2 o daemon equivalente,
- configuracion adicional para drivers.

### local_hardware

Los componentes de computo pesado corren nativos.

Usar cuando el proyecto dependa de:

- GPU,
- iGPU,
- NPU,
- CUDA,
- ROCm,
- Vulkan,
- SYCL,
- OpenVINO,
- DirectML,
- Metal,
- baja latencia,
- acceso directo a archivos grandes o dispositivos locales.

Aceptar como trade-off:

- instalacion manual de programas,
- mas variacion entre equipos,
- scripts de setup/preflight mas detallados.

### hybrid

Infraestructura auxiliar en Docker y computo pesado en nativo.

Usar cuando:

- Redis, Kafka, ChromaDB, Prometheus, Grafana o Nginx simplifican el entorno en Docker,
- modelos, audio, video o inferencia pesada deben correr nativos,
- se quiere una frontera clara entre infraestructura y compute.

Aceptar como trade-off:

- dos superficies de operacion,
- mas preflight,
- documentacion de puertos, volumenes y fronteras.

## Clasificacion Inicial Por Componente

| Componente | Runtime recomendado | Motivo |
| --- | --- | --- |
| Redis | `docker_preferred` | Servicio auxiliar facil de aislar y apagar. |
| PostgreSQL | `docker_preferred` | Estado controlado por volumen, instalacion simple. |
| SQLite externo si aplica | `docker_preferred` | Solo cuando se encapsula como servicio auxiliar; SQLite embebido suele ser local. |
| Kafka | `docker_preferred` | Stack auxiliar complejo, mejor contenerizado. |
| ChromaDB | `docker_preferred` | Servicio auxiliar portable. |
| Prometheus / Grafana | `docker_preferred` | Observabilidad temporal o auxiliar. |
| Nginx | `docker_preferred` | Proxy/edge portable. |
| LLM / llama.cpp | `dual_mode` | Docker simplifica; nativo puede acelerar y reducir latencia. |
| Gemma | `dual_mode` | Puede correr portable o nativo segun backend. |
| Qwen | `dual_mode` | Puede correr portable o nativo segun backend. |
| ACE-Step | `native_preferred` | Audio pesado, drivers y aceleradores importan. |
| RVC / voz cantada / audio IA | `native_preferred` | Sensible a GPU, latencia y librerias locales. |
| FFmpeg pesado | `native_preferred` | Mejor acceso a hardware, codecs y disco local. |
| Generacion musical/audio | `native_preferred` | Compute pesado y dependiente de aceleradores. |

## Contrato De Runtime Para Providers

Cada provider o servicio deberia declarar estos campos en configuracion, estado o diagnostico:

```text
runtime_capability:
- docker_preferred
- native_preferred
- dual_mode

runtime_active:
- docker
- native
- unavailable

hardware_backend:
- cpu
- cuda
- rocm
- vulkan
- sycl
- openvino
- metal
- directml
- unknown
```

Ejemplo:

```json
{
  "provider": "ace_step",
  "runtime_capability": "native_preferred",
  "runtime_active": "native",
  "hardware_backend": "cpu",
  "available": true,
  "warning": "Disponible por CPU, pero puede ser demasiado lento para canciones largas."
}
```

## Preflight Recomendado

El preflight debe separar claramente:

- servicios dockerizados requeridos,
- programas nativos requeridos,
- aceleradores disponibles,
- providers compatibles,
- backend recomendado,
- backend realmente activo.

Debe reportar, segun aplique al proyecto:

- Docker disponible,
- Docker Compose disponible,
- servicios auxiliares disponibles,
- Python disponible,
- Node/npm disponible,
- Git disponible,
- FFmpeg disponible,
- llama.cpp disponible,
- modelos GGUF disponibles,
- ACE-Step disponible,
- torch / torchaudio / torchcodec disponibles,
- CPU/RAM/swap/disco,
- GPU/iGPU/NPU detectadas,
- backend recomendado,
- backend activo.

## Mensajes De Error

Ningun proceso pesado debe fallar con mensajes genericos.

Todo error operativo debe explicar:

- que dependencia falta,
- si falta por modo Docker o modo nativo,
- que comando o accion debe ejecutar el usuario,
- si puede continuar por CPU,
- si existe fallback,
- que impacto tendra en rendimiento o calidad.

Ejemplo:

```text
ACE-Step esta instalado, pero no hay backend acelerado visible.
Puede continuar por CPU si SONG_AI_ALLOW_CPU_FULL_SONG=true, pero la generacion puede tardar horas.
Accion recomendada: instalar/configurar provider nativo con CUDA, DirectML, OpenVINO o SYCL.
```

## Checklist De Decision Inicial

Antes de implementar, responder:

- Que componentes son infraestructura auxiliar.
- Que componentes son compute pesado.
- Que componentes necesitan GPU/iGPU/NPU.
- Que componentes necesitan baja latencia.
- Que componentes deben ser apagables/recreables facilmente.
- Que datos son fuente de verdad.
- Que archivos son artefactos regenerables.
- Que providers deben ser intercambiables.
- Que comandos de setup/preflight deben existir.
- Que ruta minima debe funcionar sin APIs reales.

## Plantilla De ADR

Usar esta plantilla cuando se elija runtime:

```text
# ADR: Runtime del proyecto

## Contexto

## Decision

Runtime principal:
- portable_docker | local_hardware | hybrid

## Componentes Docker

## Componentes Nativos

## Componentes Dual Mode

## Hardware Objetivo

## Preflight Requerido

## Riesgos

## Trade-offs Aceptados

## Como Revertir O Cambiar La Decision
```

## Aplicacion A Song-AI

Si esta guia hubiera existido desde el inicio de Song-AI, la decision habria sido:

```text
runtime principal: local_hardware
```

Motivos:

- Song-AI genera audio y canciones completas.
- ACE-Step y otros providers de audio dependen fuertemente de hardware local.
- La laptop objetivo requiere probar backends nativos como DirectML, OpenVINO, SYCL o providers CLI locales.
- Docker no expuso iGPU/NPU de forma util en las pruebas.
- SQLite local en `data/` es la fuente activa.
- Los JSON son snapshots/exportaciones, no runtime.

Regla operativa para este repo:

- no reintroducir Docker como ruta de ejecucion,
- expresar prerequisitos en scripts,
- mantener providers intercambiables,
- priorizar ejecucion nativa para audio pesado,
- mantener mocks/fallbacks para fases tempranas,
- documentar en README cada avance funcional o arquitectonico.
