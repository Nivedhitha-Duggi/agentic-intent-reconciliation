from pathlib import Path
from app.yamlio.files import load_yaml
from app.core.drift import detect
from app.core.dependencies import order_operations
from app.simulator.twin import DigitalTwin
from app.core.engine import Engine
BASE=Path(__file__).resolve().parents[1]

def fresh(): return load_yaml(BASE/'data/desired.yaml'),load_yaml(BASE/'data/current.yaml')

def test_detects_three_modifies():
    d,c=fresh(); ops=order_operations(detect(d,c)); assert [o.intent_type.value for o in ops]==['DeviceConfigMF','Fiber','ONT']

def test_converges(tmp_path):
    d,c=fresh(); out=tmp_path/'current.yaml'; out.write_text((BASE/'data/current.yaml').read_text())
    result=Engine(DigitalTwin(c),out).run(d,approved=True); assert result.status=='CONVERGED'; assert detect(d,load_yaml(out))==[]

def test_add_order(tmp_path):
    d,c=fresh(); c.pop('ont-1'); ops=order_operations(detect(d,c)); add_ops=[o for o in ops if o.action.value=='ADD']; assert len(add_ops)==1; assert add_ops[0].intent_type.value=='ONT'

def test_delete_needs_approval(tmp_path):
    d,c=fresh(); d.pop('ont-1'); out=tmp_path/'current.yaml'; out.write_text((BASE/'data/current.yaml').read_text())
    result=Engine(DigitalTwin(c),out).run(d,approved=False); assert result.status=='APPROVAL_REQUIRED'

def test_retry(tmp_path):
    d,c=fresh(); out=tmp_path/'current.yaml'; out.write_text((BASE/'data/current.yaml').read_text()); twin=DigitalTwin(c); twin.inject_failure('ont-1',1)
    result=Engine(twin,out).run(d,approved=True); assert result.status=='CONVERGED'; assert any(r.status=='FAILED' for r in result.records)
