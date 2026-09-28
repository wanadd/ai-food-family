from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base  # noqa: E402
from app.selective_import.pipeline import ImportConfig, SelectiveImportPipeline, load_source  # noqa: E402
from app.selective_import.cutover_target import verify_cutover_target  # noqa: E402
from app.selective_import.pipeline import ImportPipelineError  # noqa: E402

# Import modules so all canonical tables are registered before create_all in a
# disposable rehearsal. Production migration authority remains Alembic.
from app.core import models as core_models  # noqa: F401,E402
from app.food import profile_models  # noqa: F401,E402
from app.recipes import v2_models  # noqa: F401,E402
from app.shopping import v2_models as shopping_models  # noqa: E402
from app.nutrition.target_models import NutritionTargetVersion  # noqa: E402
from app.notifications.v2_models import NotificationPreference  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="PLANAM V2 selective import rehearsal")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target")
    parser.add_argument("--target-url")
    parser.add_argument("--environment", choices=("DISPOSABLE", "CUTOVER"), default="DISPOSABLE")
    parser.add_argument("--allow-production-target", action="store_true")
    parser.add_argument("--expected-head")
    parser.add_argument("--source-db-name")
    parser.add_argument("--confirm-source-snapshot")
    parser.add_argument("--confirm-target-db")
    parser.add_argument("--confirm-apply", action="store_true")
    parser.add_argument("--previous-report")
    parser.add_argument("--code-checkpoint", default="local-rehearsal")
    parser.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        return _run(args)
    except (ImportPipelineError, SQLAlchemyError, OSError, ValueError) as exc:
        # Never echo a DB URL, source row, or driver exception to a cutover log.
        print(f"IMPORT_BLOCKED:{type(exc).__name__}", file=sys.stderr)
        return 2


def _run(args: argparse.Namespace) -> int:
    source, source_hash = load_source(args.source)
    if args.environment == "CUTOVER":
        if args.target or not args.target_url or not args.allow_production_target:
            raise ImportPipelineError("CUTOVER target authorization incomplete")
        if args.expected_head != "20260928_0020" or not args.source_db_name or not args.confirm_target_db:
            raise ImportPipelineError("CUTOVER identity confirmation incomplete")
        if args.mode == "apply" and not args.confirm_apply:
            raise ImportPipelineError("CUTOVER apply acknowledgement missing")
        if args.previous_report and args.mode != "apply":
            raise ImportPipelineError("previous report is only valid for apply idempotency")
        return _run_cutover(args, source, source_hash)
    if args.target_url or not args.target or args.allow_production_target or args.confirm_apply:
        raise ImportPipelineError("DISPOSABLE accepts only a local rehearsal target")
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
        core_models.EntitlementGrant.__table__,
        core_models.EntitlementConsumption.__table__,
        shopping_models.ShoppingList.__table__,
        shopping_models.ShoppingItem.__table__,
        NutritionTargetVersion.__table__,
        NotificationPreference.__table__,
    ]
    Base.metadata.create_all(engine, tables=tables)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version(version_num) VALUES ('20260928_0020')"))
    session = sessionmaker(bind=engine)()
    try:
        report = SelectiveImportPipeline(session, target_url=str(engine.url), config=ImportConfig(code_checkpoint=args.code_checkpoint)).run(source, source_hash=source_hash, dry_run=args.mode == "dry-run")
    finally:
        session.close()
        engine.dispose()
    _write_report(args.report, report)
    return 0


def _run_cutover(args: argparse.Namespace, source: dict, source_hash: str) -> int:
    url = make_url(args.target_url)
    if not url.drivername.startswith("postgresql") or not url.database:
        raise ImportPipelineError("CUTOVER requires a PostgreSQL URL")
    if args.confirm_target_db != url.database or args.source_db_name == url.database:
        raise ImportPipelineError("CUTOVER target identity mismatch")
    if source.get("snapshot") != args.confirm_source_snapshot or source.get("source_database") != args.source_db_name:
        raise ImportPipelineError("CUTOVER source identity mismatch")
    previous_counts = None
    if args.previous_report:
        previous = json.loads(Path(args.previous_report).read_text(encoding="utf-8"))
        if (previous.get("mode") != "IMPORT" or previous.get("environment") != "CUTOVER"
                or previous.get("target_database") != args.confirm_target_db
                or previous.get("target_schema_head") != args.expected_head
                or previous.get("manifest", {}).get("source_sha256") != source_hash):
            raise ImportPipelineError("CUTOVER idempotency source mismatch")
        previous_counts = previous.get("import_table_counts")
        if not isinstance(previous_counts, dict):
            raise ImportPipelineError("CUTOVER idempotency report incomplete")
    engine = create_engine(args.target_url, pool_pre_ping=True)
    try:
        database, table_counts = verify_cutover_target(
            engine, expected_database=args.confirm_target_db, source_database=args.source_db_name,
            expected_head=args.expected_head, previous_counts=previous_counts,
        )
        config = ImportConfig(
            target_environment="CUTOVER", production_import_override=True,
            code_checkpoint=args.code_checkpoint, source_database_name=args.source_db_name,
            confirmed_source_snapshot=args.confirm_source_snapshot,
            confirmed_target_database=database,
        )
        if args.mode == "dry-run":
            with engine.connect() as connection:
                connection.execute(text("SET TRANSACTION READ ONLY"))
                session = sessionmaker(bind=connection)()
                try:
                    report = SelectiveImportPipeline(session, target_url=url.render_as_string(hide_password=True), config=config).run(source, source_hash=source_hash, dry_run=True)
                finally:
                    session.close()
                    connection.rollback()
        else:
            session = sessionmaker(bind=engine)()
            try:
                report = SelectiveImportPipeline(session, target_url=url.render_as_string(hide_password=True), config=config).run(source, source_hash=source_hash, dry_run=False)
            finally:
                session.close()
        report_dict = report.as_dict()
        if args.mode == "apply":
            table_counts = _actual_counts(engine, table_counts)
        report_dict["import_table_counts"] = table_counts
        _write_report(args.report, report_dict)
        return 0
    finally:
        engine.dispose()


def _actual_counts(engine, before_counts: dict[str, int]) -> dict[str, int]:
    with engine.connect() as connection:
        quote = engine.dialect.identifier_preparer.quote
        return {name: int(connection.execute(text(f"SELECT count(*) FROM {quote(name)}")).scalar_one()) for name in before_counts}


def _write_report(path: str, report) -> None:
    summary = report if isinstance(report, dict) else report.as_dict()
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
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
    print(json.dumps({
        key: summary[key] for key in (
            "mode", "environment", "target_database", "source_records", "target_records_created",
            "reconfirmation_count", "archive_only_count", "drop_count", "rejected_count",
            "unresolved_fatal_conflicts", "target_schema_head", "target_counts",
        )
    }, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
