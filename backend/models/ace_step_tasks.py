"""Shared deterministic task checks; no model or filesystem access."""
import math

TASKS = ("text2music", "cover", "repaint", "lego", "extract", "complete")
BASE_TASKS = {"lego", "extract", "complete"}
TRACKS = {"vocals", "backing_vocals", "drums", "bass", "guitar", "keyboard", "percussion",
          "strings", "synth", "fx", "brass", "woodwinds"}


def validate_source_interval(task: str, start: float, end: float, duration: float) -> None:
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("El audio fuente debe tener una duracion valida.")
    if task in {"repaint", "lego"} and (start >= duration or (end != -1 and end > duration)):
        raise ValueError("El intervalo de edicion debe quedar dentro de la duracion del audio fuente.")


def validate_task_inputs(task: str, config: str, source: str = "", instruction: str = "",
                         start: float = 0, end: float = -1, tracks: tuple[str, ...] = ()) -> None:
    if task not in TASKS:
        raise ValueError("Tarea ACE-Step desconocida.")
    if task in BASE_TASKS and config not in {"acestep-v15-base", "acestep-v15-xl-base"}:
        raise ValueError("Esta tarea requiere seleccionar Base 1.5 explicitamente; Turbo/SFT no la admiten.")
    if task != "text2music" and not source.strip():
        raise ValueError("Selecciona el audio fuente para esta tarea ACE-Step.")
    if task in BASE_TASKS:
        if not instruction.strip() or not tracks or any(track not in TRACKS for track in tracks):
            raise ValueError("Declara instruccion y pistas admitidas para la tarea Base.")
        if task in {"lego", "extract"} and len(tracks) != 1:
            raise ValueError("Lego/Extract requieren una sola pista objetivo.")
        if any(track not in instruction.lower() for track in tracks):
            raise ValueError("La instruccion debe identificar todas las pistas seleccionadas.")
    if task in {"repaint", "lego"}:
        if (isinstance(start, bool) or isinstance(end, bool) or not math.isfinite(start)
                or not math.isfinite(end) or start < 0 or (end != -1 and end <= start)):
            raise ValueError("El intervalo debe empezar en cero o mas y terminar despues; -1 indica hasta el final.")
