#!/usr/bin/env node
/**
 * PLANAM UX audit walkthrough — Playwright 390×844 screenshots per persona.
 *
 * Usage:
 *   cd apps/web
 *   PLANAM_AUDIT_BASE_URL=http://localhost:3002 node scripts/audit-walkthrough.mjs
 */

import { execSync } from "node:child_process";
import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../../..");
const OUT_ROOT = path.join(ROOT, "reports/ux_audit");
const OUT_SCREEN = path.join(OUT_ROOT, "screenshots");
const OUT_NETWORK = path.join(OUT_ROOT, "network");
const OUT_LOGS = path.join(OUT_ROOT, "logs");
const OUT_STATUS = path.join(OUT_ROOT, "AUDIT_RUN_STATUS.md");
const OUT_BLANK = path.join(OUT_ROOT, "blank_screen_findings.json");
const OUT_STATUS_ROOT = path.join(ROOT, "reports/AUDIT_RUN_STATUS.md");
const OUT_BLANK_ROOT = path.join(ROOT, "reports/blank_screen_findings.json");
const ARCHIVE_PATH = path.join(
  ROOT,
  "reports/PLANAM_ULTIMATE_UX_AUDIT_AFTER_HARNESS_TRUE_VALID.zip",
);

const BASE_URL = process.env.PLANAM_AUDIT_BASE_URL ?? "http://localhost:3000";
const API_URL =
  process.env.PLANAM_AUDIT_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

const MIN_BODY_TEXT_LENGTH = 20;
const MIN_BODY_HTML_LENGTH = 100;
const PIXEL_VALIDATION_ENABLED = false;
const EXPECTED_SCREENSHOT_COUNT = 108;

const EXPECTED_403_ENDPOINTS = [];

const ROUTE_ASSERTIONS = {
  home: [
    "Добрый день",
    "План на день",
    "ПланАм",
    "PLANAM",
    "Меню",
    "Покупки",
    "Запасы",
    "Здоровье",
  ],
  menu: [
    "Меню",
    "Сегодня",
    "Завтрак",
    "Обед",
    "Ужин",
    "итог",
    "день",
    "Собрать",
    "ккал",
  ],
  shopping: ["Покупки", "Список", "Купить", "товар", "категор"],
  pantry: ["Запасы", "Кладовая", "продукт", "остат", "готов"],
  wellness: [
    "Здоровье",
    "питани",
    "калор",
    "белк",
    "жир",
    "углевод",
    "КБЖУ",
    "цель",
  ],
  recipes: ["Рецепт", "рецепт", "ингредиент", "приготов", "ккал"],
  account: ["Профиль", "Аккаунт", "Настройки", "Телефон", "Подписка", "Семья"],
  subscription: ["Подписка", "Тариф", "тариф", "план"],
  family: ["Семья", "семь", "Участник", "Admin", "Adult"],
};

const GLOBAL_FORBIDDEN_TEXTS = [
  "Invalid audit secret",
  "Audit auth is disabled",
  "Internal Server Error",
  "TelegramRequiredScreen",
  "Откройте приложение через Telegram",
  "403 Forbidden",
  "500 Internal Server Error",
  "HTTP 403",
  "HTTP 500",
  "Error 403",
  "Error 500",
];

const GLOBAL_FORBIDDEN_PATTERNS = [
  /CORS policy/i,
  /^Forbidden$/m,
  /^Unauthorized$/m,
  /Unauthorized\s*\(401\)/i,
];

/** Empty-state copy is valid for new users but must not appear for seeded personas. */
const PERSONA_ROUTE_FORBIDDEN = [
  {
    persona: "audit_personal_day5",
    routes: ["home", "menu"],
    text: "Меню пока не собрано",
  },
  {
    persona: "audit_personal_day5",
    routes: ["wellness"],
    text: "Заполните питание",
  },
  {
    persona: "audit_family_admin",
    routes: ["family"],
    text: "Создайте семью",
  },
];

const FATAL_CONSOLE_PATTERNS = [
  /CORS policy/i,
  /auth\/audit-login/i,
  /TelegramRequiredScreen/i,
  /Failed to load resource: net::ERR_FAILED/i,
  /Failed to fetch/i,
  /Audit auth is disabled/i,
  /Invalid audit secret/i,
  /\b401\b/,
  /\b403\b/,
];

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

