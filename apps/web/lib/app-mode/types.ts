import type { Family } from "@/lib/family/types";

export type AppMode = "personal" | "family";

export type AppContext = {
  active_mode: AppMode;
  has_family: boolean;
  can_use_family_mode: boolean;
  family: Family | null;
};
