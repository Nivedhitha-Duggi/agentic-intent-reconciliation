from __future__ import annotations
from typing import Any,Dict,List
from uuid import uuid4
from app.models import Action,Change,Intent,Operation

IGNORE={'last_updated','runtime_id','controller_metadata'}

def norm(v:Any)->Any:
    if isinstance(v,str):
        s=v.strip()
        if s.lower() in {'enabled','disabled','active','inactive'}: return s.lower()
        if s.isdigit(): return int(s)
        return s
    if isinstance(v,list):
        vals=[norm(x) for x in v]
        try:return sorted(vals)
        except TypeError:return vals
    if isinstance(v,dict): return {k:norm(v[k]) for k in sorted(v) if k not in IGNORE}
    return v

def attrs(r:Intent)->dict:
    return {k:norm(v) for k,v in sorted(r.attributes.items()) if k not in IGNORE}

def detect(desired:Dict[str,Intent], current:Dict[str,Intent])->List[Operation]:
    ops=[]
    for iid,d in desired.items():
        c=current.get(iid)
        if c is None:
            ops.append(Operation(operation_id=str(uuid4()),action=Action.ADD,intent_type=d.intent_type,intent_id=iid,parent_id=d.parent_id,desired_attributes=attrs(d)))
            continue
        da,ca=attrs(d),attrs(c)
        keys=sorted(set(da)|set(ca))
        changes={k:Change(before=ca.get(k),after=da.get(k)) for k in keys if ca.get(k)!=da.get(k)}
        meta=(d.intent_type!=c.intent_type or d.parent_id!=c.parent_id)
        if changes or meta:
            ops.append(Operation(operation_id=str(uuid4()),action=Action.MODIFY,intent_type=d.intent_type,intent_id=iid,parent_id=d.parent_id,desired_attributes=da,current_attributes=ca,changes=changes))
    for iid,c in current.items():
        if iid not in desired:
            ops.append(Operation(operation_id=str(uuid4()),action=Action.DELETE,intent_type=c.intent_type,intent_id=iid,parent_id=c.parent_id,current_attributes=attrs(c)))
    return ops
