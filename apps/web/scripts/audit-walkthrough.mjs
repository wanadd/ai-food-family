#!/usr/bin/env node
/**
 * PLANAM UX audit walkthrough — Playwright 390×844 screenshots per persona.
 *
 * Requires:
 *   - web dev server on BASE_URL (default http://localhost:3000)
 *   - API with PLANAM_AUDIT_MODE=true
 *   - NEXT_PUBLIC_PLANAM_AUDIT_MODE=true on web
 *
 * Usage:
 *   cd apps/web
 *   node scripts/audit-walkthrough.mjs
 */

import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../../..");
const OUT_SCREEN = path.join(ROOT, "reports/ux_audit/screenshots");
const OUT_NETWORK = path.join(ROOT, "reports/ux_audit/network");
const OUT_LOGS = path.join(ROOT, "reports/ux_audit/logs");

const BASE_URL = process.env.PLANAM_AUDIT_BASE_URL ?? "http://localhost:3000";

const PERSONAS = [
  "audit_new_user",
  "audit_personal_day5",
  "audit_family_admin",
  "audit_family_adult",
  "audit_start_trial",
  "audit_personal_plus",
  "audit_pair",
  "audit_family",
  "audit_family_pro",
  "audit_athlete",
  "audit_strict_diet",
  "audit_healthy_eating",
];

const ROUTES = [
  { key: "home", path: "/" },
  { key: "menu", path: "/plan/today" },
  { key: "shopping", path: "/shopping" },
  { key: "pantry", path: "/home/pantry" },
  { key: "wellness", path: "/wellness" },
  { key: "recipes", path: "/plan/recipes" },
  { key: "account", path: "/account" },
  { key: "subscription", path: "/account/subscription" },
  { key: "family", path: "/account/family" },
];

async function capturePersona(browser, persona) {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  });
  const page = await context.newPage();
  const consoleErrors = [];
  const failedNetwork = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push({ persona, text: msg.text() });
    }
  });
  page.on("response", (res) => {
    const url = res.url();
    if (
      res.status() >= 400 &&
      (url.includes("/api/") || url.includes(":8000") || url.includes("/auth/"))
    ) {
      failedNetwork.push({ persona, url, status: res.status() });
    }
  });

  for (const route of ROUTES) {
    const url = `${BASE_URL}${route.path}?auditPersona=${persona}`;
    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
      await page.waitForTimeout(1200);
      const file = `audit_${persona}_${route.key}.png`;
      await page.screenshot({
        path: path.join(OUT_SCREEN, file),
        fullPage: true,
      });
      console.log("OK", file);
    } catch (err) {
      console.error("FAIL", persona, route.key, err.message);
      failedNetwork.push({
        persona,
        url: route.path,
        status: "navigation_error",
        message: err.message,
      });
    }
  }

  await context.close();
  return { consoleErrors, failedNetwork };
}

async function main() {
  await mkdir(OUT_SCREEN, { recursive: true });
  await mkdir(OUT_NETWORK, { recursive: true });
  await mkdir(OUT_LOGS, { recursive: true });

  const browser = await chromium.launch();
  const allConsole = [];
  const allNetwork = [];

  for (const persona of PERSONAS) {
    const { consoleErrors, failedNetwork } = await capturePersona(browser, persona);
    allConsole.push(...consoleErrors);
    allNetwork.push(...failedNetwork);
  }

  await browser.close();

  await writeFile(
    path.join(OUT_NETWORK, "findings.json"),
    JSON.stringify({ failed: allNetwork, captured_at: new Date().toISOString() }, null, 2),
  );
  await writeFile(
    path.join(OUT_LOGS, "console.json"),
    JSON.stringify({ errors: allConsole, captured_at: new Date().toISOString() }, null, 2),
  );

  console.log(`Done. Screenshots → ${OUT_SCREEN}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
