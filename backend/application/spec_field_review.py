"""Explain field coverage without confusing a stored value with approval."""


def field_review(value, provenance, disposition, applicable, field_id=None):
    present = value not in (None, '', [])
    source = str(provenance.get('source', ''))
    confirmation = provenance.get('confirmation')
    if not applicable:
        return {'decision_status':'not_applicable', 'decision_label':'No se usa en esta acción',
                'review_action':'Se conserva para otras acciones; no necesitas completarlo ahora.'}
    user_source = source in {'explicit_user_phase','explicit_user_control','USER','user'}
    if source == 'explicit_user_delegation':
        return {'decision_status':'delegated', 'decision_label':'Delegado por ti al perfil automático',
                'review_action':'Revisa el perfil y el plan antes de confirmar. Puedes volver a elegir un valor manual.'}
    if (disposition == 'optional_or_delegated_pending_review' and not user_source) or source == 'explicit_delegation_proposal':
        return {'decision_status':'delegation_proposed', 'decision_label':'Delegación propuesta, pendiente de revisar',
                'review_action':('Revisa si quieres dejar este ajuste al perfil automático o elegir un valor. No se acepta por silencio.'
                    if field_id in {'seed','inference_steps','guidance_scale','shift'} else
                    'Revisa si necesitas este ajuste opcional o prefieres dejarlo sin valor. Su disponibilidad depende del motor. No se acepta por silencio.')}
    if present and confirmation == 'confirmed':
        return {'decision_status':'confirmed', 'decision_label':'Decisión confirmada',
                'review_action':'Puedes conservarla o editarla si tu intención cambió.'}
    if present and user_source:
        return {'decision_status':'user_saved', 'decision_label':'Elección guardada por ti',
                'review_action':'Revisa y confirma la configuración completa antes de generar.'}
    if present:
        return {'decision_status':'proposed', 'decision_label':'Valor guardado por revisar',
                'review_action':'Comprueba que representa tu idea; puedes ajustarlo antes de confirmar.'}
    return {'decision_status':'missing', 'decision_label':'Por decidir',
            'review_action':'Elige un valor o pide una recomendación al asistente.'}
