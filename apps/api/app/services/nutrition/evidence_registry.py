"""Machine-readable evidence registry references for nutrition targets.

P0-A1 only defines canonical identifiers and where future rules belong. It does
not encode normative nutrient values or formulas.
"""

from __future__ import annotations

NUTRITION_TARGET_EVIDENCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "EV-NT-001": {
        "domain": "nutrition_targets",
        "description": "Future atomic rule for nutrition target resolution.",
        "source_id": "SRC-RU-MR-0253-21",
        "source_version": None,
        "status": "reserved_for_p0_a2",
    }
}

NUTRITION_TARGET_SOURCE_REGISTRY: dict[str, dict[str, str | None]] = {
    "SRC-RU-MR-0253-21": {
        "domain": "nutrition_targets",
        "description": "Future source record for MR 2.3.1.0253-21.",
        "version": None,
        "status": "reserved_for_p0_a2",
    }
}
