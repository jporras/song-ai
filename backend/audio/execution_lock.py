"""One heavy ACE-Step process at a time in this application process."""
from contextlib import contextmanager
from threading import Lock

_audio_lock = Lock()
_state_lock = Lock()
_planning_active = False


def audio_execution_active() -> bool:
    return _audio_lock.locked()


@contextmanager
def exclusive_audio():
    with _state_lock:
        if _planning_active:
            raise ValueError("Hay una inferencia de planificacion en curso; espera a que termine antes de generar audio.")
        if not _audio_lock.acquire(blocking=False):
            raise ValueError("Ya hay una generacion de audio en curso; espera a que termine.")
    try:
        yield
    finally:
        _audio_lock.release()


@contextmanager
def exclusive_planning():
    global _planning_active
    with _state_lock:
        if _audio_lock.locked():
            raise ValueError("Hay audio activo; espera o cancela antes de solicitar inferencia.")
        if _planning_active:
            raise ValueError("Hay una inferencia de planificacion en curso; espera a que termine.")
        _planning_active = True
    try:
        yield
    finally:
        with _state_lock:
            _planning_active = False
