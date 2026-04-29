# app/services/__init__.py
from .module_result import ModuleResult
from .logical_contradiction import detect as detect_logical_contradiction
from .fact_grounding import detect as detect_fact_grounding
from .temporal_inconsistency import detect as detect_temporal_inconsistency
from .topic_shift import detect as detect_topic_shift

__all__ = [
    'ModuleResult',
    'detect_logical_contradiction',
    'detect_fact_grounding',
    'detect_temporal_inconsistency',
    'detect_topic_shift',
]
