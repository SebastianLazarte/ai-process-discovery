"""Streamlit client for the AI Process Discovery API.

It talks to the API over HTTP only and never imports the backend package, so the
frontend can be replaced without touching the domain (ADR 0005).
"""

import os
from decimal import Decimal
from typing import Any

import httpx
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")

LEVELS = ["UNKNOWN", "LOW", "MEDIUM", "HIGH"]
INPUT_TYPES = ["UNKNOWN", "DIGITAL_STRUCTURED", "DIGITAL_UNSTRUCTURED", "MIXED", "PHYSICAL"]
INTEGRATION = ["UNKNOWN", "NONE", "PARTIAL", "GOOD"]
METHODS = ["RULE_BASED", "API_INTEGRATION", "AI_CANDIDATE", "HYBRID", "MANUAL", "NEEDS_REVIEW"]
CONTROLS = ["NONE", "RECOMMENDED", "REQUIRED"]


class ApiError(Exception):
    pass


def api(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = httpx.request(method, f"{API_BASE_URL}{path}", timeout=120, **kwargs)
    except httpx.HTTPError as exc:
        raise ApiError(f"Cannot reach the API at {API_BASE_URL}: {exc}") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(f"{response.status_code}: {detail}")
    if response.status_code == 204:
        return None
    if response.headers.get("content-type", "").startswith("text/"):
        return response.text
    return response.json()


def call(method: str, path: str, **kwargs: Any) -> Any:
    try:
        return api(method, path, **kwargs)
    except ApiError as exc:
        st.error(str(exc))
        return None


def fmt_money(value: str | None) -> str:
    return "unknown" if value is None else f"{Decimal(value):,.2f}"


def fmt(value: str | None, suffix: str = "") -> str:
    return "n/a" if value is None else f"{value}{suffix}"


# Sidebar: choose or create a process


def sidebar() -> str | None:
    st.sidebar.title("Processes")
    processes = call("GET", "/processes") or []
    options = {f"{p['name']} (v{p['version']})": p["id"] for p in processes}
    current = st.session_state.get("process_id")
    labels = list(options)
    index = list(options.values()).index(current) if current in options.values() else 0
    if labels:
        choice = st.sidebar.radio("Open", labels, index=index)
        st.session_state["process_id"] = options[choice]

    st.sidebar.divider()
    st.sidebar.subheader("Load a demo process")
    demos = call("GET", "/demo-processes") or []
    for demo in demos:
        if st.sidebar.button(demo["name"], key=f"demo-{demo['slug']}", use_container_width=True):
            created = call("POST", f"/demo-processes/{demo['slug']}")
            if created:
                st.session_state["process_id"] = created["id"]
                st.rerun()

    st.sidebar.divider()
    with st.sidebar.form("new-process", clear_on_submit=True):
        st.subheader("New process")
        name = st.text_input("Name")
        executions = st.number_input("Executions per month", min_value=0, value=100, step=10)
        cost = st.text_input("Hourly cost (leave empty if unknown)")
        if st.form_submit_button("Create") and name:
            payload = {
                "name": name,
                "executions_per_month": int(executions),
                "hourly_cost": cost or None,
            }
            created = call("POST", "/processes", json=payload)
            if created:
                st.session_state["process_id"] = created["id"]
                st.rerun()
    return st.session_state.get("process_id")


# Process tab


def step_form(key: str, step: dict[str, Any] | None = None) -> dict[str, Any] | None:
    s = step or {}
    with st.form(key):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", s.get("name", ""))
        role = c2.text_input("Responsible role", s.get("responsible_role", ""))
        description = st.text_area("Description", s.get("description", ""), height=68)
        c1, c2, c3 = st.columns(3)
        minutes = c1.text_input("Minutes per execution", s.get("minutes_per_execution", "5"))
        occurrence = c2.text_input("Occurrence rate (0-1)", s.get("occurrence_rate", "1"))
        exceptions = c3.text_input(
            "Exception rate (0-1, empty = unknown)", s.get("exception_rate") or ""
        )
        c1, c2, c3 = st.columns(3)
        repetitiveness = c1.selectbox(
            "Repetitiveness", LEVELS, LEVELS.index(s.get("repetitiveness", "UNKNOWN"))
        )
        rule_clarity = c2.selectbox(
            "Rule clarity", LEVELS, LEVELS.index(s.get("rule_clarity", "UNKNOWN"))
        )
        criticality = c3.selectbox(
            "Criticality", LEVELS, LEVELS.index(s.get("criticality", "UNKNOWN"))
        )
        c1, c2 = st.columns(2)
        input_type = c1.selectbox(
            "Input type", INPUT_TYPES, INPUT_TYPES.index(s.get("input_type", "UNKNOWN"))
        )
        integration = c2.selectbox(
            "Integration readiness",
            INTEGRATION,
            INTEGRATION.index(s.get("integration_readiness", "UNKNOWN")),
        )
        tools = st.text_input("Tools (comma separated)", ", ".join(s.get("tools", [])))
        c1, c2, c3 = st.columns(3)
        judgement = c1.checkbox(
            "Requires human judgement", s.get("requires_human_judgement", False)
        )
        approval = c2.checkbox("Requires human approval", s.get("requires_human_approval", False))
        sensitive = c3.checkbox("Handles sensitive data", s.get("handles_sensitive_data", False))
        if not st.form_submit_button("Save step"):
            return None
    return {
        "name": name,
        "responsible_role": role,
        "description": description,
        "minutes_per_execution": minutes,
        "occurrence_rate": occurrence,
        "exception_rate": exceptions or None,
        "repetitiveness": repetitiveness,
        "rule_clarity": rule_clarity,
        "criticality": criticality,
        "input_type": input_type,
        "integration_readiness": integration,
        "tools": [t.strip() for t in tools.split(",") if t.strip()],
        "requires_human_judgement": judgement,
        "requires_human_approval": approval,
        "handles_sensitive_data": sensitive,
    }


def process_tab(process: dict[str, Any]) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Executions per month", process["executions_per_month"])
    c2.metric("Hourly cost", fmt_money(process["hourly_cost"]))
    c3.metric("Version", process["version"])
    if process["description"]:
        st.caption(process["description"])

    st.subheader("Steps")
    steps = process["steps"]
    ids = [s["id"] for s in steps]
    for i, step in enumerate(steps):
        flags = [
            label
            for label, on in (
                ("judgement", step["requires_human_judgement"]),
                ("approval", step["requires_human_approval"]),
                ("sensitive", step["handles_sensitive_data"]),
            )
            if on
        ]
        title = f"{step['position']}. {step['name']}  ·  {step['minutes_per_execution']} min"
        if flags:
            title += f"  ·  {', '.join(flags)}"
        with st.expander(title):
            c1, c2, c3 = st.columns(3)
            if c1.button("Move up", key=f"up-{step['id']}", disabled=i == 0):
                ids[i - 1], ids[i] = ids[i], ids[i - 1]
                call("PUT", f"/processes/{process['id']}/steps/order", json={"step_ids": ids})
                st.rerun()
            if c2.button("Move down", key=f"down-{step['id']}", disabled=i == len(steps) - 1):
                ids[i + 1], ids[i] = ids[i], ids[i + 1]
                call("PUT", f"/processes/{process['id']}/steps/order", json={"step_ids": ids})
                st.rerun()
            if c3.button("Delete", key=f"del-{step['id']}"):
                call("DELETE", f"/steps/{step['id']}")
                st.rerun()
            payload = step_form(f"edit-{step['id']}", step)
            if payload and call("PATCH", f"/steps/{step['id']}", json=payload):
                st.rerun()

    with st.expander("Add a step"):
        payload = step_form(f"add-{process['id']}")
        if payload and call("POST", f"/processes/{process['id']}/steps", json=payload):
            st.rerun()

    if st.button("Delete process", type="secondary"):
        call("DELETE", f"/processes/{process['id']}")
        st.session_state.pop("process_id", None)
        st.session_state.pop("analysis_id", None)
        st.rerun()


# Analyse tab


def analyse_tab(process: dict[str, Any]) -> None:
    st.write(
        "Economic inputs are your assumptions. The system never estimates them and the "
        "LLM never sees them."
    )
    c1, c2 = st.columns(2)
    implementation = c1.text_input("Implementation cost (empty if unknown)")
    tooling = c2.text_input("Monthly tooling cost", "0")
    st.markdown("**Expected time reduction per step**")
    reductions: dict[str, str] = {}
    for step in process["steps"]:
        percent = st.slider(step["name"], 0, 100, 0, step=5, key=f"red-{step['id']}")
        if percent:
            reductions[step["id"]] = str(Decimal(percent) / 100)

    use_llm = st.checkbox("Enrich with the LLM (interpretation, risks, architecture)")
    sensitive = [s["name"] for s in process["steps"] if s["handles_sensitive_data"]]
    confirm = False
    if use_llm and sensitive:
        st.warning(
            "These steps handle sensitive data and their descriptions would be sent to the "
            f"LLM provider: {', '.join(sensitive)}."
        )
        confirm = st.checkbox("I confirm these descriptions can be sent to the provider")

    if st.button(
        "Run analysis", type="primary", disabled=use_llm and bool(sensitive) and not confirm
    ):
        payload = {
            "use_llm": use_llm,
            "confirm_sensitive": confirm,
            "assumptions": {
                "implementation_cost": implementation or None,
                "monthly_tooling_cost": tooling or "0",
                "expected_time_reduction_by_step": reductions,
            },
        }
        analysis = call("POST", f"/processes/{process['id']}/analyses", json=payload)
        if analysis:
            st.session_state["analysis_id"] = analysis["id"]
            st.success("Analysis saved. Open the Results tab.")


# Results tab


def results_tab(analysis: dict[str, Any]) -> None:
    llm = analysis["llm"]
    st.caption(
        f"Analysis {analysis['id'][:8]} · process v{analysis['process_version']} · "
        f"rules {analysis['rules_version']} · LLM {llm['status']}"
        + (
            f" ({llm['provider']}/{llm['model']}, prompt {llm['prompt_version']})"
            if llm["model"]
            else ""
        )
    )
    if llm["status"] == "unavailable":
        st.warning(
            f"The LLM was unavailable ({llm['error_kind']}). Deterministic results are complete."
        )

    state = analysis["current_state"]
    c1, c2 = st.columns(2)
    c1.metric("Current monthly hours", state["monthly_hours"])
    c2.metric("Current monthly cost", fmt_money(state["monthly_cost"]))

    suit, impact, risk, control = st.tabs(
        ["Automation suitability", "Business impact", "Risk", "Human controls"]
    )
    with suit:
        score = analysis["automation_suitability"]["process_score"]
        st.metric("Process suitability (time-weighted, 0-100)", fmt(score))
        st.caption("Suitability says whether a step can be automated, not whether it is worth it.")
        for step in analysis["step_assessments"]:
            st.progress(
                step["suitability_score"] / 100, text=f"{step['name']}: {step['suitability_score']}"
            )
    with impact:
        b = analysis["business_impact"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Hours freed / month", b["estimated_hours_saved"])
        c2.metric("Net monthly savings", fmt_money(b["net_monthly_savings"]))
        c3.metric("Payback (months)", fmt(b["payback_months"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("Gross monthly savings", fmt_money(b["estimated_monthly_savings"]))
        c2.metric("Implementation cost", fmt_money(b["implementation_cost"]))
        roi = b["roi_12_months"]
        c3.metric("ROI at 12 months", "n/a" if roi is None else f"{Decimal(roi) * 100:.0f} %")
        if b["steps_without_reduction"]:
            st.info(
                f"{len(b['steps_without_reduction'])} step(s) have no expected reduction "
                "and count as zero."
            )
    with risk:
        for item in analysis["risks"] or []:
            st.markdown(f"- **{item['source']} / {item['type']}**: {item['description']}")
        if analysis["unknowns"]:
            st.markdown("**Unknowns**")
            for text in analysis["unknowns"]:
                st.markdown(f"- {text}")
    with control:
        for item in analysis["human_controls"] or []:
            st.markdown(
                f"- **{item['step_name']}: {item['control']}**. {'; '.join(item['reasons'])}"
            )
        if not analysis["human_controls"]:
            st.write("No human control required by the rules.")

    st.subheader("Step by step")
    for step in analysis["step_assessments"]:
        header = (
            f"{step['position']}. {step['name']} · {step['final_method']} · "
            f"{step['final_human_control']} · decided by {step['final_source']}"
        )
        with st.expander(header):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Rules:** {step['rules_method']}. {step['rules_method_reason']}")
                st.table(
                    [
                        {
                            "factor": f["name"],
                            "points": f"{f['points']} / {f['max_points']}",
                            "detail": f["detail"],
                        }
                        for f in step["score_factors"]
                    ]
                )
                if step["score_penalties"]:
                    st.markdown(
                        "**Penalties:** "
                        + ", ".join(
                            f"{p['name']} (-{p['points']})" for p in step["score_penalties"]
                        )
                    )
                if step["score_unknowns"]:
                    st.markdown("**Unknown inputs:** " + ", ".join(step["score_unknowns"]))
            with c2:
                ai = step["ai_suggestion"]
                if ai:
                    st.markdown(
                        f"**AI suggestion:** {ai['method']} (confidence {ai['confidence']:.2f})"
                    )
                    st.write(ai["interpretation"])
                    st.caption(ai["rationale"])
                    for label, items in (
                        ("Dependencies", ai["dependencies"]),
                        ("Risks", ai["risks"]),
                        ("Uncertainties", ai["uncertainties"]),
                    ):
                        if items:
                            st.markdown(f"**{label}:** " + "; ".join(items))
                else:
                    st.caption("No AI suggestion for this analysis.")
                for note in step["reconciliation_notes"]:
                    st.caption(f"Reconciliation: {note}")
                if step["override"]:
                    o = step["override"]
                    st.info(
                        f"Overridden from {o['original_method']} / "
                        f"{o['original_human_control']}: {o['reason']}"
                    )
            with st.form(f"override-{analysis['id']}-{step['step_id']}"):
                st.markdown("**Override this recommendation**")
                c1, c2 = st.columns(2)
                method = c1.selectbox("Method", METHODS, METHODS.index(step["final_method"]))
                control_value = c2.selectbox(
                    "Human control", CONTROLS, CONTROLS.index(step["final_human_control"])
                )
                reason = st.text_input("Reason (required)")
                if st.form_submit_button("Save override"):
                    result = call(
                        "POST",
                        f"/analyses/{analysis['id']}/overrides",
                        json={
                            "step_id": step["step_id"],
                            "method": method,
                            "human_control": control_value,
                            "reason": reason,
                        },
                    )
                    if result:
                        st.rerun()


# Blueprint and history tabs


def blueprint_tab(analysis_id: str) -> None:
    markdown = call("GET", f"/analyses/{analysis_id}/blueprint.md")
    if not markdown:
        return
    st.download_button(
        "Download blueprint (.md)",
        markdown,
        file_name=f"blueprint-{analysis_id[:8]}.md",
        mime="text/markdown",
    )
    st.markdown(markdown)


def history_tab(process_id: str) -> None:
    rows = call("GET", f"/processes/{process_id}/analyses") or []
    if not rows:
        st.write("No analyses yet.")
        return
    for row in rows:
        c1, c2 = st.columns([4, 1])
        c1.write(
            f"{row['created_at'][:19]} · v{row['process_version']} · {row['rules_version']} · "
            f"LLM {row['llm_status']} · {row['override_count']} override(s)"
        )
        if c2.button("Open", key=f"open-{row['id']}"):
            st.session_state["analysis_id"] = row["id"]
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="AI Process Discovery", layout="wide")
    st.title("AI Process Discovery & Automation Planner")
    st.caption(
        "Deterministic first: hours, costs, scores and ROI are computed by code. "
        "The LLM only interprets."
    )

    process_id = sidebar()
    if not process_id:
        st.info("Load a demo process or create one from the sidebar.")
        return
    process = call("GET", f"/processes/{process_id}")
    if not process:
        st.session_state.pop("process_id", None)
        return
    st.header(process["name"])

    analysis_id = st.session_state.get("analysis_id")
    analysis = call("GET", f"/analyses/{analysis_id}") if analysis_id else None
    if analysis and analysis["process_id"] != process_id:
        analysis = None

    tabs = st.tabs(["Process", "Analyse", "Results", "Blueprint", "History"])
    with tabs[0]:
        process_tab(process)
    with tabs[1]:
        analyse_tab(process)
    with tabs[2]:
        if analysis:
            results_tab(analysis)
        else:
            st.write("Run an analysis or open one from History.")
    with tabs[3]:
        if analysis:
            blueprint_tab(analysis["id"])
        else:
            st.write("Run an analysis first.")
    with tabs[4]:
        history_tab(process_id)


main()
