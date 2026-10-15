"""One-time, backed-up consolidation of the two researched local songs.

First run against a copy with --data-dir. --apply is explicitly required.
No models, audio generation or creative confirmation run here.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from core.storage import StorageManager
from application.project_consolidation import ProjectConsolidation
from application.ace_step_plan_compiler import AceStepPlanCompiler

PROJECTS = {'song_2ea83a928856': 'Isabella', 'song_7eed9f0d14d6': 'Alma'}


def resolution(store, song_id, recipient):
    project = store.get_song_project(song_id)
    phases = store.list_project_phase_data(project['user_id'][4:])
    sections = phases['lyrics']['data']['lyricSections']
    old = project['spec']['json_spec']
    voice = phases['voice']['data']['voice']
    instruments = ['piano', 'music box', 'soft pad', 'cello', 'violin'] if recipient == 'Alma' else ['piano', 'music box', 'soft pad', 'cinematic strings']
    spec = dict(title=recipient, project_name=recipient,
        creative_brief=f'Canción de cuna para {recipient}, tierna y poética, con acompañamiento suave y voz femenina cantada. Conservar íntegramente la letra editada del proyecto.',
        description=f'Canción de cuna para {recipient}.', song_type='lullaby', recipient_name=recipient,
        language='Spanish', theme=f'Canción de cuna para {recipient}: sueño tranquilo, luna, estrellas y cariño.',
        emotion='warm and tender', voice_style='soft warm female lead vocal, consistent singer',
        bpm=old['bpm'], key=old['key'], duration_seconds=old['duration_seconds'], time_signature='4/4',
        structure=[s['type'].lower() for s in sections], instruments=instruments,
        groove='gentle lullaby pulse', dynamic_arc='gentle growth, calm ending',
        vocal_expression=voice['performance'], pronunciation=voice['pronunciation'],
        vocal_range='comfortable middle register', vocal_layers=['lead'],
        lyrical_tone='tender', narrator='caring first-person voice',
        required_phrases=['Alma'] if recipient == 'Alma' else [], excluded_content=[],
        rhyme_preference='preserve existing lyrics', production_route='integrated_song',
        sample_duration_seconds=30, mix_balance='clear lead vocal over soft accompaniment',
        output_format=old['output_format'], quality_profile='technical_and_full_listening_review_pending',
        generation_api='direct', task_type='text2music', ace_step_config='acestep-v15-turbo')
    # Timing is deliberately left delegated: saved lyrics do not prove measured timing.
    direction = [{'id': s['id'], 'section': s['type'], 'singer': 'lead', 'voices': 1,
                  'mode': 'solo', 'harmony': False} for s in sections]
    plan_sections = [{'id': s['id'], 'name': s['type'], 'seconds': None,
                      'intensity': 25, 'transition': 'crescendo',
                      'timing_status': 'delegated_pending_audio', 'origin': 'codex_proposal'} for s in sections]
    return {'recipient': recipient, 'spec': spec, 'section_direction': direction, 'plan_sections': plan_sections,
        'instrumental_description': f"Canción de cuna lenta a {spec['bpm']} BPM en {spec['key']}, 4/4. {', '.join(instruments)}. Ambiente cálido, nocturno y envolvente; evitar golpes bruscos. Intención de arreglo, sin prometer ejecución DSP.",
        'melody_description': f"Voz femenina suave y cálida para {recipient}. {voice['performance']}. {voice['pronunciation']}. Una voz principal; frases cantables, registro medio cómodo propuesto. Seguir las {len(sections)} secciones de la letra conservada. No es una partitura MIDI ni una grabación humana.",
        'field_notes': {'recipient_name': 'Nombre del proyecto y letra editada prevalecen sobre defaults heredados.',
                        'structure': 'Secuencia literal de lyricSections SQLite; no añadir puente ni coro.',
                        'bpm': 'Coincide en ficha e intención guardadas; no usar BPM 96 del asset mock.',
                        'duration_seconds': 'Objetivo histórico, no duración garantizada.',
                        'voice_style': 'Voz generada propuesta; no clonación ni identidad humana acreditada.'},
        'conflicts': ['Se prioriza la letra editada SQLite sobre la letra del asset compartido.',
            'Estructura de letra real prevalece sobre plantilla de siete secciones y plan de 88 segundos.',
            'Una voz principal: armonías y call-response de plantilla contradicen opciones guardadas desactivadas.',
            'Se recuperan instrumentos y BPM del proyecto, no los del mock compartido.'] +
            (['Destinatario Alma; Isabella era un default heredado contradictorio con título y letra.'] if recipient == 'Alma' else [])}


def backup(data):
    target = data/'rescue_20261007'/'before_consolidation'
    if target.exists():
        raise RuntimeError('Ya existe respaldo: verificar resultado previo antes de repetir una migración parcial.')
    target.mkdir(parents=True)
    with sqlite3.connect(f'file:{(data/"song_ai.sqlite").as_posix()}?mode=ro', uri=True) as source:
        with sqlite3.connect(target/'song_ai.sqlite') as destination:
            source.backup(destination)
    for name in ('sets', 'drafts', 'projects', 'songs', 'samples'):
        if (data/name).exists():
            shutil.copytree(data/name, target/name)
    return target


def run(data, apply=False):
    data = data.resolve()
    if not apply:
        print(json.dumps({'status': 'preview_only', 'projects': PROJECTS, 'data_dir': str(data)}, ensure_ascii=False))
        return
    # Backup precedes even schema initialization.
    with sqlite3.connect(f'file:{(data/"song_ai.sqlite").as_posix()}?mode=ro', uri=True) as connection:
        specs = [json.loads(row[0]) for row in connection.execute('SELECT json_spec FROM song_specs WHERE song_id IN (?,?)', tuple(PROJECTS))]
    if len(specs) != 2:
        raise RuntimeError('No están ambos proyectos originales; no aplicar sobre otra base.')
    if all(s.get('_consolidation', {}).get('version') == ProjectConsolidation.VERSION for s in specs):
        print(json.dumps({'status': 'already_consolidated'}))
        return
    target = backup(data)
    store = StorageManager(data)
    results = []
    for song_id, recipient in PROJECTS.items():
        resolved = resolution(store, song_id, recipient)
        provisional = {'json_spec': resolved['spec'], 'missing_fields': [],
                       'revision': {'revision_id': 'validation-only', 'deterministic_valid': True, 'user_confirmation_status': 'confirmed'}}
        source_project = store.get_song_project(song_id)
        lyrics = store.list_project_phase_data(source_project['user_id'][4:])['lyrics']['data']['lyricsEditor']['content']
        AceStepPlanCompiler().compile(provisional, lyrics)
        result = ProjectConsolidation(store).execute(song_id, resolved)
        audio = []
        for artifact in store.get_song_project(song_id)['artifacts']:
            if artifact['type'] in ('final_song_wav', 'final_song_mp3', 'final_song_flac'):
                path = Path(artifact['file_path'])
                info = {'artifact_id': artifact['artifact_id'], 'path': str(path), 'exists': path.is_file()}
                if path.is_file():
                    info['sha256'] = store.file_checksum(path)
                    original = target/'projects'/song_id/path.name
                    if not original.is_file() or store.file_checksum(original) != info['sha256']:
                        raise RuntimeError('El audio original no coincide con el respaldo.')
                    if path.suffix.lower() == '.wav':
                        with wave.open(str(path), 'rb') as wav:
                            info['duration_seconds'] = wav.getnframes()/wav.getframerate()
                    store.song_workflow_repository.update_artifact_metadata(artifact['artifact_id'],
                        {**artifact['metadata'], 'recovered_audio': True, 'current_spec_acceptance': 'not_evaluated',
                         'recovered_sha256': info['sha256']})
                audio.append(info)
        results.append({**result, 'audio_evidence': audio})
    # Nonmusical smoke fixture stays recoverable, outside the working library.
    for item in store.set_repository.list_sets():
        if item['set_id'] not in {store.get_song_project(key)['user_id'][4:] for key in PROJECTS}:
            if item['project_name'] != 'Prueba local dos estrofas':
                raise RuntimeError('Proyecto adicional desconocido: no clasificar automáticamente.')
            item['compatibility_data']['workspace_role'] = 'fixture'
            store.save_song_set(__import__('models.song_set', fromlist=['SongSet']).SongSet.from_dict(item))
    selected = {value for result in results for value in result.get('asset_ids', {}).values()}
    for item in store.list_asset_drafts(include_superseded=True):
        if item['asset_id'] not in selected:
            path = Path(item['path'])/'metadata.json'
            meta = store.read_json(path)
            meta.setdefault('metadata', {})['workspace_role'] = 'superseded'
            store.write_json(path, meta)
    report = {'version': ProjectConsolidation.VERSION, 'backup': str(target), 'projects': results,
              'active_projects': len(store.list_song_projects()), 'active_sets': len(store.list_indexed_sets()),
              'active_assets': len(store.list_asset_drafts()), 'creative_review': 'pending', 'audio_generated': False}
    store.write_json(data/'rescue_20261007'/'consolidation_report.json', report)
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    run(args.data_dir, args.apply)
