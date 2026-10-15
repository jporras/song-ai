"""One grounded next step from persisted candidate and sample context."""
class NextAudioAction:
    def choose(self, candidate: dict, sample: dict) -> dict | None:
        action = None
        if candidate.get("status") not in {"reviewed", "listening_pending", "audio_unavailable"} and sample.get("status") not in {"evaluation_pending", "evaluated", "historical_evaluation"}:
            return None
        if sample.get("status") == "set_pending":
            action = ("prepare_set", "Confirma un set con instrumental, melodia vocal y letra antes de crear el sample.")
        elif sample.get("status") in {"evaluation_pending", "evaluated", "historical_evaluation"}:
            if (sample.get("listening_review") or {}).get("review_current") is False:
                action = ("listen_updated_sample", "Tu opinion del sample es anterior. Revisa el set y escucha un sample vigente antes de aprobarlo.")
            elif (sample.get("listening_review") or {}).get("decision") == "changes_requested":
                action = ("review_sample_changes", "Revisa los cambios que anotaste para el sample antes de aprobarlo o generar otro.")
            elif sample.get("status") == "historical_evaluation":
                action = ("reevaluate_sample", "La comprobacion del sample es anterior. Vuelve a comprobarlo con el plan actual.")
            elif ((sample.get("report") or {}).get("signal_metrics") or {}).get("digital_silence") is True:
                action = ("replace_silent_sample", "El sample contiene solo silencio digital. Genera otro candidato y revisa su audio.")
            elif sample.get("approval_status") != "approved":
                action = ("listen_sample", "Escucha el sample y decide si lo apruebas o que necesitas corregir.")
            elif sample.get("status") == "evaluation_pending":
                action = ("evaluate_sample", "Comprueba la correspondencia del sample con el plan vigente.")
            elif not sample.get("report", {}).get("configuration_matches"):
                action = ("update_candidate", "El sample no coincide con los datos actuales. Revisa el plan y genera un candidato actualizado.")
            else:
                action = ("complete_sample_evidence", "Completa las evidencias pendientes si quieres usar el sample como prueba de calidad. El sample no es requisito para generar la cancion completa.")
        elif candidate.get("status") == "audio_unavailable":
            action = ("replace_candidate", "El audio revisado cambio o no esta disponible. Genera otro candidato para escucharlo.")
        elif candidate.get("status") == "listening_pending":
            action = ("listen_candidate", "Escucha el candidato y registra si corresponde a tu idea o necesita cambios.")
        elif candidate.get("status") == "reviewed":
            review = candidate.get("review") or {}
            if review.get("inputs_current") is not True:
                action = ("review_plan", "Tu opinion corresponde a una version anterior. Revisa el plan vigente y genera otro candidato.")
            elif review.get("decision") == "changes_requested":
                if (candidate.get("correction") or {}).get("inputs_current") is True:
                    action = ("review_correction_controls", "Revisa tu propuesta guardada en los controles de audio y tus notas en la ficha musical. Guarda y confirma la nueva revision antes de preparar el plan.")
                else:
                    action = ("review_changes", "Revisa los cambios que anotaste y prepara una propuesta para ajustar el plan sin perder tu idea.")
            elif review.get("decision") == "accepted":
                action = ("create_sample", "Puedes crear un sample opcional de este candidato y revisarlo por separado, o continuar con la revision de la cancion completa.")
        return {"code": action[0], "message": action[1], "final_generation_ready": False} if action else None
