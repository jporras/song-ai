# APIalto nivel real sinLM — 2026-10-09

Job ace_job_d866bef6871a3e21cf6f4997b7b8876d7e156c2e33c56811b94fe86d436bea68 completado mediante SQLite/jobs/runner reales sobre copiaQA. Plan ace_plan_2cb5913a56a24c0e8218c960d564178c; revisión spec_rev_64926a5cb6b2; SHA235f4cc5d821a42809d777606e632651a20a6e6a924e440357adcafee8728732. Escenario técnico explícitoQA, no nueva aprobación creativa del usuario final.

Artefacto ace_candidate_eba76699626d4311a957694addc1dcdb: WAV15,0s,720000frames,48kHz,2canales,PCM16,2880044bytes. SHA d21dcbb6288028edf5aa3db590de98c483e6140df7a04d2ed1135100b2761689.

Runtime: Turbo solicitado/reportado coincidentes, XPU activo,8pasos, seed42; high_level/lm_used false/rewrites_enabled false/reported_completion. Input_observation matched y approved_inputs_match. Motor reporta18campos cotejados, ningún unreported ni mismatched; opciones efectivas guidance1/shift3 preservadas/trazadas. Wrapper e informe del motor no prueban fidelidad audible. No escucha/aceptación ni sample aprobado.

S06-07 V0,5→1: ruta alto nivel sinLM ejecutada y separada del handler directo ya observado. La ruta conLM sigue enS00-04, modos/trazas restantesS06-04/05 yS10. No cerrar esos entregables por este caso.

Resultado persistido en `data/qa_high_level_1791602467245496700/result.json`. Cover/Repaint preparados todavía no ejecutados; fuente15sPCM/checksums en REAL_AUDIO_NEXT_CASES_20261009.md.

Runner192,8s; mínimoRAM320MB/pico98%, swap máximo7694MB. La estabilidad observada no permite prometer margen de memoria paraBase/LM. Global92,4%.
