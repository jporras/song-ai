"""Resolve section assistance from the active persisted project revision."""
from copy import deepcopy
from application.lyric_section_direction import validate_section_directions
from application.lyric_line_protection import validate_line_protection


def creative_spec_context(record):
    if not record:
        return None
    spec = record.get('json_spec', {})
    return {'revision':deepcopy(record.get('revision', {})),
            'json_spec':{key:deepcopy(value) for key,value in spec.items() if not key.startswith('_')},
            'source':'active_sqlite_revision',
            'omitted':'editor projections, provenance history and consolidation diagnostics; creative fields preserved'}


def section_transform_context(project, payload):
    if payload.get('spec_revision_id') != project.get('music_spec_revision_id'):
        raise ValueError('La ficha cambió. Recarga antes de solicitar una propuesta de letra.')
    sections = project.get('phase_data', {}).get('lyrics', {}).get('data', {}).get('lyricSections', [])
    original = next((s for s in sections if s['id'] == payload.get('section_id')), None)
    if original is None:
        raise ValueError('La sección no pertenece al proyecto activo.')
    draft = payload.get('section_draft')
    if not isinstance(draft, dict) or draft.get('id') != original['id'] or draft.get('text') != payload.get('text') or draft.get('type') != payload.get('section_type'):
        raise ValueError('El borrador y la sección solicitada no coinciden.')
    if original.get('locked') or draft.get('locked'):
        raise ValueError('La sección está protegida; guarda su desbloqueo antes de solicitar cambios.')
    validate_line_protection([original], [draft], None)
    validate_section_directions([draft], [original])
    phases = project.get('phase_data', {})
    identity = project.get('project', project)
    return {'project_name':identity.get('project_name', ''), 'description':identity.get('description', ''),
            'intent':deepcopy(phases.get('intent', {}).get('data', {}).get('intent', {})),
            'lyrics':deepcopy(phases.get('lyrics', {}).get('data', {}).get('lyrics', {})),
            'instrumental':deepcopy(phases.get('instrumental', {}).get('data', {}).get('instrumental', {})),
            'voice':deepcopy(phases.get('voice', {}).get('data', {}).get('voice', {})),
            'set':{key:deepcopy(value) for key,value in project.get('set', {}).items()
                   if key in ('set_id','project_name','description','instrumental_id','melody_id','lyrics_id')},
            'selected_assets':{role:{key:deepcopy(asset[key]) for key in
                ('asset_id','asset_type','manifest','intent','metadata','source_of_truth') if key in asset}
                for role, asset in project.get('assets', {}).items()},
            'music_spec':creative_spec_context(project.get('music_spec')),
            'snapshot_references':deepcopy(project.get('snapshot_files', {})),
            'section':deepcopy(draft), 'spec_revision_id':project['music_spec_revision_id']}


def validate_section_result(context, text):
    section = context.get('section', {})
    before, after = section.get('text', '').split('\n'), text.split('\n')
    if any(i >= len(after) or before[i] != after[i] for i in section.get('protected_lines', [])):
        raise ValueError('La propuesta alteró una línea protegida; no se aplicó ningún cambio.')
