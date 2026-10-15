"""Dispatch explicit regeneration commands to injected application use cases."""


class ArtifactRegeneration:
    OPERATIONS = {
        'lyrics_markdown':'lyrics', 'lyrics_json':'lyrics', 'lyrics_approved_json':'lyrics_review',
        'music_plan_json':'music_plan', 'midi':'midi', 'midi_metadata_json':'midi',
        'instrumental_wav':'instrumental', 'vocals_wav':'vocals',
        'vocals_converted_wav':'voice_conversion', 'mix_wav':'mix',
        'final_song_wav':'master', 'final_song_mp3':'master', 'final_song_flac':'master',
        'export_manifest_json':'export', 'project_zip':'export',
    }

    def __init__(self, handlers):
        self.handlers = handlers

    def execute(self, song_id, artifact_type):
        operation = self.OPERATIONS.get(artifact_type)
        if operation not in self.handlers:
            raise ValueError(f'No hay regenerador registrado para {artifact_type}.')
        return self.handlers[operation](song_id)
