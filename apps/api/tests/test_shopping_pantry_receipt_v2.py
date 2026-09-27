from pathlib import Path
from app.shopping.v2_contracts import ShoppingDemandV2, ReceiptProposalV2, can_merge_demands, checked_item_proves_pantry, ocr_is_verified_purchase

ROOT = Path(__file__).parents[1]
MIGRATION = ROOT / "alembic" / "versions" / "20260927_0016_wave_5_shopping_pantry_receipt.py"


def test_unknown_and_manual_demand_do_not_merge_or_become_stock():
    unknown = ShoppingDemandV2("milk", None, "l", "PLAN")
    known = ShoppingDemandV2("milk", 1, "l", "PLAN")
    assert unknown.quantity_state == "UNKNOWN"
    assert not can_merge_demands(unknown, known)
    assert not checked_item_proves_pantry("CHECKED")


def test_receipt_proposal_is_observation_until_verified():
    proposal = ReceiptProposalV2("OCR")
    assert not ocr_is_verified_purchase(proposal)
    assert ocr_is_verified_purchase(ReceiptProposalV2("OCR", "VERIFIED", "HIGH", True))


def test_wave_5_migration_has_exact_nine_canonical_tables_and_guards():
    text = MIGRATION.read_text(encoding="utf-8")
    tables = ("shopping_lists", "shopping_demands", "shopping_items", "purchase_events", "pantry_inventory", "pantry_movements", "receipt_documents", "receipt_proposals", "receipt_lines")
    assert all(f'"{table}"' in text for table in tables)
    assert "ck_shopping_items_state" in text
    assert "ck_pantry_inventory_nonnegative" in text
    assert "ck_receipt_lines_state" in text
    assert "uq_receipt_proposals_idempotency" in text


def test_w5_router_contains_exact_frozen_public_routes():
    text = (ROOT / "app" / "routers" / "v2_shopping.py").read_text(encoding="utf-8")
    assert text.count("@router.") == 7
    assert "@router.post(\"/households/{household_id}/plans" not in text
