"""Optional ACE-Step high-level adapter; imports engines only when requested."""
def generate(handler, args, caption, lyrics, diagnostics, output_dir):
    if __package__:
        from .acestep_runtime_options import runtime_options
    else:
        from acestep_runtime_options import runtime_options
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    lm = None
    use_lm = args.generation_api == "high_level_lm"
    observation = {"api": args.generation_api, "lm_requested": use_lm, "lm_used": False,
                   "status": "pending", "rewrites_enabled": False}
    diagnostics["runtime"]["generation_api"] = observation
    if use_lm and args.task_type != "text2music":
        raise ValueError("El ensayo LM solo esta conectado para text2music.")
    try:
        if use_lm:
            from acestep.llm_inference import LLMHandler
            lm = LLMHandler()
            status, ready = lm.initialize(checkpoint_dir=args.checkpoint_path,
                lm_model_path=args.lm_model_path, backend="pt", device="cpu", offload_to_cpu=True)
            observation["initialization"] = str(status)
            observation["lm_model"] = args.lm_model_path
            if not ready or not lm.llm_initialized:
                raise RuntimeError("No se pudo inicializar el LM opcional; no se usara fallback silencioso.")
        params = GenerationParams(task_type=args.task_type, caption=caption, lyrics=lyrics,
            bpm=args.bpm, keyscale=args.key_scale, timesignature=args.time_signature,
            vocal_language=args.vocal_language, duration=args.duration,
            reference_audio=args.reference_audio or None, src_audio=args.src_audio or None,
            inference_steps=args.infer_step, guidance_scale=runtime_options(args)['guidance_scale'],
            seed=args.seed, shift=runtime_options(args)['shift'],
            repainting_start=args.repainting_start, repainting_end=args.repainting_end,
            audio_cover_strength=args.audio_cover_strength, chunk_mask_mode=args.chunk_mask_mode,
            thinking=use_lm, use_cot_caption=False, use_cot_language=False,
            use_cot_metas=False, use_cot_lyrics=False)
        if args.instruction:
            params.instruction = args.instruction
        config = GenerationConfig(batch_size=1, seeds=[args.seed], use_random_seed=False, audio_format="wav")
        result = generate_music(handler, lm, params, config, save_dir=str(output_dir))
        if not result.success or not result.audios:
            raise RuntimeError(str(result.error or "La API de alto nivel no devolvio audio."))
        effective = result.audios[0].get("params", {})
        observation['engine_reported_options'] = {key:effective[key] for key in ('seed','inference_steps','guidance_scale','shift') if key in effective}
        expected_inputs = {
            "task_type": args.task_type, "caption": caption, "lyrics": lyrics,
            "bpm": args.bpm, "keyscale": args.key_scale,
            "timesignature": args.time_signature, "vocal_language": args.vocal_language,
            "duration": args.duration, "reference_audio": args.reference_audio or None,
            "src_audio": args.src_audio or None, "inference_steps": args.infer_step,
            **runtime_options(args), "repainting_start": args.repainting_start,
            "repainting_end": args.repainting_end,
            "audio_cover_strength": args.audio_cover_strength,
            "chunk_mask_mode": args.chunk_mask_mode,
        }
        if args.instruction:
            expected_inputs["instruction"] = args.instruction
        observation["input_correspondence"] = {
            "scope": "engine_reported_parameters_not_audio_fidelity",
            "verified_fields": [], "unreported_fields": [], "mismatched_fields": [],
        }
        correspondence = observation["input_correspondence"]
        for field, expected in expected_inputs.items():
            if field not in effective:
                correspondence["unreported_fields"].append(field)
            elif effective[field] != expected:
                correspondence["mismatched_fields"].append(field)
            else:
                correspondence["verified_fields"].append(field)
        if correspondence["mismatched_fields"]:
            raise RuntimeError("La API modifico entradas aprobadas: " +
                               ", ".join(correspondence["mismatched_fields"]) +
                               "; el resultado no se publicara.")
        for field, expected in (("caption", caption), ("lyrics", lyrics), ("vocal_language", args.vocal_language)):
            if effective.get(field) != expected:
                raise RuntimeError("La API modifico entradas aprobadas; el resultado no se publicara.")
        codes = effective.get("audio_codes")
        if use_lm and not codes:
            raise RuntimeError("El LM solicitado no dejo evidencia de codigos musicales.")
        observation.update(status="reported_completion", lm_used=bool(use_lm and codes),
                           time_costs=result.extra_outputs.get("time_costs", {}), seed=args.seed)
        return {"success": True, "audios": result.audios}
    except Exception:
        observation["status"] = "failed"
        raise
    finally:
        if lm is not None:
            lm.unload()
