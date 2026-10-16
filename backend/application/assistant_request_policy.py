"""Keep conversational proposals independent of optional technical inference."""
import re


def needs_technical_review(question: str, phase_patch: dict) -> bool:
    if phase_patch.get("available"):
        return True
    return bool(re.search(r"\b(revisa|revisar|valida|validar|viabilidad|compatibilidad|compila|compilar|especificacion|especificación|configuracion|configuración|ace[- ]?step)\b", question, re.IGNORECASE))


def conversation_state(readiness: dict) -> dict:
    """Expose current decisions and gates, excluding execution logs and duplicate assets."""
    state = {key: readiness[key] for key in (
        "missing", "recommendations", "saved_editor_phases", "ui_ready_phases",
        "audio_next_action", "candidate_listening", "sample_evaluation", "music_tools"
    ) if key in readiness}
    project = readiness.get("professional_project") or {}
    state["professional_project"] = {key: project[key] for key in (
        "id", "title", "status", "current_phase"
    ) if key in project}
    spec = project.get("spec") or {}
    if spec:
        current = spec.get("json_spec") or {}
        provenance = current.get("_provenance") or {}
        state["professional_project"]["spec"] = {
            "revision": spec.get("revision"),
            "json_spec": {key: value for key, value in current.items() if not key.startswith("_")},
            "field_authority": {key: {name: value.get(name) for name in ("origin", "confirmation")}
                                for key, value in provenance.items() if isinstance(value, dict)},
        }
    return state


def lyric_reference(asset: dict) -> dict:
    manifest = asset.get("manifest") or {}
    mock = "mock" in str(manifest.get("provider", "")).lower()
    return {"asset_id": manifest.get("asset_id"), "manifest": manifest,
            "intent": asset.get("intent", {}),
            "creative_authority": "mock_example_not_confirmed_user_wish" if mock else "existing_draft_review_required",
            "content": None if mock else asset.get("content", "")}


def plain_lyric_proposal(question: str, response: str) -> str:
    """Remove presentation only when an exact requested line count is identifiable."""
    match = re.search(r"\b(\d+|dos|tres|cuatro|cinco|seis|ocho)\s+l[ií]neas\b", question, re.IGNORECASE)
    if not match or not re.search(r"\b(letra|cantables)\b", question, re.IGNORECASE):
        return response
    counts = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "ocho": 8}
    count = counts.get(match[1].lower(), int(match[1]) if match[1].isdigit() else 0)
    lines = [line.strip() for line in response.splitlines() if line.strip()]
    if lines and (re.match(r"^#{1,6}\s+", lines[0]) or
                  re.search(r"(?:(?:l[ií]neas|versos) cantables|propuesta de letra).*:\s*$", lines[0], re.IGNORECASE)):
        lines = lines[1:]
    if len(lines) != count:
        return response
    cleaned = []
    for line in lines:
        line = re.sub(r"^\*\*(.*?)\*\*$", r"\1", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = re.sub(r"^\*\*(.*?)\*\*$", r"\1", line)
        cleaned.append(line)
    return "\n".join(cleaned)
