"""Deterministic final report rendering with required scientific sections."""

from atlas.domain.models import FinalReport


FINAL_REPORT_HEADINGS = (
    "Summary",
    "Winning Candidate",
    "Reasons It Won",
    "Reasons Alternatives Lost",
    "Confidence",
    "Assumptions",
    "Known Unknowns",
    "Model Disagreements",
    "Scientific Risks",
    "Recommended Experimental Next Steps",
    "Evidence Summary",
)


def _bullets(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None recorded."]


def render_final_report(report: FinalReport) -> str:
    lines = ["# Atlas Final Report", ""]
    lines.extend(["## Summary", "", report.summary, ""])
    lines.extend(
        [
            "## Winning Candidate",
            "",
            f"**{report.winning_candidate}** — recommended for experimental validation.",
            "",
        ]
    )
    lines.extend(["## Reasons It Won", "", *_bullets(report.reasons_it_won), ""])
    lines.extend(["## Reasons Alternatives Lost", ""])
    for candidate_id, reasons in report.reasons_alternatives_lost.items():
        lines.append(f"### {candidate_id}")
        lines.append("")
        lines.extend(_bullets(reasons))
        lines.append("")
    lines.extend(["## Confidence", "", report.confidence, ""])
    lines.extend(["## Assumptions", "", *_bullets(report.assumptions), ""])
    lines.extend(["## Known Unknowns", "", *_bullets(report.known_unknowns), ""])
    lines.extend(
        ["## Model Disagreements", "", *_bullets(report.model_disagreements), ""]
    )
    lines.extend(["## Scientific Risks", "", *_bullets(report.scientific_risks), ""])
    lines.extend(
        [
            "## Recommended Experimental Next Steps",
            "",
            *_bullets(report.recommended_experimental_next_steps),
            "",
        ]
    )
    lines.extend(["## Evidence Summary", "", *_bullets(report.evidence_summary), ""])
    return "\n".join(lines).rstrip() + "\n"
