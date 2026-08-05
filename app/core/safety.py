from app.models import Action,Intent,IntentType,Operation,Risk

def enrich(ops:list[Operation])->tuple[Risk,bool]:
    overall=Risk.LOW; approval=False
    for op in ops:
        if op.action==Action.DELETE:
            op.risk=Risk.HIGH if op.intent_type in {IntentType.DEVICE_MF,IntentType.DEVICE_CONFIG_MF,IntentType.UPLINK} else Risk.MEDIUM
            op.requires_approval=True
        elif op.intent_type==IntentType.DEVICE_MF or len(op.changes)>=3:
            op.risk=Risk.MEDIUM; op.requires_approval=True
        approval|=op.requires_approval
        if op.risk==Risk.HIGH: overall=Risk.HIGH
        elif op.risk==Risk.MEDIUM and overall==Risk.LOW: overall=Risk.MEDIUM
    return overall,approval

def validate(ops:list[Operation],current:dict[str,Intent])->None:
    deleting={o.intent_id for o in ops if o.action==Action.DELETE}
    errors=[]
    for op in ops:
        if op.action==Action.DELETE:
            children=[r.intent_id for r in current.values() if r.parent_id==op.intent_id]
            left=[c for c in children if c not in deleting]
            if left: errors.append(f'Cannot delete {op.intent_id}; children remain: {left}')
    if errors: raise ValueError('; '.join(errors))
