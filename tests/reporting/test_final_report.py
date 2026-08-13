from atlas.domain.models import CampaignConfig
from atlas.reporting import FINAL_REPORT_HEADINGS, render_final_report
from atlas.workflow.graph import run_campaign


def test_final_report_renders_every_required_section(tmp_path) -> None:
    report = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached").final_report
    rendered = render_final_report(report)
    assert tuple(
        line.removeprefix("## ") for line in rendered.splitlines() if line.startswith("## ")
    ) == FINAL_REPORT_HEADINGS
    assert "DP622-S2" in rendered
    assert "ATLAS-V001" in rendered
    assert "recommended for experimental validation" in rendered


def test_final_report_preserves_scientific_claim_boundaries(tmp_path) -> None:
    report = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached").final_report
    rendered = render_final_report(report).lower()
    for forbidden_claim in (
        "discovers a cure",
        "validates an alzheimer’s therapeutic",
        "proves disease modification",
        "clinical success",
        "experimentally improved dp622",
    ):
        assert forbidden_claim not in rendered
    assert "catalytic geometry does not establish catalytic activity" in rendered
    assert "synthetic demo evidence" in rendered
