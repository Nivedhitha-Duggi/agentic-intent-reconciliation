from __future__ import annotations
from pathlib import Path
from app.models import Plan,Record,Result
from app.core.drift import detect
from app.core.dependencies import order_operations
from app.core.safety import enrich,validate
from app.simulator.twin import DigitalTwin,TwinError
from app.yamlio.files import write_yaml

class Engine:
    def __init__(self,twin:DigitalTwin,current_yaml:Path,max_retries:int=2):
        self.twin=twin; self.current_yaml=Path(current_yaml); self.max_retries=max_retries
    def plan(self,desired):
        current=self.twin.snapshot(); ops=order_operations(detect(desired,current)); validate(ops,current)
        risk,approval=enrich(ops)
        return Plan(operations=ops,explanation=f'Generated {len(ops)} trusted dependency-aware operations.',risk=risk,requires_approval=approval)
    def run(self,desired,approved=False):
        plan=self.plan(desired)
        if not plan.operations:
            return Result(status='NO_CHANGES',plan=plan,final_state=list(self.twin.snapshot().values()),summary='No drift detected.')
        if plan.requires_approval and not approved:
            return Result(status='APPROVAL_REQUIRED',plan=plan,final_state=list(self.twin.snapshot().values()),summary='Approval required.')
        records=[]
        for op in plan.operations:
            ok=False
            for attempt in range(1,self.max_retries+2):
                try:
                    self.twin.apply(op); records.append(Record(operation_id=op.operation_id,stage='executor',status='SUCCESS',message=f'{op.action.value} {op.intent_id}',attempt=attempt)); ok=True; break
                except TwinError as e:
                    records.append(Record(operation_id=op.operation_id,stage='executor',status='FAILED',message=str(e),attempt=attempt))
            if not ok:
                rem=order_operations(detect(desired,self.twin.snapshot()))
                write_yaml(self.current_yaml,self.twin.snapshot().values())
                return Result(status='FAILED',plan=plan,records=records,remaining=rem,final_state=list(self.twin.snapshot().values()),summary=f'Failed on {op.intent_id}')
        write_yaml(self.current_yaml,self.twin.snapshot().values())
        rem=order_operations(detect(desired,self.twin.snapshot()))
        return Result(status='CONVERGED' if not rem else 'FAILED',plan=plan,records=records,remaining=rem,final_state=list(self.twin.snapshot().values()),summary='Desired and current YAML now match.' if not rem else 'Drift remains.')
