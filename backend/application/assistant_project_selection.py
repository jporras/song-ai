"""Resolve one persisted song/set context before any model handoff."""
def resolve_assistant_song(store, song_id, set_id):
    if not song_id:
        return set_id, None
    song = store.get_song_project(song_id)
    if song is None:
        raise ValueError('El proyecto solicitado no existe. Selecciona un proyecto vigente.')
    owner = str(song.get('user_id', ''))
    linked_set = owner[4:].strip() if owner.startswith('set:') else ''
    if set_id and set_id != linked_set:
        raise ValueError('La ficha y el set pertenecen a proyectos distintos. Recarga el proyecto activo.')
    return linked_set, song
