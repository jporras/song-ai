# Pistas objetivo en ejecución Base

Caso QA `qa_high_level_1791603362405517900`, plan `ace_plan_cef769706b84487b9331a25bc69e9025`: fallo real Lego antes de carga de pesos. El compilador conservaba `target_tracks=['guitar']`, pero el adaptador omitía `--tracks`; `validate_task_inputs` del wrapper rechazó la solicitud correctamente.

Corregido el adaptador: valida las restricciones Base, transmite las pistas aprobadas sin sustituirlas y registra procedencia y transformación `comma_join` en el contexto de ejecución. La instrucción sigue siendo el condicionamiento nativo; tracks es una restricción del wrapper. No añade campos inexistentes al handler.

Verificación: `python -m unittest tests.test_ace_step_user_input_acceptance tests.test_ace_step_execution`: 9 pruebas aprobadas. La matriz USER verifica argv y validación real de argumentos para Lego/Extract/Complete. Fallo inicial conservado; reintento en nueva QA, sin acreditar generación hasta finalizar ni modificar originales.

Reintento QA1791603499514019000, plan `ace_plan_c468153aa9364d83a97ef5d00696c80f`: argv real contiene `--tracks guitar`; modelo Base cargado y difusión PyTorch CPU iniciada (32pasos). Esto confirma que el fallo previo fue superado, pero no acredita todavía salida de audio. El lote secuencial espera este resultado antes de Extract y Complete.

Regresión puntual posterior: Complete con decisión USER `['drums','bass']` conserva orden/valores como `--tracks drums,bass`, instrucción intacta, contexto con `comma_join` y ficha sin mutación; argumentos pasan el validador real del wrapper. Una prueba específica aprobada en0.047s, sin repetir suite ni cargar modelos. No acredita ejecución o separación de dos pistas por el motor.