function isApiUrl(url) {
  return url.includes(":8000") || url.includes("/auth/") || url.includes("/api/");
}

function isExpected403(url) {
  return EXPECTED_403_ENDPOINTS.some((fragment) => url.includes(fragment));
}

function isFatalNetwork(entry) {
  const url = entry.url ?? "";
  const status = entry.status;
  if (status === "navigation_error") return true;
  if (!isApiUrl(url)) return false;
  if (typeof status === "number" && status === 401) return true;
  if (typeof status === "number" && status === 403) return !isExpected403(url);
  if (typeof status === "number" && status >= 400 && url.includes("/auth/audit-login")) {
    return true;
  }
  return false;
}

function isFatalConsoleError(text) {
  return FATAL_CONSOLE_PATTERNS.some((re) => re.test(text));
}

function matchedExpectedTexts(routeKey, bodyText) {
  return (ROUTE_ASSERTIONS[routeKey] ?? []).filter((needle) =>
    bodyText.includes(needle),
  );
}

function matchedForbiddenTexts(bodyText, persona, routeKey) {
  const hits = [];
  for (const text of GLOBAL_FORBIDDEN_TEXTS) {
    if (bodyText.includes(text)) hits.push(text);
  }
  for (const re of GLOBAL_FORBIDDEN_PATTERNS) {
    if (re.test(bodyText)) hits.push(re.toString());
  }
  for (const rule of PERSONA_ROUTE_FORBIDDEN) {
    if (
      rule.persona === persona &&
      rule.routes.includes(routeKey) &&
      bodyText.includes(rule.text) &&
      !hits.includes(rule.text)
    ) {
      hits.push(rule.text);
    }
  }
  return hits;
}

async function readBodyMetrics(page) {
  const bodyText = await page.locator("body").innerText().catch(() => "");
  const bodyHtmlLength = await page
    .locator("body")
    .evaluate((el) => el.innerHTML.trim().length)
    .catch(() => 0);
  return {
    bodyText,
    bodyTextLength: bodyText.trim().length,
    bodyHtmlLength,
  };
}

function makeFinding({
  persona,
  routeKey,
  url,
  reason,
  metrics,
  matchedExpected = [],
  matchedForbidden = [],
  screenshotPath = null,
}) {
  return {
    persona,
    route: routeKey,
    url,
    reason,
    bodyTextLength: metrics.bodyTextLength,
    bodyHtmlLength: metrics.bodyHtmlLength,
    matchedExpectedTexts: matchedExpected,
    matchedForbiddenTexts: matchedForbidden,
    screenshotPath,
    timestamp: new Date().toISOString(),
  };
}

async function waitForAuditLogin(page, isFirstRouteInContext) {
  const response = await page
    .waitForResponse((res) => res.url().includes("/auth/audit-login"), {
      timeout: isFirstRouteInContext ? 60000 : 10000,
    })
    .catch(() => null);

  if (response) {
    if (response.status() !== 200) {
      throw new Error(`audit-login returned ${response.status()}`);
    }
    return { ok: true, status: 200 };
  }

  if (!isFirstRouteInContext) {
    return { ok: true, status: "cached_session" };
  }

  throw new Error("audit-login did not occur");
}

async function waitForRenderedPage(page, routeKey) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForLoadState("networkidle", { timeout: 45000 }).catch(() => {});

  await page.waitForFunction(
    () =>
      document.body &&
      document.body.innerText.trim().length > 20 &&
      document.body.innerHTML.trim().length > 100,
    null,
    { timeout: 30000 },
  );

  const needles = ROUTE_ASSERTIONS[routeKey] ?? [];
  if (needles.length > 0) {
    await page.waitForFunction(
      (expected) => {
        const text = document.body?.innerText ?? "";
        return expected.some((needle) => text.includes(needle));
      },
      needles,
      { timeout: 30000 },
    );
  }

  await page.waitForTimeout(1000);
}

