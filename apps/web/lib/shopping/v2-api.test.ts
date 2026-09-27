import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/lib/api-client";
import { addShoppingItemV2, acceptReceiptV2, adjustPantryV2, createReceiptV2, purchaseShoppingItemV2, readPantryV2, readShoppingV2 } from "./v2-api";
vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));
describe("shopping/pantry/receipt v2 adapter", () => {
  it("uses the seven frozen routes and mutation keys", async () => {
    vi.mocked(apiFetch).mockResolvedValue({});
    await readShoppingV2("i", "family", "h"); await addShoppingItemV2("i", "family", "h", {}, "1"); await purchaseShoppingItemV2("i", "family", "h", "x", true, "2"); await readPantryV2("i", "family", "h"); await adjustPantryV2("i", "family", "h", {}, "3"); await createReceiptV2("i", "family", "h", {}, "4"); await acceptReceiptV2("i", "family", "h", "r", "p", ["l"], "5");
    expect(vi.mocked(apiFetch).mock.calls.map((call) => call[2])).toEqual([
      "/v2/households/h/shopping", "/v2/households/h/shopping/items", "/v2/shopping/items/x/purchase", "/v2/households/h/pantry", "/v2/households/h/pantry/adjust", "/v2/households/h/receipts", "/v2/receipts/r/proposals/p/accept",
    ]);
  });
});
