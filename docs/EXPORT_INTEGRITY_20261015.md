# Integridad de exportación final — 2026-10-15

Revisión independiente del cierre real S01-04. El servicio de exportación ya exige set válido, ficha confirmada, tipos de artefacto finales y calidad de procedencia, pero todavía falta probar una entrega integrada con un resultado final real.

Se corrigió un defecto en `StorageManager.verify_song_artifact`: al detectar corrupción, la comprobación sustituía el checksum esperado de SQLite por el checksum del archivo alterado. Una segunda verificación podía aprobarlo. Ahora conserva el checksum de registro y guarda el valor observado en campos separados. El resultado continúa `CORRUPTED` en verificaciones repetidas.

`LocalProjectExportService.export` comprueba que cada archivo que entrará en el ZIP pertenece al proyecto y coincide con el checksum registrado antes de crear el archivo de exportación. Un archivo alterado bloquea la exportación; no se escribe el ZIP. La prueba nueva modifica un artefacto final registrado y verifica ese rechazo. Los datos de prueba son sintéticos y no acreditan generación ni descarga de un resultado real.

Verificación: `python -m unittest tests.test_local_project_exports -q`: 4 aprobadas. Regresión completa `python -m unittest discover -s tests -p 'test_*.py' -q`: 372 ejecutadas, 367 aprobadas, 5 omitidas, 0 fallidas, 115,199 s. S01-04 permanece en V0.5: falta el resultado final real, exportación/manifest/ZIP y descarga integrados. La escucha y aceptación se hacen después de D/V 100 %.
