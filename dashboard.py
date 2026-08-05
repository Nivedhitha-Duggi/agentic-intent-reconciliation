from pathlib import Path
import requests,streamlit as st
st.set_page_config(page_title='Agentic Intent Reconciliation',layout='wide')
st.title('Agentic Intent Reconciliation')
st.caption('DeviceMF · DeviceConfigMF · Uplink · Fiber · ONT')
api=st.sidebar.text_input('API URL','http://127.0.0.1:8000')
if st.button('Reload YAML') or 'yamls' not in st.session_state:
    try: st.session_state.yamls=requests.get(f'{api}/yaml',timeout=10).json()
    except Exception as e: st.error(e); st.stop()
left,right=st.columns(2)
with left:
    st.subheader('Desired YAML'); st.code(st.session_state.yamls['desired'],language='yaml')
with right:
    st.subheader('Current / deployed YAML'); current_text=st.text_area('Edit deployed YAML live',st.session_state.yamls['current'],height=520,label_visibility='collapsed')
    if st.button('Save current YAML'):
        r=requests.post(f'{api}/yaml/current',json={'yaml_text':current_text},timeout=15)
        if r.ok: st.success('Saved and validated'); st.session_state.yamls['current']=current_text
        else: st.error(r.text)
col1,col2=st.columns(2)
with col1:
    if st.button('Preview drift',use_container_width=True):
        r=requests.get(f'{api}/plan',timeout=20); st.session_state.plan=r.json()
with col2:
    approved=st.checkbox('Approve risky operations')
    if st.button('Run reconciliation',type='primary',use_container_width=True):
        r=requests.post(f'{api}/reconcile',json={'approved':approved},timeout=60); st.session_state.result=r.json(); st.session_state.yamls=requests.get(f'{api}/yaml').json()
if 'plan' in st.session_state:
    st.subheader('Trusted remediation plan'); st.json(st.session_state.plan)
if 'result' in st.session_state:
    st.subheader('Execution result'); st.json(st.session_state.result)
