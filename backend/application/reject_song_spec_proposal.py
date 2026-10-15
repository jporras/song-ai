"""Record explicit rejection of a current model proposal without changing MusicSpec."""
from application.song_spec_proposal import latest_current_proposal


class RejectSongSpecProposal:
    def __init__(self, store):
        self.store = store

    def execute(self, song_id, revision_id, task_id):
        project = self.store.get_song_project(song_id)
        if not project or (project.get('spec') or {}).get('revision', {}).get('revision_id') != revision_id:
            raise ValueError('La ficha cambio. Recarga antes de rechazar la propuesta.')
        proposal = latest_current_proposal(self.store.list_tasks(), song_id, revision_id)
        if not proposal or proposal['task_id'] != task_id:
            raise ValueError('Selecciona la propuesta tecnica vigente del proyecto activo.')
        rejection = {'task_id': task_id, 'source_revision_id': revision_id, 'decision': 'rejected',
                     'actor': 'user', 'music_spec_modified': False}
        self.store.create_song_event(song_id=song_id, phase='SONG_SPEC_COLLECTION', status='completed',
            progress=100, active_model='user', message='Propuesta tecnica rechazada; ficha conservada.',
            payload={'song_spec_proposal_review': rejection})
        return rejection


def proposal_is_rejected(store, song_id, proposal):
    return bool(proposal and any(
        event.get('payload', {}).get('song_spec_proposal_review', {}).get('task_id') == proposal['task_id']
        and event['payload']['song_spec_proposal_review'].get('decision') == 'rejected'
        for event in store.list_song_project_events(song_id)))
