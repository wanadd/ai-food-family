from __future__ import annotations

from dataclasses import dataclass

from app.cutover.inventory import inventory_counts
from app.cutover.manifest import manifest_class_counts
from app.v2.migration_authority import current_schema_authority_snapshot


@dataclass(frozen=True)
class C1InventoryReport:
    legacy_surfaces: int
    legacy_writers: int
    legacy_readers: int
    v2_pre_c1: int
    physical_union_pre_c1: int
    authority_overlaps: int
    migration_classes: dict[str, int]


def collect_inventory_report() -> C1InventoryReport:
    snapshot = current_schema_authority_snapshot()
    counts = inventory_counts()
    return C1InventoryReport(
        legacy_surfaces=counts["legacy_surfaces"],
        legacy_writers=counts["legacy_writers"],
        legacy_readers=counts["legacy_readers"],
        v2_pre_c1=len(snapshot.v2_versioned_migration),
        physical_union_pre_c1=len(set().union(*snapshot.by_authority().values())) + 1,
        authority_overlaps=len(snapshot.authority_overlaps),
        migration_classes=manifest_class_counts(),
    )
