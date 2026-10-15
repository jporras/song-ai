"""Value kinds shared by proposal decoding and deterministic validation."""
NUMBER_CONTROLS = frozenset({'number', 'seconds', 'duration', 'bpm'})
LIST_CONTROLS = frozenset({'list', 'multi_choice', 'ordered_list'})
