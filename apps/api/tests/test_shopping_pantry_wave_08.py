from app.shopping.v2_contracts import ReceiptProposalV2, ShoppingDemandV2, can_merge_demands, checked_item_proves_pantry, expiration_state, merge_demands, ocr_is_verified_purchase

def test_demand_preserves_plan_recipe_and_person_provenance():
    demand = ShoppingDemandV2("oats", None, None, "PLAN", "rev", "slot", "recipe-v", "person")
    assert demand.quantity_state == "UNKNOWN"
    assert demand.plan_revision_id == "rev"

def test_unknown_quantity_is_not_zero_and_safe_merge_is_constrained():
    unknown = ShoppingDemandV2("oats", None, "g", "PLAN", product_requirement={"certified_gf": True})
    generic = ShoppingDemandV2("oats", 500, "g", "PLAN", product_requirement={})
    assert unknown.quantity_state == "UNKNOWN"
    assert not can_merge_demands(unknown, generic)
    assert merge_demands(unknown, generic) is None

def test_manual_item_and_checkbox_are_not_hidden_purchase_truth():
    manual = ShoppingDemandV2("milk", 1, "pack", "MANUAL")
    assert manual.source_kind == "MANUAL"
    assert not checked_item_proves_pantry("CHECKED")

def test_receipt_ocr_is_proposal_until_verified():
    proposal = ReceiptProposalV2("OCR")
    assert not ocr_is_verified_purchase(proposal)
    assert expiration_state(None) == "UNKNOWN"
