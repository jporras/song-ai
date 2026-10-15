"""Translate an approved plan into process arguments, without shell interpolation."""
from pathlib import Path
import json
from models.ace_step_tasks import validate_task_inputs


class AceStepExecutionArguments:
    FIELDS = {
        "generation_api": "--generation-api", "lm_model_path": "--lm-model-path",
        "reference_audio": "--reference-audio", "seed": "--seed",
        "inference_steps": "--infer-step", "guidance_scale": "--guidance-scale", "shift": "--shift",
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
        tracks = plan["retained_spec"].get("target_tracks", [])
        if payload.get("task_type") in {"lego", "extract", "complete"}:
            validate_task_inputs(payload["task_type"], config, payload.get("src_audio", ""),
                                 payload.get("instruction", ""), payload.get("repainting_start", 0),
                                 payload.get("repainting_end", -1), tuple(tracks))
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
                "--config-path", profile.config_path, "--infer-step", str(payload.get("inference_steps", profile.infer_steps)),
                "--device", profile.device, "--torch-threads", str(profile.threads)]
        argv.extend(("--diagnostics", str(directory / "ace_step_diagnostics.json")))
        context_path = directory / 'ace_execution_context.json'
        context_path.write_text(json.dumps({'spec_revision_id':plan.get('spec_revision_id') or plan.get('input_trace', {}).get('spec_revision_id'),
            'plan_sha256':plan.get('plan_sha256'),
            'approved_inputs':payload,
            'wrapper_task_constraints': {'target_tracks': tracks,
                'source': 'approved_plan.retained_spec.target_tracks',
                'cli_rule': 'comma_join', 'scope': 'wrapper_validation_not_native_handler_parameter'},
            'approved_audio_sha256':{entry['target']:entry['audio_sha256']
                for entry in plan.get('input_trace', {}).get('entries', [])
                if entry.get('audio_sha256') and entry['target'] in {'src_audio','reference_audio'}},
            'execution_profile':{'config_path':profile.config_path, 'inference_steps':profile.infer_steps},
            'requested_options':{key:payload[key] for key in ('seed','inference_steps','guidance_scale','shift') if key in payload},
            'provenance':{key:plan['retained_spec'].get('_provenance', {}).get(key, {}) for key in ('seed','inference_steps','guidance_scale','shift')}}, ensure_ascii=False), encoding='utf-8')
        argv.extend(('--execution-context', str(context_path)))
        if payload.get("task_type") in {"lego", "extract", "complete"}:
            argv.extend(("--tracks", ",".join(tracks)))
        for key, flag in self.FIELDS.items():
            if key in payload and key != "inference_steps":
                argv.extend((flag, str(payload[key])))
        return argv
