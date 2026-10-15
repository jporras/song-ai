"""Bounded PCM measurements; no inference about musical or vocal quality."""
import math
import struct
import wave
from pathlib import Path
from adapters.sample_audio_evidence import inspect_sample_wav


def measure_pcm_signal(path: Path, directory: Path) -> dict:
    before = inspect_sample_wav(path, directory)
    width = before["sample_width"]
    if width not in {1, 2, 3, 4}:
        return {"status": "unsupported", "audio_sha256": before["sha256"]}
    count, zeros, extremes, peak, squares = 0, 0, 0, 0, 0
    scale = 2 ** (8 * width - 1)
    with wave.open(str(path), "rb") as audio:
        while chunk := audio.readframes(16384):
            if width == 1:
                values = (v - 128 for v in chunk)
            elif width == 3:
                values = (int.from_bytes(chunk[i:i + 3], "little", signed=True) for i in range(0, len(chunk), 3))
            else:
                values = (v[0] for v in struct.iter_unpack("<h" if width == 2 else "<i", chunk))
            for value in values:
                count += 1
                zeros += value == 0
                extremes += value in (-scale, scale - 1)
                peak = max(peak, abs(value))
                squares += value * value
    after = inspect_sample_wav(path, directory)
    if after != before:
        raise ValueError("El audio cambio durante la medicion; vuelve a comprobarlo.")
    rms = math.sqrt(squares / count) / scale
    return {"status": "measured", "method": "pcm_integer_samples", "audio_sha256": after["sha256"],
            "sample_values": count, "digital_silence": zeros == count,
            "zero_values": zeros, "full_scale_values": extremes,
            "full_scale_ratio": extremes / count, "peak_dbfs": 20 * math.log10(peak / scale) if peak else None,
            "rms_dbfs": 20 * math.log10(rms) if rms else None,
            "quality_verified": False}
