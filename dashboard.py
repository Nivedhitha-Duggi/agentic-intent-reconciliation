import requests
import streamlit as st


def flatten_operations(operations):
    rows = []

    for operation in operations:
        action = operation.get("action", "UNKNOWN")
        intent_type = operation.get("intent_type", "Unknown")
        intent_id = operation.get("intent_id", "Unknown")
        changes = operation.get("changes", {})

        if action == "MODIFY" and changes:
            for field, values in changes.items():
                rows.append(
                    {
                        "Action": action,
                        "Intent Type": intent_type,
                        "Intent ID": intent_id,
                        "Field": field,
                        "Current": values.get("before"),
                        "Desired": values.get("after"),
                        "Risk": operation.get("risk", "LOW"),
                    }
                )

        elif action == "ADD":
            rows.append(
                {
                    "Action": action,
                    "Intent Type": intent_type,
                    "Intent ID": intent_id,
                    "Field": "Entire resource",
                    "Current": "Missing",
                    "Desired": "Resource must be created",
                    "Risk": operation.get("risk", "LOW"),
                }
            )

        elif action == "DELETE":
            rows.append(
                {
                    "Action": action,
                    "Intent Type": intent_type,
                    "Intent ID": intent_id,
                    "Field": "Entire resource",
                    "Current": "Resource exists",
                    "Desired": "Resource must be removed",
                    "Risk": operation.get("risk", "LOW"),
                }
            )

    return rows


def count_operations(operations):
    counts = {
        "ADD": 0,
        "MODIFY": 0,
        "DELETE": 0,
    }

    for operation in operations:
        action = operation.get("action")

        if action in counts:
            counts[action] += 1

    return counts


st.set_page_config(
    page_title="Agentic Intent Reconciliation",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Agentic Intent Reconciliation")
st.caption("DeviceMF · DeviceConfigMF · Uplink · Fiber · ONT")


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

api = st.sidebar.text_input(
    "API URL",
    "http://127.0.0.1:8000",
).rstrip("/")

if st.sidebar.button(
    "Check API",
    use_container_width=True,
):
    try:
        response = requests.get(
            f"{api}/",
            timeout=10,
        )

        if response.ok:
            st.sidebar.success("API is running")
        else:
            st.sidebar.error(
                f"API returned status {response.status_code}"
            )

    except Exception as exc:
        st.sidebar.error(f"Unable to connect: {exc}")


st.sidebar.markdown("---")
st.sidebar.markdown("### Supported intents")
st.sidebar.markdown(
    """
- DeviceMF
- DeviceConfigMF
- Uplink
- Fiber
- ONT
"""
)


# ---------------------------------------------------------
# Load YAML
# ---------------------------------------------------------

if (
    st.button("↻ Reload YAML")
    or "yamls" not in st.session_state
):
    try:
        response = requests.get(
            f"{api}/yaml",
            timeout=10,
        )
        response.raise_for_status()

        st.session_state.yamls = response.json()

        st.session_state.pop("plan", None)
        st.session_state.pop("result", None)

    except Exception as exc:
        st.error(f"Unable to load YAML: {exc}")
        st.stop()


# ---------------------------------------------------------
# YAML panels
# ---------------------------------------------------------

st.subheader("1. Intent YAML")

left, right = st.columns(2)

with left:
    st.markdown("#### Desired state")

    st.code(
        st.session_state.yamls["desired"],
        language="yaml",
    )

with right:
    st.markdown("#### Current / deployed state")

    current_text = st.text_area(
        "Edit deployed YAML live",
        value=st.session_state.yamls["current"],
        height=520,
        label_visibility="collapsed",
    )

    if st.button(
        "💾 Save current YAML",
        use_container_width=True,
    ):
        try:
            response = requests.post(
                f"{api}/yaml/current",
                json={
                    "yaml_text": current_text,
                },
                timeout=15,
            )

            if response.ok:
                st.session_state.yamls["current"] = current_text

                st.session_state.pop("plan", None)
                st.session_state.pop("result", None)

                st.success(
                    "Current YAML saved and validated"
                )

            else:
                st.error(response.text)

        except Exception as exc:
            st.error(f"Unable to save YAML: {exc}")


# ---------------------------------------------------------
# Reconciliation controls
# ---------------------------------------------------------

st.subheader("2. Detect and reconcile")

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "🔎 Preview drift",
        use_container_width=True,
    ):
        try:
            response = requests.get(
                f"{api}/plan",
                timeout=20,
            )
            response.raise_for_status()

            st.session_state.plan = response.json()
            st.session_state.pop("result", None)

        except Exception as exc:
            st.error(
                f"Unable to generate plan: {exc}"
            )

