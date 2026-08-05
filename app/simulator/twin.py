from __future__ import annotations
from copy import deepcopy
from app.models import Action,Intent,Operation

class TwinError(RuntimeError): pass

class DigitalTwin:
    def __init__(self,state:dict[str,Intent]):
        self.state=deepcopy(state); self.failures={}
    def snapshot(self): return deepcopy(self.state)
    def inject_failure(self,intent_id:str,count:int=1): self.failures[intent_id]=count
    def apply(self,op:Operation):
        if self.failures.get(op.intent_id,0)>0:
            self.failures[op.intent_id]-=1; raise TwinError(f'Injected temporary failure for {op.intent_id}')
        if op.action==Action.ADD:
            if op.intent_id in self.state: raise TwinError(f'{op.intent_id} already exists')
            if op.parent_id and op.parent_id not in self.state: raise TwinError(f'Missing parent {op.parent_id}')
            self.state[op.intent_id]=Intent(intent_type=op.intent_type,intent_id=op.intent_id,parent_id=op.parent_id,attributes=deepcopy(op.desired_attributes),version=1)
        elif op.action==Action.MODIFY:
            if op.intent_id not in self.state: raise TwinError(f'{op.intent_id} missing')
            old=self.state[op.intent_id]
            self.state[op.intent_id]=Intent(intent_type=op.intent_type,intent_id=op.intent_id,parent_id=op.parent_id,attributes=deepcopy(op.desired_attributes),version=old.version+1)
        elif op.action==Action.DELETE:
            children=[r.intent_id for r in self.state.values() if r.parent_id==op.intent_id]
            if children: raise TwinError(f'Children still exist: {children}')
            self.state.pop(op.intent_id,None)