function validateRenderedPage(persona, routeKey, url, metrics, screenshotPath) {
  const findings = [];
  const fatals = [];
  const expected = matchedExpectedTexts(routeKey, metrics.bodyText);
  const forbidden = matchedForbiddenTexts(metrics.bodyText, persona, routeKey);

  if (metrics.bodyTextLength < MIN_BODY_TEXT_LENGTH || metrics.bodyHtmlLength < MIN_BODY_HTML_LENGTH) {
    const finding = makeFinding({
      persona,
      routeKey,
      url,
      reason: "blank_screen",
      metrics,
      matchedExpected: expected,
      matchedForbidden: forbidden,
      screenshotPath,
    });
    findings.push(finding);
    fatals.push({ ...finding, reason: "blank_screen" });
  }

  if (expected.length === 0 && metrics.bodyTextLength >= MIN_BODY_TEXT_LENGTH) {
    const finding = makeFinding({
      persona,
      routeKey,
      url,
      reason: "route_not_rendered",
      metrics,
      matchedExpected: expected,
      matchedForbidden: forbidden,
      screenshotPath,
    });
    findings.push(finding);
    fatals.push({ ...finding, reason: "route_not_rendered" });
  }

  if (forbidden.length > 0) {
    const finding = makeFinding({
      persona,
      routeKey,
      url,
      reason: "forbidden_state",
      metrics,
      matchedExpected: expected,
      matchedForbidden: forbidden,
      screenshotPath,
    });
    findings.push(finding);
    fatals.push({ ...finding, reason: "forbidden_state" });
  }

  return { findings, fatals, expected, forbidden };
}

function attachListeners(page, persona, consoleErrors, failedNetwork) {
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push({ persona, text: msg.text() });
  });
  page.on("response", (res) => {
    const url = res.url();
    if (res.status() >= 400 && isApiUrl(url)) {
      failedNetwork.push({ persona, url, status: res.status() });
    }
  });
}

function collectFatals(consoleErrors, failedNetwork, pageFatals = []) {
  return {
    fatalConsole: consoleErrors.filter((e) => isFatalConsoleError(e.text)),
    fatalNetwork: failedNetwork.filter((e) => isFatalNetwork(e)),
    pageFatals,
  };
}

async function gotoAndCapture(page, persona, route, isFirstRoute, consoleErrors, failedNetwork) {
  const url = `${BASE_URL}${route.path}?auditPersona=${persona}`;
  const file = `audit_${persona}_${route.key}.png`;
  const screenshotPath = path.join(OUT_SCREEN, file);
  const pageFatals = [];
  const blankFindings = [];

  try {
    const loginWait = page.waitForResponse(
      (res) => res.url().includes("/auth/audit-login"),
      { timeout: 60000 },
    );

    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });

    try {
      const loginRes = await loginWait;
      if (loginRes.status() !== 200) {
        throw new Error(`audit-login returned ${loginRes.status()}`);
      }
    } catch (err) {
      if (isFirstRoute) {
        const finding = makeFinding({
          persona,
          routeKey: route.key,
          url,
          reason: "auth_failure",
          metrics: { bodyText: "", bodyTextLength: 0, bodyHtmlLength: 0 },
          screenshotPath: null,
        });
        blankFindings.push(finding);
        pageFatals.push({ ...finding, text: err.message });
        failedNetwork.push({
          persona,
          url: `${API_URL}/auth/audit-login`,
          status: 403,
          message: err.message,
        });
        console.error("INVALID", file, "auth_failure");
        return { pageFatals, blankFindings, bodyTextLength: null };
      }
      await waitForAuditLogin(page, false);
    }

    await waitForRenderedPage(page, route.key);
    const metrics = await readBodyMetrics(page);
    const validation = validateRenderedPage(persona, route.key, url, metrics, null);

    if (validation.fatals.length > 0) {
      blankFindings.push(...validation.findings);
      pageFatals.push(...validation.fatals);
      console.error("INVALID", file, validation.fatals.map((f) => f.reason).join(", "));
      return { pageFatals, blankFindings, bodyTextLength: null };
    }

    await page.screenshot({ path: screenshotPath, fullPage: false, timeout: 30000 });

    const postMetrics = await readBodyMetrics(page);
    const postValidation = validateRenderedPage(
      persona,
      route.key,
      url,
      postMetrics,
      screenshotPath,
    );
    if (postValidation.fatals.length > 0) {
      blankFindings.push(...postValidation.findings);
      pageFatals.push(...postValidation.fatals);
      console.error("INVALID", file, postValidation.fatals.map((f) => f.reason).join(", "));
      return { pageFatals, blankFindings, bodyTextLength: null };
    }

    console.log("OK", file);
    return { pageFatals, blankFindings, bodyTextLength: postMetrics.bodyTextLength };
  } catch (err) {
    console.error("FAIL", persona, route.key, err.message);
    const metrics = await readBodyMetrics(page).catch(() => ({
      bodyText: "",
      bodyTextLength: 0,
      bodyHtmlLength: 0,
    }));
    const finding = makeFinding({
      persona,
      routeKey: route.key,
      url,
      reason: err.message.includes("audit-login") ? "auth_failure" : "blank_screen",
      metrics,
      screenshotPath: null,
    });
    blankFindings.push(finding);
    pageFatals.push({ ...finding, text: err.message });
    failedNetwork.push({
      persona,
      url: route.path,
      status: "navigation_error",
      message: err.message,
    });
  }

  return { pageFatals, blankFindings, bodyTextLength: null };
}

