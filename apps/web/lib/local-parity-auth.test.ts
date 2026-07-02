import { afterEach, describe, expect, it, vi } from "vitest";

import { setNodeEnvForTest } from "@/lib/test/env";

import { isLocalParityModeEnabled } from "./local-parity-auth";

const originalNodeEnv = process.env.NODE_ENV;
const originalFlag = process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE;

function setHost(hostname: string) {
  vi.stubGlobal("window", {
    location: { hostname },
  });
}

describe("local parity auth gate", () => {
  afterEach(() => {
    setNodeEnvForTest(originalNodeEnv);
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = originalFlag;
    vi.unstubAllGlobals();
  });

  it("renders local parity panel only when public flag is true on localhost", () => {
    setNodeEnvForTest("development");
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = "true";
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(true);
  });

  it("hides local parity panel by default", () => {
    setNodeEnvForTest("development");
    delete process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE;
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(false);
  });

  it("hides local parity panel in production/default", () => {
    setNodeEnvForTest("production");
    delete process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE;
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(false);
  });

  it("hides local parity panel away from localhost", () => {
    setNodeEnvForTest("development");
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = "true";
    setHost("planam.ru");

    expect(isLocalParityModeEnabled()).toBe(false);
  });
});
