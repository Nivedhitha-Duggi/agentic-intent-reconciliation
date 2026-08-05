# Agentic Intent Reconciliation

A complete clean-room prototype for reconciling telecom intents represented in YAML.

Supported intent types:

- `DeviceMF`
- `DeviceConfigMF`
- `Uplink`
- `Fiber`
- `ONT`

The system reads `data/desired.yaml` and `data/current.yaml`, validates them, detects `ADD`, `MODIFY`, and `DELETE` drift, orders operations by dependency, applies corrections to a digital twin, writes the corrected deployed state back to YAML, and verifies convergence.

## Architecture

```text
desired.yaml + current.yaml
          |
          v
     YAML validation
          |
          v
      Drift engine
          |
          v
 Dependency-aware plan
          |
          v
 Safety + approval gate
          |
          v
 Digital twin execution
          |
          v
  current.yaml rewritten
          |
          v
      Verification
          |
          v
       CONVERGED
```

Real LLM-backed agents are available through LangGraph when an OpenAI API key is configured. The LLM explains and coordinates the trusted plan; deterministic Python still controls all changes.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Run the CLI demo:

```bash
python scripts/run_reconcile.py --approve
```

Start the API:

```bash
uvicorn app.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Start the live dashboard in another terminal:

```bash
streamlit run dashboard.py
```

## Live demo

1. Open `data/current.yaml`.
2. Change the ONT VLAN from `100` to any wrong value, such as `500`.
3. Keep `data/desired.yaml` at VLAN `200`.
4. In the dashboard, click **Reload YAML**, **Preview drift**, then **Run reconciliation**.
5. The plan will show `MODIFY ONT ont-1` with the before/after value.
6. The digital twin applies the change.
7. `data/current.yaml` is rewritten with VLAN `200`.
8. The result becomes `CONVERGED`.

You can also remove a resource from `current.yaml` to trigger `ADD`, or add an extra resource to trigger `DELETE`.

## Real agent mode

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='gpt-4.1-mini'
python scripts/run_agent.py --approve
```
