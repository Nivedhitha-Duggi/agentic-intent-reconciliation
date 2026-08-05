from __future__ import annotations
import os
from typing import Annotated,List,TypedDict
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END,StateGraph
from langgraph.graph.message import add_messages
from app.core.engine import Engine

class State(TypedDict,total=False):
    messages: Annotated[List[BaseMessage],add_messages]
    desired: dict
    approved: bool
    plan: object
    result: object


def build_graph(engine:Engine):
    llm=ChatOpenAI(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),temperature=0)
    def intent_agent(s):
        r=llm.invoke([SystemMessage(content='You are the Intent Agent. Summarize only the provided DeviceMF, DeviceConfigMF, Uplink, Fiber, and ONT desired intents. Do not invent anything.'),HumanMessage(content=str([x.model_dump(mode='json') for x in s['desired'].values()]))])
        return {'messages':[r]}
    def planner_agent(s):
        p=engine.plan(s['desired'])
        r=llm.invoke([SystemMessage(content='You are the Planner Agent. Explain the trusted deterministic operations without changing their order or content.'),HumanMessage(content=p.model_dump_json(indent=2))])
        p.explanation=r.content
        return {'messages':[r],'plan':p}
    def safety_agent(s):
        p=s['plan']
        r=llm.invoke([SystemMessage(content='You are the Safety Agent. Explain the existing risk and approval requirement. Never lower the risk.'),HumanMessage(content=p.model_dump_json(indent=2))])
        return {'messages':[r]}
    def execute_agent(s): return {'result':engine.run(s['desired'],approved=s.get('approved',False))}
    def verify_agent(s):
        r=llm.invoke([SystemMessage(content='You are the Verification Agent. Summarize the structured result and whether convergence was achieved.'),HumanMessage(content=s['result'].model_dump_json(indent=2))])
        s['result'].summary=r.content
        return {'messages':[r],'result':s['result']}
    def route(s): return 'stop' if s['plan'].requires_approval and not s.get('approved',False) else 'go'
    def stop(s): return {'result':engine.run(s['desired'],approved=False)}
    g=StateGraph(State)
    for n,f in [('intent',intent_agent),('planner',planner_agent),('safety',safety_agent),('execute',execute_agent),('verify',verify_agent),('stop',stop)]: g.add_node(n,f)
    g.set_entry_point('intent'); g.add_edge('intent','planner'); g.add_edge('planner','safety'); g.add_conditional_edges('safety',route,{'go':'execute','stop':'stop'}); g.add_edge('execute','verify'); g.add_edge('verify',END); g.add_edge('stop',END)
    return g.compile()
