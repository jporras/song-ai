"""Translate an approved plan into process arguments, without shell interpolation."""
from pathlib import Path


class AceStepExecutionArguments:
    FIELDS = {
        "task_type": "--task-type", "bpm": "--bpm", "key_scale": "--key-scale",
        "time_signature": "--time-signature", "vocal_language": "--vocal-language",
        "audio_duration": "--duration", "src_audio": "--src-audio", "instruction": "--instruction",
        "repainting_start": "--repainting-start", "repainting_end": "--repainting-end",
        "chunk_mask_mode": "--chunk-mask-mode", "audio_cover_strength": "--audio-cover-strength",
    }

    def build(self, item: dict, profile, python: str, directory: Path, output: Path) -> list[str]:
        if item.get("effective_status") != "approved" or item.get("inputs_current") is not True:
            raise ValueError("El plan debe estar aprobado y vigente para traducirlo a ejecucion.")
        plan = item["plan"]
        config = plan["retained_spec"].get("ace_step_config")
        if config != profile.config_path:
            raise ValueError("El perfil no coincide con la configuracion del plan; revisa y aprueba el modelo elegido.")
        payload = plan["payload"]
        unknown = set(payload) - set(self.FIELDS) - {"captions", "lyrics"}
        if unknown:
            raise ValueError("El plan contiene parametros sin traduccion al wrapper.")
        directory.mkdir(parents=True, exist_ok=True)
        prompt = directory / "ace_plan_caption.txt"
        lyrics = directory / "ace_plan_lyrics.md"
        prompt.write_text(payload["captions"], encoding="utf-8")
        lyrics.write_text(payload["lyrics"], encoding="utf-8")
        argv = [python, "tools/acestep_generate.py", "--prompt", str(prompt), "--lyrics", str(lyrics),
                "--output", str(output), "--checkpoint-path", profile.checkpoint_root,
                "--config-path", profile.config_path, "--infer-step", str(profile.infer_steps),
                "--device", profile.device, "--torch-threads", str(profile.threads)]
        argv.extend(("--diagnostics", str(directory / "ace_step_diagnostics.json")))
        for key, flag in self.FIELDS.items():
            if key in payload:
                argv.extend((flag, str(payload[key])))
        return argv
