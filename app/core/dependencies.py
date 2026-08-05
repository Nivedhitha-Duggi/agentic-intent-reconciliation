from app.models import Action,IntentType,Operation
ORDER={IntentType.DEVICE_MF:0,IntentType.DEVICE_CONFIG_MF:1,IntentType.UPLINK:2,IntentType.FIBER:3,IntentType.ONT:4}

def order_operations(ops:list[Operation])->list[Operation]:
    def key(op):
        if op.action==Action.ADD:return (0,ORDER[op.intent_type])
        if op.action==Action.MODIFY:return (1,ORDER[op.intent_type])
        return (2,-ORDER[op.intent_type])
    return sorted(ops,key=key)
