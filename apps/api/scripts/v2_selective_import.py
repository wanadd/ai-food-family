from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base  # noqa: E402
from app.selective_import.pipeline import ImportConfig, SelectiveImportPipeline, load_source  # noqa: E402

# Import modules so all canonical tables are registered before create_all in a
# disposable rehearsal. Production migration authority remains Alembic.
from app.core import models as core_models  # noqa: F401,E402
from app.food import profile_models  # noqa: F401,E402
from app.recipes import v2_models  # noqa: F401,E402


def main() -> int:
    parser = argparse.ArgumentParser(description="PLANAM V2 selective import rehearsal")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    source, source_hash = load_source(args.source)
    target_path = Path(args.target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{target_path}")
    # The rehearsal target contains only the canonical tables this pipeline
    # touches. Alembic remains the authority for a real PostgreSQL target.
    tables = [
        core_models.CorePerson.__table__,
        core_models.CoreAccount.__table__,
        core_models.CoreAuthIdentity.__table__,
        core_models.CoreHousehold.__table__,
        core_models.CoreMembership.__table__,
        core_models.LegacyIdMapping.__table__,
        profile_models.FoodProfile.__table__,
        profile_models.FoodProfileFact.__table__,
        profile_models.FoodProfileReconfirmation.__table__,
        v2_models.CanonicalRecipe.__table__,
        v2_models.CanonicalRecipeVersion.__table__,
        v2_models.CanonicalLegacyMapping.__table__,
        v2_models.CanonicalArchiveFallback.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version(version_num) VALUES ('20260927_0019')"))
    session = sessionmaker(bind=engine)()
    try:
        report = SelectiveImportPipeline(session, target_url=str(engine.url), config=ImportConfig(code_checkpoint="local-rehearsal")).run(source, source_hash=source_hash, dry_run=args.mode == "dry-run")
    finally:
        session.close()
        engine.dispose()
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.as_dict(), ensure_ascii=True, indent=2), encoding="utf-8")
    summary = report.as_dict()
    report_path.with_suffix(".md").write_text(
        "# W10 Selective Import Report\n\n"
        f"- Batch: `{summary['batch_id']}`\n"
        f"- Source: `{summary['source_identity']}`\n"
        f"- Target schema: `{summary['target_schema_head']}`\n"
        f"- Mode: `{summary['mode']}`\n"
        f"- Source records: `{summary['source_records']}`\n"
        f"- Target records created: `{summary['target_records_created']}`\n"
        f"- Reconfirmation: `{summary['reconfirmation_count']}`\n"
        f"- Archive-only: `{summary['archive_only_count']}`\n"
        f"- Dropped: `{summary['drop_count']}`\n"
        f"- Fatal conflicts: `{summary['unresolved_fatal_conflicts']}`\n\n"
        "Sensitive source values are intentionally excluded. See the adjacent JSON for bounded classifications, mappings and manifest hashes.\n",
        encoding="utf-8",
    )
    print(json.dumps(report.as_dict(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
