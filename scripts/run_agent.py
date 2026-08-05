from pathlib import Path
import argparse,os
from app.yamlio.files import load_yaml
from app.simulator.twin import DigitalTwin
from app.core.engine import Engine
from app.agents.workflow import build_graph
if not os.getenv('OPENAI_API_KEY'): raise SystemExit('OPENAI_API_KEY required')
BASE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--approve',action='store_true'); a=p.parse_args()
d=load_yaml(BASE/'data/desired.yaml'); c=load_yaml(BASE/'data/current.yaml'); engine=Engine(DigitalTwin(c),BASE/'data/current.yaml')
out=build_graph(engine).invoke({'desired':d,'approved':a.approve,'messages':[]})
print(out['result'].model_dump_json(indent=2))
