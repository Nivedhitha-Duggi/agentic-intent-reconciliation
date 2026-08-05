from pathlib import Path
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from app.yamlio.files import load_yaml
from app.simulator.twin import DigitalTwin
from app.core.engine import Engine

BASE=Path(__file__).resolve().parents[2]; DESIRED=BASE/'data/desired.yaml'; CURRENT=BASE/'data/current.yaml'
app=FastAPI(title='Agentic Intent Reconciliation API',version='1.0')

class RunRequest(BaseModel): approved: bool=False
class EditRequest(BaseModel): yaml_text: str

def context():
    desired=load_yaml(DESIRED); current=load_yaml(CURRENT); twin=DigitalTwin(current); return desired,current,twin,Engine(twin,CURRENT)

@app.get('/')
def root(): return {'service':'Agentic Intent Reconciliation','docs':'/docs'}
@app.get('/yaml')
def get_yaml(): return {'desired':DESIRED.read_text(),'current':CURRENT.read_text()}
@app.post('/yaml/current')
def set_current(req:EditRequest):
    CURRENT.write_text(req.yaml_text,encoding='utf-8')
    try: load_yaml(CURRENT)
    except Exception as e: raise HTTPException(400,str(e))
    return {'status':'saved'}
@app.get('/plan')
def plan():
    desired,_,_,engine=context(); return engine.plan(desired)
@app.post('/reconcile')
def reconcile(req:RunRequest):
    desired,_,_,engine=context(); return engine.run(desired,approved=req.approved)
