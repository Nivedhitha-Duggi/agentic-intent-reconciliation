from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

class IntentType(str, Enum):
    DEVICE_MF='DeviceMF'
    DEVICE_CONFIG_MF='DeviceConfigMF'
    UPLINK='Uplink'
    FIBER='Fiber'
    ONT='ONT'

class Action(str, Enum):
    ADD='ADD'; MODIFY='MODIFY'; DELETE='DELETE'

class Risk(str, Enum):
    LOW='LOW'; MEDIUM='MEDIUM'; HIGH='HIGH'

class Intent(BaseModel):
    intent_type: IntentType
    intent_id: str=Field(min_length=1)
    parent_id: Optional[str]=None
    version: int=Field(default=1, ge=1)
    attributes: Dict[str,Any]=Field(default_factory=dict)

    @model_validator(mode='after')
    def parent_rule(self):
        if self.intent_type==IntentType.DEVICE_MF and self.parent_id is not None:
            raise ValueError('DeviceMF cannot have parent_id')
        if self.intent_type!=IntentType.DEVICE_MF and not self.parent_id:
            raise ValueError(f'{self.intent_type.value} requires parent_id')
        return self

class Change(BaseModel):
    before: Any=None
    after: Any=None

class Operation(BaseModel):
    operation_id: str
    action: Action
    intent_type: IntentType
    intent_id: str
    parent_id: Optional[str]=None
    desired_attributes: Dict[str,Any]=Field(default_factory=dict)
    current_attributes: Dict[str,Any]=Field(default_factory=dict)
    changes: Dict[str,Change]=Field(default_factory=dict)
    risk: Risk=Risk.LOW
    requires_approval: bool=False

class Plan(BaseModel):
    operations: List[Operation]
    explanation: str=''
    risk: Risk=Risk.LOW
    requires_approval: bool=False

class Record(BaseModel):
    operation_id: str
    stage: str
    status: Literal['SUCCESS','FAILED','SKIPPED']
    message: str
    attempt: int=1

class Result(BaseModel):
    status: Literal['CONVERGED','NO_CHANGES','APPROVAL_REQUIRED','FAILED']
    plan: Optional[Plan]=None
    records: List[Record]=Field(default_factory=list)
    remaining: List[Operation]=Field(default_factory=list)
    final_state: List[Intent]=Field(default_factory=list)
    summary: str=''
