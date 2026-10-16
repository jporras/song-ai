"""Generate sprint progress from the reviewed task ledger; no inference of status."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(ledger):
    weights = ledger['weights']
    assert abs(sum(weights.values()) - 1) < 1e-9
    tasks = ledger['tasks']
    assert len({task['id'] for task in tasks}) == len(tasks)
    for task in tasks:
        assert all(task[field] in (0, 0.5, 1) for field in ('developed', 'verified', 'accepted'))
        assert task['accepted'] <= task['verified'] <= task['developed']
        assert task['evidence'] and task['remaining']
    lines = ['# Avance calculado de sprints', '',
        f"Baseline revisada: {ledger['baseline_date']}. {len(tasks)} entregables de alcance activo.", '',
        'Cada entregable tiene igual peso dentro de su sprint; cada uno de los ocho sprints tiene igual peso global. Desarrollo 62,5% y verificación 37,5%, conservando la proporción previa 50:30. Aceptación fuera del cálculo: se revisará después de alcanzar 100% en desarrollo y verificación. Estados: 0 pendiente, 0.5 parcial, 1 completo con evidencia. Aceptación acreditada únicamente donde existe decisión explícita o evidencia del criterio correspondiente; no se deduce del número de tests.', '',
        'El cálculo mide avance de entregables, no horas ni calidad de audio. Los estados son evaluaciones explícitas revisables; el script calcula, no audita el código. No contar los mismos avances en subdivisiones DS/S06-A–F. El 100% de avance exige desarrollo y verificación completos de este alcance; la aceptación y el cierre final se evalúan después, por separado.', '',
        'Reclasificación 2026-10-15: la escucha musical y el piloto con participantes pertenecen a aceptación; la verificación mide ejecución y comportamiento técnico observados. S01-03 cierra correspondencia técnica de un sample real y S01-04 cierra exportación integrada real; la escucha permanece en aceptación. Esto no certifica fidelidad perceptual ni simula un piloto. S00-04, S06-05, S06-06 y S10-07 conservan pruebas técnicas pendientes.', '',
        '| Sprint | Desarrollo | Verificación | Aceptación registrada (fuera del cálculo) | Avance D/V |',
        '| --- | ---: | ---: | ---: | ---: |']
    totals = []
    for sprint in sorted({task['id'].split('-')[0] for task in tasks}):
        entries = [task for task in tasks if task['id'].split('-')[0] == sprint]
        averages = {field:sum(task[field] for task in entries)/len(entries) for field in ('developed', 'verified', 'accepted')}
        score = sum(weights[field]*averages[field] for field in weights)*100
        totals.append(score)
        lines.append(f"| {sprint} | {averages['developed']*100:.1f}% | {averages['verified']*100:.1f}% | {averages['accepted']*100:.1f}% | {score:.1f}% |")
    global_score = round(sum(totals)/len(totals), 8)
    lines.extend(['', f'**Global: {global_score:.1f}%**. Medición vigente solo D/V. El 70,6% anterior incluía aceptación y no es directamente comparable; el cambio de fórmula no añade entregables.', '',
        '## Entregables y pendientes', '', '| ID | Entregable | D / V / A | Evidencia | Pendiente |', '| --- | --- | --- | --- | --- |'])
    for task in tasks:
        lines.append(f"| {task['id']} | {task['title']} | {task['developed']} / {task['verified']} / {task['accepted']} | {task['evidence']} | {task['remaining']} |")
    lines.extend(['', '## Regla de actualización', '',
        'Actualizar estado y evidencia solo al entregar trabajo que cubra el pendiente identificado. Un nuevo test redundante no suma puntos. Añadir o dividir entregables cambia el denominador: registrar el cambio de alcance explícitamente; no hacerlo para inflar el avance. Cada continuación cita IDs entregados, transición de estados y diferencia calculada. Conservar el historial en el plan/README. Ejecutar `python scripts/sprint_progress.py` para regenerar este reporte desde `docs/sprint_progress.json`.', '',
        '## Niveles de verificación', '',
        '| Nivel | Qué se ejecuta | Estado del lote 2026-10-15 |',
        '| --- | --- | --- |',
        '| P | Python, frontend, build y contratos sin modelos | 379 Python: 374 aprobadas y 5 omitidas tras la exportación integrada; 63 frontend aprobadas en el lote anterior; build y contrato instalado correctos en ese lote. |',
        '| L | Gemma/Qwen reales con SQLite QA | Gemma 18,75 s y Qwen 50,42 s respondieron por registry con steering; evidencia histórica de tasks conservada. |',
        '| A | ACE-Step real y recorrido final | Turbo sin LM generó WAV/MP3/FLAC reales en QA; manifest, ZIP y descargas ASGI comprobados. LM1.7B no cargado: presupuesto 11609 MB frente a 10540 MB disponibles en su preflight. |', '',
        'Detalle, límites y criterios de salida: [lote 2026-10-15](SPRINT_VERIFICATION_BATCH_20261015.md) y [estrategia](VERIFICATION_STRATEGY.md). Ningún nivel sustituye la aceptación del usuario.', '',
        '## Próximo bloque prioritario', '',
        'Desarrollo pendiente: ' + (', '.join(task['id'] for task in tasks if task['developed'] < 1) or 'ninguno')
        + '. Verificación parcial: ' + (', '.join(task['id'] for task in tasks if 0 < task['verified'] < 1) or 'ninguna')
        + '. Completar la verificación técnica pendiente por costo y criticidad según VERIFICATION_STRATEGY.md; conservar escucha y piloto para la aceptación final. No atribuir calidad audible a integridad de archivos.', ''])
    return '\n'.join(lines)


if __name__ == '__main__':
    report = render(json.loads((ROOT/'docs/sprint_progress.json').read_text(encoding='utf-8')))
    (ROOT/'docs/SPRINT_PROGRESS.md').write_text(report, encoding='utf-8')
    print(next(line for line in report.splitlines() if line.startswith('**Global:')))
