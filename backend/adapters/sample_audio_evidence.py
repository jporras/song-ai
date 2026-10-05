"""Technical WAV evidence; this does not certify singing, fidelity or listening."""
import hashlib
from pathlib import Path
import wave


def inspect_sample_wav(path: Path, sample_directory: Path) -> dict[str, object]:
    resolved = path.resolve()
    directory = sample_directory.resolve()
    if directory not in resolved.parents or not resolved.is_file():
        raise ValueError("El audio del sample debe existir dentro de su carpeta.")
    try:
        with wave.open(str(resolved), "rb") as audio:
            frames = audio.getnframes()
            channels = audio.getnchannels()
            rate = audio.getframerate()
            width = audio.getsampwidth()
            actual = 0
            while chunk := audio.readframes(65536):
                actual += len(chunk)
            if frames <= 0 or rate <= 0 or channels <= 0 or actual != frames * channels * width:
                raise ValueError("El WAV del sample esta vacio o incompleto; vuelve a generarlo.")
    except (wave.Error, EOFError) as error:
        raise ValueError("El audio del sample no es un WAV PCM valido; vuelve a generarlo.") from error
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return {"relative_path": resolved.relative_to(directory).as_posix(), "sha256": digest.hexdigest(),
            "size_bytes": resolved.stat().st_size, "frames": frames, "sample_rate": rate,
            "channels": channels, "sample_width": width, "duration_seconds": frames / rate}
