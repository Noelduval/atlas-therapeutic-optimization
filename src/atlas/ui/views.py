"""Evidence-backed Streamlit views for the locked Atlas v1 program."""

import tempfile
from pathlib import Path

import streamlit as st

from atlas.benchmark import run_benchmark
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.models import CampaignConfig
from atlas.rendering import render_scientific_notebook
from atlas.workflow.graph import CampaignRun, run_campaign


_DESCRIPTION = (
    "Start from the published DP622-S2 Aβ-cleaving metalloprotease and run a blinded "
    "autonomous computational optimization campaign against Aβ42."
)


def _metadata() -> None:
    rows = (
        ("Starting candidate", "DP622-S2"),
        ("Target context", "Aβ42"),
        ("Cleavage system", "S2"),
        ("Campaign type", "Blinded retrospective benchmark"),
        ("Experimental labels", "Hidden"),
        ("Optimization mode", "Constrained scaffold optimization"),
    )
    html = ['<div class="atlas-metadata">']
    html.extend(
        f'<div class="atlas-row"><div class="atlas-key">{key}</div><div class="atlas-value">{value}</div></div>'
        for key, value in rows
    )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_challenge() -> None:
    st.title("Atlas Challenge")
    st.subheader("Alzheimer’s Aβ Metalloprotease Optimization")
    st.markdown(f'<p class="atlas-description">{_DESCRIPTION}</p>', unsafe_allow_html=True)
    _metadata()
    phase = st.session_state.atlas_phase
    if phase == "unloaded":
        if st.button("Load Atlas Challenge", type="primary", key="load_challenge"):
            st.session_state.atlas_phase = "loaded"
            st.rerun()
    elif phase == "loaded":
        if st.button("Start Campaign", type="primary", key="start_campaign"):
            with st.spinner("Running deterministic demo_cached campaign…"):
                run_dir = Path(tempfile.mkdtemp(prefix="atlas-ui-challenge-"))
                st.session_state.atlas_run = run_campaign(
                    CampaignConfig(), run_dir, profile="demo_cached"
                )
            st.session_state.atlas_phase = "complete"
            st.rerun()
    else:
        run: CampaignRun = st.session_state.atlas_run
        st.success(
            f"Campaign complete: {run.final_report.status.value} · Recommendation: "
            f"{run.final_report.winning_candidate}"
        )
        st.markdown(run.final_report.summary)


def render_run_monitor(run: CampaignRun) -> None:
    st.title("Run Monitor")
    st.markdown('<div class="atlas-kicker">DP622-S2 / Aβ42 / S2</div>', unsafe_allow_html=True)
    st.subheader("Recommendation")
    st.markdown(f"### {run.final_report.winning_candidate}")
    st.code(run.final_report.status.value, language=None)
    st.markdown(run.recommendation_lock.rationale)
    st.subheader("Evidence confidence")
    st.info(
        "Synthetic demo evidence is used for orchestration demonstration only and is not measured evidence."
    )
    st.subheader("Timeline")
    st.dataframe(
        [
            {
                "#": event.sequence,
                "Stage": event.stage.replace("_", " ").title(),
                "Status": "completed",
                "Provenance": event.payload.get("provenance", "workflow"),
            }
            for event in run.events
        ],
        hide_index=True,
        width="stretch",
    )
    st.subheader("Model disagreements")
    for conflict in run.final_report.model_disagreements:
        st.warning(conflict)


def render_candidates(run: CampaignRun) -> None:
    st.title("Candidates")
    st.caption("The original seed and every rejected synthetic demo hypothesis remain visible.")
    rows = [
        {
            "Candidate": run.final_report.winning_candidate,
            "Disposition": "recommended",
            "Reason": "Seed retained; no variant cleared the promotion margin.",
        }
    ]
    rows.extend(
        {
            "Candidate": candidate,
            "Disposition": "rejected",
            "Reason": " ".join(reasons),
        }
        for candidate, reasons in run.final_report.reasons_alternatives_lost.items()
    )
    st.dataframe(rows, hide_index=True, width="stretch")


def render_structures() -> None:
    dataset = load_visible_challenge()
    reference = dataset.structural_reference
    st.title("Structures")
    st.subheader("DP622 E96Q / Aβ42 structural reference")
    st.markdown(
        f"**PDB:** `{reference.pdb_id}`  \n**EMDB:** `{reference.emdb_id}`  "
        f"\n**Construct:** `{reference.construct_name}`"
    )
    st.warning(
        "This is the inactive E96Q pre-catalytic structural reference. Catalytic geometry is not catalytic activity."
    )
    st.markdown(
        "The paper reports close agreement between the design and cryo-EM structure, while emphasizing "
        "that sub-angstrom catalytic preorganization remains difficult."
    )


def render_evidence(run: CampaignRun) -> None:
    st.title("Evidence")
    st.info(
        "Synthetic demo evidence — deterministic orchestration fixtures, not biological model output and not measured evidence."
    )
    st.dataframe(
        [
            {
                "Dimension": record.kind.value.replace("_", " ").title(),
                "Score": record.score,
                "Provenance": record.provenance.value,
                "Interpretation": record.summary,
            }
            for record in run.evidence
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption("No synthetic catalytic kinetics are generated or displayed.")


def render_notebook(run: CampaignRun) -> None:
    st.title("Scientific Notebook")
    st.markdown(render_scientific_notebook(run.events))


def render_benchmarks() -> None:
    st.title("Benchmarks")
    if st.session_state.atlas_benchmark is None:
        output_dir = Path(tempfile.mkdtemp(prefix="atlas-ui-benchmark-"))
        st.session_state.atlas_benchmark = run_benchmark("demo_cached", output_dir)
    result = st.session_state.atlas_benchmark
    st.markdown(f"**Single benchmark family:** `{result.benchmark_family}`")
    st.warning(
        "Negative retrospective result: the demo recommendation did not recover a published optimized control."
    )
    st.dataframe(
        [
            {
                "Experiment": experiment.name,
                "Winner": experiment.winner,
                "Negative result": experiment.negative_result,
                "Conclusion": experiment.conclusion,
            }
            for experiment in result.experiments
        ],
        hide_index=True,
        width="stretch",
    )


def render_methods() -> None:
    st.title("Methods")
    st.markdown(
        "Atlas v1 uses a typed LangGraph workflow, deterministic synthetic demo adapters, a hash-chained "
        "scientific event ledger, a pre-lock hidden-label firewall, Pareto ranking, and a deterministic "
        "Scientific Critic. Future adapters expose interfaces for sequence, proposal, structure, complex "
        "interaction, and OpenMM simulation systems."
    )
    st.warning(
        "The demo does not claim biological model performance, experimental improvement, therapeutic validation, or clinical relevance."
    )


def render_selected_view(selection: str, run: CampaignRun) -> None:
    renderers = {
        "Atlas Challenge": render_challenge,
        "Run Monitor": lambda: render_run_monitor(run),
        "Candidates": lambda: render_candidates(run),
        "Structures": render_structures,
        "Evidence": lambda: render_evidence(run),
        "Scientific Notebook": lambda: render_notebook(run),
        "Benchmarks": render_benchmarks,
        "Methods": render_methods,
    }
    renderers[selection]()
