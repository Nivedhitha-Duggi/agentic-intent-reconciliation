from pathlib import Path
import argparse
from app.yamlio.files import load_yaml
from app.simulator.twin import DigitalTwin
from app.core.engine import Engine
BASE=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(); p.add_argument('--approve',action='store_true'); p.add_argument('--inject-failure'); a=p.parse_args()
d=load_yaml(BASE/'data/desired.yaml'); c=load_yaml(BASE/'data/current.yaml'); twin=DigitalTwin(c)
if a.inject_failure:twin.inject_failure(a.inject_failure,1)
result=Engine(twin,BASE/'data/current.yaml').run(d,approved=a.approve)
print(result.model_dump_json(indent=2))