async function runPreflight(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const failedNetwork = [];
  const pageFatals = [];
  const blankFindings = [];

  attachListeners(page, "preflight", consoleErrors, failedNetwork);

  await page.goto(`${BASE_URL}/dev/audit`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(1000);

  const loginWait = page.waitForResponse(
    (res) => res.url().includes("/auth/audit-login") && res.status() === 200,
    { timeout: 60000 },
  );

  await page.goto(`${BASE_URL}/?auditPersona=audit_personal_day5`, {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  try {
    await loginWait;
    await waitForRenderedPage(page, "home");
    const metrics = await readBodyMetrics(page);
    const validation = validateRenderedPage(
      "audit_personal_day5",
      "home",
      `${BASE_URL}/?auditPersona=audit_personal_day5`,
      metrics,
      null,
    );
    pageFatals.push(...validation.fatals);
    blankFindings.push(...validation.findings);
  } catch (err) {
    const finding = makeFinding({
      persona: "preflight",
      routeKey: "home",
      url: `${BASE_URL}/?auditPersona=audit_personal_day5`,
      reason: "auth_failure",
      metrics: { bodyText: "", bodyTextLength: 0, bodyHtmlLength: 0 },
    });
    blankFindings.push(finding);
    pageFatals.push({ ...finding, text: err.message });
    failedNetwork.push({
      persona: "preflight",
      url: `${API_URL}/auth/audit-login`,
      status: 403,
      message: err.message,
    });
  }

  await context.close();
  return { consoleErrors, failedNetwork, pageFatals, blankFindings };
}

async function capturePersona(browser, persona) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const failedNetwork = [];
  const pageFatals = [];
  const blankFindings = [];

  attachListeners(page, persona, consoleErrors, failedNetwork);

  const bodyTextLengths = [];

  for (let i = 0; i < ROUTES.length; i += 1) {
    const result = await gotoAndCapture(
      page,
      persona,
      ROUTES[i],
      i === 0,
      consoleErrors,
      failedNetwork,
    );
    pageFatals.push(...result.pageFatals);
    blankFindings.push(...result.blankFindings);
    if (typeof result.bodyTextLength === "number") {
      bodyTextLengths.push(result.bodyTextLength);
    }
  }

  await context.close();
  return { consoleErrors, failedNetwork, pageFatals, blankFindings, bodyTextLengths };
}

function countByReason(findings, reason) {
  return findings.filter((f) => f.reason === reason).length;
}

async function writeReports({
  valid,
  fatalConsole,
  fatalNetwork,
  pageFatals,
  blankFindings,
  screenshotsCount,
  allConsole,
  allNetwork,
  bodyTextMinLength,
  failedRoutes,
}) {
  const networkFailedCount = allNetwork.filter((e) => isFatalNetwork(e)).length;
  const blankScreensCount = countByReason(blankFindings, "blank_screen");
  const routeAssertionFailuresCount = countByReason(blankFindings, "route_not_rendered");
  const authFailuresCount = countByReason(blankFindings, "auth_failure");
  const forbiddenStateCount = countByReason(blankFindings, "forbidden_state");

  const lines = [
    "# PLANAM UX Audit Run Status",
    "",
    `valid: ${valid}`,
    `screenshots_count: ${screenshotsCount}`,
    `network_failed_count: ${networkFailedCount}`,
    `blank_screens_count: ${blankScreensCount}`,
    `route_assertion_failures_count: ${routeAssertionFailuresCount}`,
    `auth_failures_count: ${authFailuresCount}`,
    `forbidden_state_count: ${forbiddenStateCount}`,
    `fatal_errors_count: ${fatalConsole.length + fatalNetwork.length + pageFatals.length}`,
    `body_text_min_length: ${bodyTextMinLength}`,
    `pixel_validation_enabled: ${PIXEL_VALIDATION_ENABLED}`,
    `personas_count: ${PERSONAS.length}`,
    `base_url: ${BASE_URL}`,
    `api_url: ${API_URL}`,
    `captured_at: ${new Date().toISOString()}`,
    "",
  ];

  if (valid) {
    lines.push(`archive_path: ${ARCHIVE_PATH}`, "");
  } else {
    lines.push("archive_path: (not created — audit invalid)", "");
    lines.push("## Why invalid", "");
    if (blankScreensCount > 0) lines.push(`- blank screens: ${blankScreensCount}`);
    if (routeAssertionFailuresCount > 0) {
      lines.push(`- route assertion failures: ${routeAssertionFailuresCount}`);
    }
    if (authFailuresCount > 0) lines.push(`- auth failures: ${authFailuresCount}`);
    if (forbiddenStateCount > 0) lines.push(`- forbidden states: ${forbiddenStateCount}`);
    if (networkFailedCount > 0) lines.push(`- network failures: ${networkFailedCount}`);
    lines.push("");
  }

  if (failedRoutes.length > 0) {
    lines.push("## Failed routes", "");
    for (const route of failedRoutes.slice(0, 40)) {
      lines.push(`- [${route.persona}/${route.route}] ${route.reason}`);
    }
    lines.push("");
  }

  lines.push(
    "## Summary",
    "",
    `- total console errors: ${allConsole.length}`,
    `- total network issues (>=400): ${allNetwork.length}`,
  );

  const statusBody = lines.join("\n");
  await writeFile(OUT_STATUS, statusBody, "utf8");
  await writeFile(OUT_STATUS_ROOT, statusBody, "utf8");
  await writeFile(OUT_BLANK, JSON.stringify(blankFindings, null, 2));
  await writeFile(OUT_BLANK_ROOT, JSON.stringify(blankFindings, null, 2));
}

function createArchiveIfValid(valid) {
  if (!valid) return;
  const psPath = OUT_ROOT.replace(/'/g, "''");
  const zipPath = ARCHIVE_PATH.replace(/'/g, "''");
  execSync(
    `powershell -NoProfile -Command "Compress-Archive -Path '${psPath}' -DestinationPath '${zipPath}' -Force"`,
    { stdio: "inherit" },
  );
}

async function main() {
  const { rm } = await import("node:fs/promises");
  await rm(OUT_SCREEN, { recursive: true, force: true }).catch(() => {});
  await mkdir(OUT_SCREEN, { recursive: true });
  await mkdir(OUT_NETWORK, { recursive: true });
  await mkdir(OUT_LOGS, { recursive: true });

  const allConsole = [];
  const allNetwork = [];
  const allPageFatals = [];
  const allBlankFindings = [];
  const successfulBodyTextLengths = [];
  let bodyTextMinLength = Number.POSITIVE_INFINITY;

  const browser = await chromium.launch();
  try {
    const preflight = await runPreflight(browser);
    allConsole.push(...preflight.consoleErrors);
    allNetwork.push(...preflight.failedNetwork);
    allPageFatals.push(...preflight.pageFatals);
    allBlankFindings.push(...preflight.blankFindings);

    const preflightFatals = collectFatals(
      preflight.consoleErrors,
      preflight.failedNetwork,
      preflight.pageFatals,
    );

    if (
      preflightFatals.fatalConsole.length > 0 ||
      preflightFatals.fatalNetwork.length > 0 ||
      preflightFatals.pageFatals.length > 0
    ) {
      console.error("FATAL: audit preflight failed");
      await writeReports({
        valid: false,
        ...preflightFatals,
        blankFindings: allBlankFindings,
        screenshotsCount: 0,
        allConsole,
        allNetwork,
        bodyTextMinLength: 0,
        failedRoutes: allBlankFindings,
      });
      process.exit(1);
    }
  } finally {
    await browser.close();
  }

  for (const persona of PERSONAS) {
    const personaBrowser = await chromium.launch();
    try {
      const result = await capturePersona(personaBrowser, persona);
      allConsole.push(...result.consoleErrors);
      allNetwork.push(...result.failedNetwork);
      allPageFatals.push(...result.pageFatals);
      allBlankFindings.push(...result.blankFindings);
      successfulBodyTextLengths.push(...result.bodyTextLengths);
    } finally {
      await personaBrowser.close();
    }
  }

  for (const length of successfulBodyTextLengths) {
    if (length < bodyTextMinLength) bodyTextMinLength = length;
  }
  if (!Number.isFinite(bodyTextMinLength)) bodyTextMinLength = 0;

  const { fatalConsole, fatalNetwork } = collectFatals(
    allConsole,
    allNetwork,
    allPageFatals,
  );
  const networkFailedCount = allNetwork.filter((e) => isFatalNetwork(e)).length;
  const blankScreensCount = countByReason(allBlankFindings, "blank_screen");
  const routeAssertionFailuresCount = countByReason(allBlankFindings, "route_not_rendered");
  const authFailuresCount = countByReason(allBlankFindings, "auth_failure");
  const forbiddenStateCount = countByReason(allBlankFindings, "forbidden_state");

  let screenshotsCount = 0;
  try {
    const { readdir } = await import("node:fs/promises");
    const files = await readdir(OUT_SCREEN);
    screenshotsCount = files.filter((f) => f.endsWith(".png")).length;
  } catch {
    screenshotsCount = 0;
  }

  const valid =
    fatalConsole.length === 0 &&
    fatalNetwork.length === 0 &&
    allPageFatals.length === 0 &&
    networkFailedCount === 0 &&
    blankScreensCount === 0 &&
    routeAssertionFailuresCount === 0 &&
    authFailuresCount === 0 &&
    forbiddenStateCount === 0 &&
    screenshotsCount >= EXPECTED_SCREENSHOT_COUNT;

  await writeFile(
    path.join(OUT_NETWORK, "findings.json"),
    JSON.stringify(
      {
        failed: allNetwork,
        fatal: fatalNetwork,
        network_failed_count: networkFailedCount,
        blank_screens_count: blankScreensCount,
        route_assertion_failures_count: routeAssertionFailuresCount,
        auth_failures_count: authFailuresCount,
        forbidden_state_count: forbiddenStateCount,
        captured_at: new Date().toISOString(),
      },
      null,
      2,
    ),
  );
  await writeFile(
    path.join(OUT_LOGS, "console.json"),
    JSON.stringify(
      {
        errors: allConsole,
        fatal: fatalConsole,
        page_fatals: allPageFatals,
        blank_findings: allBlankFindings,
        captured_at: new Date().toISOString(),
      },
      null,
      2,
    ),
  );

  await writeReports({
    valid,
    fatalConsole,
    fatalNetwork,
    pageFatals: allPageFatals,
    blankFindings: allBlankFindings,
    screenshotsCount,
    allConsole,
    allNetwork,
    bodyTextMinLength,
    failedRoutes: allBlankFindings,
  });

  if (valid) {
    createArchiveIfValid(true);
  }

  console.log(`Done. Screenshots → ${OUT_SCREEN}`);
  console.log(
    `Status: valid=${valid}, network_failed=${networkFailedCount}, blank=${blankScreensCount}, route_assert=${routeAssertionFailuresCount}, auth=${authFailuresCount}, forbidden=${forbiddenStateCount}`,
  );

  if (!valid) {
    console.error("AUDIT INVALID");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
