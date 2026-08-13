"""Visible, pre-lock facts for the VITA DP622-S2 / Aβ42 / S2 challenge."""

from typing import Literal

from atlas.domain.enums import Availability, CandidateStatus
from atlas.domain.models import AtlasModel, CampaignConfig, Candidate
from atlas.challenge.assets import load_asset_manifest, load_sequence_assets


class StructuralReference(AtlasModel):
    pdb_id: Literal["23WN"] = "23WN"
    emdb_id: Literal["EMD-69322"] = "EMD-69322"
    construct_name: Literal["DP622 E96Q with Aβ42"] = "DP622 E96Q with Aβ42"
    active_site_variant: Literal["E96Q"] = "E96Q"
    is_active_enzyme: Literal[False] = False
    coordinate_asset: str = "references/structures/23WN.cif"
    coordinate_sha256: str
    metadata_asset: str = "references/structures/EMD-69322_metadata.json"
    metadata_sha256: str
    asset_availability: Literal[Availability.AVAILABLE] = Availability.AVAILABLE
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
    manifest = load_asset_manifest()
    sequences = {
        record["candidate_name"]: record for record in load_sequence_assets()
    }
    seed_record = sequences["DP622-S2"]
    pdb_asset = manifest["assets"]["pdb_23wn"]
    emdb_asset = manifest["assets"]["emdb_69322_metadata"]
    supplement = manifest["assets"]["vita_supplementary"]
    return ChallengeDataset(
        config=CampaignConfig(),
        seed=Candidate(
            candidate_id="DP622-S2",
            display_name="DP622-S2",
            is_seed=True,
            sequence=seed_record["sequence"],
            sequence_availability=Availability[seed_record["availability"]],
            status=CandidateStatus.SEED,
        ),
        source_title="De novo design of metalloproteases for targeted amyloid-β cleavage",
        source_doi="10.15302/vita.2026.07.0055",
        abeta42_sequence="DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA",
        s2_context="GLMVGG|VVIA",
        catalytic_residues=("Y91", "E96", "D126", "H172"),
        structural_reference=StructuralReference(
            coordinate_sha256=pdb_asset["sha256"],
            metadata_sha256=emdb_asset["sha256"],
        ),
        supplementary_assets=Availability[supplement["availability"]],
        visible_information=(
            "DP622-S2 is the canonical active seed candidate.",
            "Aβ42 is the target context and S2 is the cleavage system.",
            "The recovered structure is the inactive DP622 E96Q pre-catalytic reference.",
            "Published structural distances may establish a geometry baseline only.",
            "The inactive deposited E96Q fusion-construct sequence is source-backed.",
            "The exact active seed and optimized-control sequences remain unavailable.",
            "Publisher Supplementary Information is available; named optimized-enzyme design files remain unavailable.",
        ),
        anonymized_control_ids=("REFERENCE-CONTROL-001", "REFERENCE-CONTROL-002"),
    )
