from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera una cancion completa local con ACE-Step.")
    parser.add_argument("--prompt", required=True, help="Ruta al prompt musical.")
    parser.add_argument("--lyrics", required=True, help="Ruta al lyrics.md final.")
    parser.add_argument("--output", required=True, help="Ruta WAV final esperada.")
    parser.add_argument("--checkpoint-path", default="/app/models/music/ace-step", help="Volumen/ruta de checkpoints ACE-Step.")
    parser.add_argument("--duration", type=float, default=60.0, help="Duracion en segundos.")
    parser.add_argument("--infer-step", type=int, default=27)
    parser.add_argument("--guidance-scale", type=float, default=15.0)
    parser.add_argument("--scheduler-type", default="euler")
    parser.add_argument("--cfg-type", default="apg")
    parser.add_argument("--omega-scale", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device-id", type=int, default=0)
    parser.add_argument("--bf16", default="true")
    parser.add_argument("--cpu-offload", default="true")
    parser.add_argument("--overlapped-decode", default="true")
    args = parser.parse_args()

    try:
        from acestep.pipeline_ace_step import ACEStepPipeline
    except ImportError as error:
        raise SystemExit(
            "ACE-Step no esta instalado dentro del contenedor. Activa "
            "SONG_AI_BOOTSTRAP_ON_START=true y SONG_AI_INSTALL_ACE_STEP=true."
        ) from error

    prompt = Path(args.prompt).read_text(encoding="utf-8")
    lyrics = Path(args.lyrics).read_text(encoding="utf-8")
    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    import os

    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.device_id)
    pipeline = ACEStepPipeline(
        checkpoint_dir=str(checkpoint_path),
        dtype="bfloat16" if truthy(args.bf16) else "float32",
        torch_compile=False,
        cpu_offload=truthy(args.cpu_offload),
        overlapped_decode=truthy(args.overlapped_decode),
    )
    pipeline(
        audio_duration=args.duration,
        prompt=prompt,
        lyrics=lyrics,
        infer_step=args.infer_step,
        guidance_scale=args.guidance_scale,
        scheduler_type=args.scheduler_type,
        cfg_type=args.cfg_type,
        omega_scale=args.omega_scale,
        manual_seeds=str(args.seed),
        guidance_interval=0.5,
        guidance_interval_decay=0.0,
        min_guidance_scale=3.0,
        use_erg_tag=True,
        use_erg_lyric=True,
        use_erg_diffusion=True,
        oss_steps="16, 29, 52, 96, 129, 158, 172, 183, 189, 200",
        guidance_scale_text=0.0,
        guidance_scale_lyric=0.0,
        save_path=str(output_path),
    )
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise SystemExit(f"ACE-Step no genero el WAV esperado: {output_path}")
    print(f"Cancion completa generada con ACE-Step: {output_path}")
    return 0


def truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
