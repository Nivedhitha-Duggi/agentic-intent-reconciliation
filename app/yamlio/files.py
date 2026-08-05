from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable
import yaml
from app.models import Intent

def load_yaml(path: str|Path)->Dict[str,Intent]:
    path=Path(path)
    data=yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    resources=data.get('resources')
    if not isinstance(resources,list):
        raise ValueError("YAML must contain a 'resources' list")
    parsed=[Intent.model_validate(x) for x in resources]
    ids=[x.intent_id for x in parsed]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate intent_id detected')
    state={x.intent_id:x for x in parsed}
    validate_parents(state)
    return state

def validate_parents(state: Dict[str,Intent])->None:
    for r in state.values():
        if r.parent_id and r.parent_id not in state:
            raise ValueError(f'{r.intent_id} references missing parent {r.parent_id}')

def write_yaml(path: str|Path, resources: Iterable[Intent])->None:
    payload={'resources':[r.model_dump(mode='json') for r in resources]}
    Path(path).write_text(yaml.safe_dump(payload,sort_keys=False),encoding='utf-8')
