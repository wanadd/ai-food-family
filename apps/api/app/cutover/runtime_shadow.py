from __future__ import annotations

from app.cutover.runtime_reconciliation import DatabaseReconciliation


class PostgresShadowEngine(DatabaseReconciliation):
    """Read-only shadow comparison over real legacy and V2 tables."""

    def run(self, **kwargs):
        return self.compare_tables(**kwargs)
