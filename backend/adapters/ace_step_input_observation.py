"""Bind wrapper input observations to a plan, separately from engine and quality evidence."""
def inspect_input_observation(trace, plan):
    if not isinstance(trace, dict) or trace.get('status') == 'legacy_context_without_full_input_contract':
        return {'status':'unavailable', 'matches_approved_plan':False,
                'scope':'wrapper_observation_not_engine_or_audio_quality'}
    if plan is None:
        return {'status':'plan_not_compared', 'matches_approved_plan':False,
                'scope':'wrapper_observation_not_engine_or_audio_quality'}
    expected = plan['payload']
    entries = trace.get('entries')
    match = (bool(plan.get('spec_revision_id')) and bool(plan.get('plan_sha256'))
             and trace.get('schema_version') == 'runtime_inputs_v1'
             and trace.get('status') == 'approved_inputs_match'
             and trace.get('spec_revision_id') == plan.get('spec_revision_id')
             and trace.get('plan_sha256') == plan.get('plan_sha256')
             and isinstance(entries, list) and len(entries) == len(expected)
             and all(isinstance(entry, dict) for entry in entries))
    if match:
        names = [entry.get('field') for entry in entries]
        match = all(isinstance(name, str) for name in names) and set(names) == set(expected)
    if match:
        match = all(not isinstance(entry.get('approved_value'), bool)
                    and not isinstance(entry.get('wrapper_value'), bool)
                    and entry.get('approved_value') == expected[entry['field']]
                    and entry.get('wrapper_value') == expected[entry['field']]
                    and entry.get('transformation') == 'approved_request_identity_v1'
                    for entry in entries)
    checksums = {entry['target']:entry['audio_sha256']
                 for entry in plan.get('input_trace',{}).get('entries',[])
                 if entry.get('verification_status') == 'verified_project_audio_artifact'
                 and entry.get('target') in {'src_audio','reference_audio'}}
    if match:
        observed = {entry['field']:entry for entry in entries}
        match = all(observed.get(field,{}).get('verified_audio_sha256') == digest
                    for field,digest in checksums.items())
    return {'status':'matched' if match else 'mismatch', 'matches_approved_plan':bool(match),
            'scope':'wrapper_observation_not_engine_or_audio_quality'}