with col2:
    approved = st.checkbox(
        "Approve risky operations"
    )

    if st.button(
        "▶ Run reconciliation",
        type="primary",
        use_container_width=True,
    ):
        try:
            response = requests.post(
                f"{api}/reconcile",
                json={
                    "approved": approved,
                },
                timeout=60,
            )
            response.raise_for_status()

            st.session_state.result = response.json()

            if st.session_state.result.get("plan"):
                st.session_state.plan = (
                    st.session_state.result["plan"]
                )

            yaml_response = requests.get(
                f"{api}/yaml",
                timeout=10,
            )
            yaml_response.raise_for_status()

            st.session_state.yamls = yaml_response.json()

        except Exception as exc:
            st.error(
                f"Reconciliation failed: {exc}"
            )


# ---------------------------------------------------------
# Reconciliation summary
# ---------------------------------------------------------

if "plan" in st.session_state:
    plan = st.session_state.plan
    operations = plan.get("operations", [])
    counts = count_operations(operations)

    st.subheader("3. Reconciliation summary")

    metric1, metric2, metric3, metric4, metric5 = st.columns(5)

    metric1.metric(
        "Operations",
        len(operations),
    )

    metric2.metric(
        "ADD",
        counts["ADD"],
    )

    metric3.metric(
        "MODIFY",
        counts["MODIFY"],
    )

    metric4.metric(
        "DELETE",
        counts["DELETE"],
    )

    metric5.metric(
        "Plan risk",
        plan.get("risk", "LOW"),
    )

    st.markdown("#### Detected drift")

    drift_rows = flatten_operations(operations)

    if drift_rows:
        st.dataframe(
            drift_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No drift detected. "
            "Desired and deployed states already match."
        )


# ---------------------------------------------------------
# Plan display
# ---------------------------------------------------------

if "plan" in st.session_state:
    st.subheader("4. Trusted remediation plan")

    plan = st.session_state.plan
    operations = plan.get("operations", [])

    if operations:
        for index, operation in enumerate(
            operations,
            start=1,
        ):
            action = operation.get(
                "action",
                "UNKNOWN",
            )

            intent_type = operation.get(
                "intent_type",
                "Unknown",
            )

            intent_id = operation.get(
                "intent_id",
                "Unknown",
            )

            with st.expander(
                f"Step {index}: "
                f"{action} "
                f"{intent_type} "
                f"— {intent_id}",
                expanded=True,
            ):
                st.write(
                    f"**Risk:** "
                    f"`{operation.get('risk', 'LOW')}`"
                )

                st.write(
                    "**Approval:** "
                    + (
                        "`Required`"
                        if operation.get(
                            "requires_approval"
                        )
                        else "`Not required`"
                    )
                )

                changes = operation.get(
                    "changes",
                    {},
                )

                if changes:
                    rows = []

                    for field, values in changes.items():
                        rows.append(
                            {
                                "Field": field,
                                "Current": values.get(
                                    "before"
                                ),
                                "Desired": values.get(
                                    "after"
                                ),
                            }
                        )

                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                else:
                    st.json(operation)

    else:
        st.success(
            "No drift detected. "
            "Desired and deployed states match."
        )


# ---------------------------------------------------------
# Result display
# ---------------------------------------------------------

if "result" in st.session_state:
    st.subheader("5. Execution result")

    result = st.session_state.result
    status = result.get(
        "status",
        "UNKNOWN",
    )

    summary = result.get(
        "summary",
        "",
    )

    if status in {
        "CONVERGED",
        "NO_CHANGES",
    }:
        st.success(
            f"{status}: {summary}"
        )

    elif status == "APPROVAL_REQUIRED":
        st.warning(
            f"{status}: {summary}"
        )

    else:
        st.error(
            f"{status}: {summary}"
        )

    records = result.get(
        "records",
        [],
    )

    if records:
        st.markdown("#### Execution records")

        st.dataframe(
            records,
            use_container_width=True,
            hide_index=True,
        )

    remaining = result.get(
        "remaining",
        [],
    )

    if remaining:
        st.markdown("#### Remaining drift")

        st.json(remaining)

    with st.expander(
        "Raw workflow result"
    ):
        st.json(result)


# ---------------------------------------------------------
# Final YAML
# ---------------------------------------------------------

st.subheader("6. Final deployed YAML")

st.code(
    st.session_state.yamls["current"],
    language="yaml",
)