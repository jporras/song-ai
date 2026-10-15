# S01-03 — correspondencia técnica de sample real

El 2026-10-15 se usó el candidato real `ace_job_d866bef6871a3e21cf6f4997b7b8876d7e156c2e33c56811b94fe86d436bea68` de la QA aislada `data/qa_high_level_1791602467245496700`. No se inició generación nueva ni se modificaron proyectos de producción.

`create_candidate_sample` creó `sample-602a065126c6453dbea9db5ce7a603e3` tras autorización técnica QA explícita. El WAV copiado conserva SHA256 `d21dcbb6288028edf5aa3db590de98c483e6140df7a04d2ed1135100b2761689`. El sample está ligado a `qa-builder-batch-set`, plan `ace_plan_2cb5913a56a24c0e8218c960d564178c` y la revisión del candidato. Su estado persistido es `approval_status=pending`.

La evaluación de correspondencia registra `configuration_matches=true`, `execution_configuration_matches=true` y `assessment_current=true` tras reabrir SQLite. `representativity_verified=false` y `final_generation_ready=false`: la coincidencia de provider/configuración y el checksum no prueban voz, canto, calidad ni representatividad perceptual. La copia completa del candidato como sample tampoco acredita por sí sola que un fragmento corto prediga otra generación final.

S01-03 se mide ahora en D/V por la correspondencia técnica verificable del sample opcional. La escucha y decisión de uso como evidencia de calidad quedan para la aceptación final. El sample nunca es requisito para generar la canción completa.
