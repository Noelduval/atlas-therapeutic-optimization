"""Visible, pre-lock facts for the VITA DP622-S2 / Aβ42 / S2 challenge."""

from typing import Literal

from atlas.domain.enums import Availability, CandidateStatus
from atlas.domain.models import AtlasModel, CampaignConfig, Candidate


class StructuralReference(AtlasModel):
    pdb_id: Literal["23WN"] = "23WN"
    emdb_id: Literal["EMD-69322"] = "EMD-69322"
    construct_name: Literal["DP622 E96Q with Aβ42"] = "DP622 E96Q with Aβ42"
    active_site_variant: Literal["E96Q"] = "E96Q"
    is_active_enzyme: Literal[False] = False
    interpretation: str = (
        "Inactive pre-catalytic structural reference; geometry is not catalytic activity."
    )


class ChallengeDataset(AtlasModel):
    config: CampaignConfig
    seed: Candidate
    source_title: str
    source_doi: str
    abeta42_sequence: str
    s2_context: str
    catalytic_residues: tuple[str, ...]
    structural_reference: StructuralReference
    supplementary_assets: Availability
    visible_information: tuple[str, ...]
    anonymized_control_ids: tuple[str, ...]


def load_visible_challenge() -> ChallengeDataset:
    """Return only facts allowed to enter a campaign before recommendation lock."""
    return ChallengeDataset(
        config=CampaignConfig(),
        seed=Candidate(
            candidate_id="DP622-S2",
            display_name="DP622-S2",
            is_seed=True,
            sequence=None,
            sequence_availability=Availability.UNAVAILABLE,
            status=CandidateStatus.SEED,
        ),
        source_title="De novo design of metalloproteases for targeted amyloid-β cleavage",
        source_doi="10.15302/vita.2026.07.0055",
        abeta42_sequence="DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA",
        s2_context="GLMVGG|VVIA",
        catalytic_residues=("Y91", "E96", "D126", "H172"),
        structural_reference=StructuralReference(),
        supplementary_assets=Availability.UNAVAILABLE,
        visible_information=(
            "DP622-S2 is the canonical active seed candidate.",
            "Aβ42 is the target context and S2 is the cleavage system.",
            "The committed structure is the inactive DP622 E96Q pre-catalytic reference.",
            "Published structural distances may establish a geometry baseline only.",
            "Exact candidate sequences and supplementary design files are unavailable.",
        ),
        anonymized_control_ids=("REFERENCE-CONTROL-001", "REFERENCE-CONTROL-002"),
    )
