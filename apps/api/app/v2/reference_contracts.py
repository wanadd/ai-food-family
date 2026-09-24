from __future__ import annotations

from enum import Enum


class StableReferenceEnum(str, Enum):
    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(member.value for member in cls)


class KnowledgeState(StableReferenceEnum):
    UNKNOWN = "UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"
    KNOWN_NONE = "KNOWN_NONE"
    KNOWN_PRESENT = "KNOWN_PRESENT"


class EvidenceReviewStatus(StableReferenceEnum):
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REVIEWED_ACCEPTED = "REVIEWED_ACCEPTED"
    REVIEWED_REJECTED = "REVIEWED_REJECTED"
    SUPERSEDED = "SUPERSEDED"


class ProvenanceState(StableReferenceEnum):
    UNKNOWN = "UNKNOWN"
    SOURCE_BACKED = "SOURCE_BACKED"
    USER_ASSERTED = "USER_ASSERTED"
    DERIVED = "DERIVED"
    AI_PROPOSED = "AI_PROPOSED"


class LifecycleState(StableReferenceEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"


REFERENCE_ENUM_CONTRACTS: dict[str, tuple[str, ...]] = {
    enum_cls.__name__: enum_cls.values()
    for enum_cls in (
        KnowledgeState,
        EvidenceReviewStatus,
        ProvenanceState,
        LifecycleState,
    )
}
