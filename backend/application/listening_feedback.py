"""Shared explicit listening feedback contract."""
def validate_listening_feedback(request: dict) -> tuple[str, str]:
    if request.get("listened") is not True:
        raise ValueError("Escucha este audio y confirma su revision antes de guardar tu opinion.")
    decision, notes = request.get("decision"), request.get("notes", "")
    if decision not in ("accepted", "changes_requested"):
        raise ValueError("Indica si corresponde a tu idea o necesita cambios.")
    if not isinstance(notes, str) or len(notes) > 2000:
        raise ValueError("Describe los cambios en hasta 2000 caracteres.")
    if decision == "changes_requested" and not notes.strip():
        raise ValueError("Indica que quieres corregir para orientar el siguiente paso.")
    return decision, notes.strip()
