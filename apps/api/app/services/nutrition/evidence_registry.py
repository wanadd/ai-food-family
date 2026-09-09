"""Machine-readable evidence registry references for nutrition targets."""

from __future__ import annotations

NUTRITION_TARGET_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-NT-001": {
        "domain": "nutrition_targets",
        "description": "MR 2.3.1.0253-21 table lookup for baseline nutrition targets.",
        "source_id": "SRC-RU-MR-0253-21",
        "source_version": "MR-2.3.1.0253-21@2021-07-22",
        "calculation_method": "mr_2_3_1_0253_21_table_lookup_v1",
        "status": "active",
    }
}

NUTRITION_TARGET_SOURCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "SRC-RU-MR-0253-21": {
        "domain": "nutrition_targets",
        "description": "MR 2.3.1.0253-21 source record for baseline macro targets.",
        "version": "MR-2.3.1.0253-21@2021-07-22",
        "dataset_id": "PLANAM-MR-0253-21-MACRO-TARGETS-v1",
        "status": "verified_for_P0_A2",
    }
}
