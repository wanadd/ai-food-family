import { afterEach, describe, expect, it, vi } from "vitest";

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
    process.env.NODE_ENV = originalNodeEnv;
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = originalFlag;
    vi.unstubAllGlobals();
  });

  it("renders local parity panel only when public flag is true on localhost", () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = "true";
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(true);
  });

  it("hides local parity panel by default", () => {
    process.env.NODE_ENV = "development";
    delete process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE;
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(false);
  });

  it("hides local parity panel in production", () => {
    process.env.NODE_ENV = "production";
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = "true";
    setHost("localhost");

    expect(isLocalParityModeEnabled()).toBe(false);
  });

  it("hides local parity panel away from localhost", () => {
    process.env.NODE_ENV = "development";
    process.env.NEXT_PUBLIC_LOCAL_PARITY_MODE = "true";
    setHost("planam.ru");

    expect(isLocalParityModeEnabled()).toBe(false);
  });
});
