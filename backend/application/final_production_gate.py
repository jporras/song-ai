"""Validate persisted production inputs independently of optional sample evidence."""
from application.music_spec_revision_service import require_confirmed_music_spec


class FinalProductionGate:
    def __init__(self, store):
        self.store = store

    def require_for_project(self, project):
        owner = str(project.get("user_id", ""))
        if not owner.startswith("set:") or not owner[4:].strip():
            raise ValueError("Vincula el proyecto a un set valido antes de producir la cancion completa.")
        set_id = owner[4:].strip()
        song_set = self.store.get_indexed_set(set_id)
        if song_set is None:
            raise ValueError("El proyecto necesita un set valido en SQLite antes de producir la cancion completa.")
        self.store.validate_song_set_assets(*(str(song_set[key]) for key in
                                             ("instrumental_id", "melody_id", "lyrics_id")))
        require_confirmed_music_spec(project)
        return song_set
