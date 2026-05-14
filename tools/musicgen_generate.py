from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera instrumental WAV local con MusicGen via transformers.")
    parser.add_argument("--prompt", required=True, help="Ruta al prompt musical generado por Song AI.")
    parser.add_argument("--output", required=True, help="Ruta WAV de salida esperada.")
    parser.add_argument("--model", default="facebook/musicgen-small", help="Modelo MusicGen local/cacheado.")
    parser.add_argument("--seconds", type=int, default=30, help="Duracion aproximada del instrumental.")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, mps, etc.")
    args = parser.parse_args()

    try:
        import torch
        from scipy.io.wavfile import write as write_wav
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except ImportError as error:
        raise SystemExit(
            "Faltan dependencias para MusicGen. Instala en el entorno local: "
            "pip install torch transformers scipy. Detalle: " + str(error)
        ) from error

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processor = AutoProcessor.from_pretrained(args.model)
    model = MusicgenForConditionalGeneration.from_pretrained(args.model)
    model.to(args.device)

    sample_rate = int(model.config.audio_encoder.sampling_rate)
    max_new_tokens = max(64, int(args.seconds * 50))
    inputs = processor(text=[prompt], padding=True, return_tensors="pt").to(args.device)
    with torch.no_grad():
        audio_values = model.generate(**inputs, max_new_tokens=max_new_tokens)

    audio = audio_values[0, 0].detach().cpu().float().numpy()
    peak = max(0.01, float(abs(audio).max()))
    normalized = (audio / peak * 32767).astype("int16")
    write_wav(str(output_path), sample_rate, normalized)
    print(f"Instrumental generado: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
