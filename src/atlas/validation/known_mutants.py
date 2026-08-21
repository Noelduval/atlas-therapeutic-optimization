"""Published benchmark labels used only for validation classification."""

from __future__ import annotations

import pandas as pd


PUBLISHED_ACTIVITY = (
    ("WT", 325.26, "reference"),
    ("Y91F", 474.19, "beneficial-looking"),
    ("D126A", 384.62, "beneficial-looking"),
    ("H172A", 232.60, "regressive"),
    ("Y91F_D126A", 161.46, "strongly regressive"),
)


def published_benchmark_table() -> pd.DataFrame:
    return pd.DataFrame(
        PUBLISHED_ACTIVITY,
        columns=[
            "variant_id",
            "published_efficiency_m_inv_s_inv",
            "published_trend",
        ],
    )
