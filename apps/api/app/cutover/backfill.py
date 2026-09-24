from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any, Callable, Iterable
from uuid import UUID, uuid5

from app.cutover.manifest import MigrationClass


class Outcome(StrEnum):
    MIGRATED = "MIGRATED"
    RECOMPUTED = "RECOMPUTED"
    RECONFIRM_REQUIRED = "RECONFIRM_REQUIRED"
    ARCHIVED = "ARCHIVED"
    SKIPPED_BY_POLICY = "SKIPPED_BY_POLICY"
    ERROR = "ERROR"


@dataclass(frozen=True)
class BackfillRecord:
    domain: str
    source_table: str
    source_id: str
    migration_class: MigrationClass
    payload: dict[str, Any] = field(default_factory=dict)
    ambiguous: bool = False
    conflicting: bool = False


@dataclass
class BackfillResult:
    run_id: str
    dry_run: bool
    processed: int = 0
    migrated: int = 0
    recomputed: int = 0
    reconfirm_required: int = 0
    archived: int = 0
    skipped_by_policy: int = 0
    errors: int = 0
    error_ids: list[str] = field(default_factory=list)
    checkpoint: str | None = None
    resumed_from: str | None = None

    @property
    def unexplained_source_loss(self) -> int:
        return self.processed - sum((self.migrated, self.recomputed, self.reconfirm_required, self.archived, self.skipped_by_policy, self.errors))

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__ | {"unexplained_source_loss": self.unexplained_source_loss}


class BackfillEngine:
    """Deterministic local backfill engine; persistence is supplied by the caller."""

    NAMESPACE = UUID("4f0a5cc1-4a15-4d1b-9b6e-9e7f4af1f1c1")

    def __init__(self) -> None:
        self.mapping_store: dict[tuple[str, str], str] = {}
        self.outcome_store: dict[tuple[str, str], Outcome] = {}
        self.checkpoints: dict[str, str] = {}

    @classmethod
    def stable_v2_id(cls, source_table: str, source_id: str) -> str:
        return str(uuid5(cls.NAMESPACE, f"{source_table}:{source_id}"))

    def run(
        self,
        records: Iterable[BackfillRecord],
        *,
        run_id: str,
        dry_run: bool = True,
        resume_from: str | None = None,
        fail_after: int | None = None,
        transform: Callable[[BackfillRecord, str], None] | None = None,
    ) -> BackfillResult:
        result = BackfillResult(run_id=run_id, dry_run=dry_run, resumed_from=resume_from)
        ordered = sorted(records, key=lambda item: (item.source_table, item.source_id))
        started = resume_from is None
        for record in ordered:
            key = (record.source_table, record.source_id)
            if not started:
                if self._checkpoint_token(record) == resume_from:
                    started = True
                else:
                    continue
            result.processed += 1
            v2_id = self.stable_v2_id(*key)
            try:
                outcome = self._classify(record)
                if not dry_run:
                    self.mapping_store.setdefault(key, v2_id)
                    self.outcome_store[key] = outcome
                    if transform:
                        transform(record, v2_id)
                self._increment(result, outcome)
                result.checkpoint = self._checkpoint_token(record)
                if fail_after is not None and result.processed >= fail_after:
                    self.checkpoints[run_id] = result.checkpoint
                    raise RuntimeError("BACKFILL_INTERRUPTED_AFTER_CHECKPOINT")
            except RuntimeError:
                raise
            except Exception as exc:
                result.errors += 1
                result.error_ids.append(f"{record.source_table}:{record.source_id}:{type(exc).__name__}")
                result.checkpoint = self._checkpoint_token(record)
        if result.checkpoint:
            self.checkpoints[run_id] = result.checkpoint
        return result

    def _classify(self, record: BackfillRecord) -> Outcome:
        if record.conflicting or record.ambiguous or record.migration_class is MigrationClass.RECONFIRM:
            return Outcome.RECONFIRM_REQUIRED
        return {
            MigrationClass.AUTO_MIGRATE: Outcome.MIGRATED,
            MigrationClass.RECOMPUTE: Outcome.RECOMPUTED,
            MigrationClass.ARCHIVE_ONLY: Outcome.ARCHIVED,
            MigrationClass.COMPATIBILITY_ONLY: Outcome.SKIPPED_BY_POLICY,
            MigrationClass.DO_NOT_MIGRATE: Outcome.SKIPPED_BY_POLICY,
            MigrationClass.DELETE_LATER: Outcome.SKIPPED_BY_POLICY,
        }.get(record.migration_class, Outcome.ERROR)

    @staticmethod
    def _checkpoint_token(record: BackfillRecord) -> str:
        return sha256(f"{record.source_table}:{record.source_id}".encode()).hexdigest()[:24]

    @staticmethod
    def _increment(result: BackfillResult, outcome: Outcome) -> None:
        setattr(result, outcome.value.lower(), getattr(result, outcome.value.lower()) + 1)
