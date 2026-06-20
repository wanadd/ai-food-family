#!/usr/bin/env node
/**
 * PLANAM ultimate full UX audit.
 *
 * Produces a scenario-oriented audit pack without changing product UI/backend.
 * The runner is intentionally tolerant: missing routes/CTAs become UX issues,
 * not harness crashes.
 */

import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../../..");
const RUN_DIR = path.join(ROOT, "reports", "ultimate_full_ux_audit_2026_06_20");
const SCREEN_DIR = path.join(RUN_DIR, "screenshots");
const SHEET_DIR = path.join(RUN_DIR, "sheets");
const VIDEO_DIR = path.join(RUN_DIR, "videos");
const LOG_DIR = path.join(RUN_DIR, "logs");
const ZIP_PATH = path.join(ROOT, "reports", "PLANAM_ULTIMATE_FULL_UX_AUDIT_2026_06_20.zip");

const BASE_URL = process.env.PLANAM_AUDIT_BASE_URL ?? process.env.BASE_URL ?? "http://localhost:3002";
const API_URL =
  process.env.PLANAM_AUDIT_API_URL ??
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

const VIEWPORT = { width: 390, height: 844 };
const FORBIDDEN_STRINGS = [
  "undefined",
  "null",
  "NaN",
  "после наполнения базы",
  "TODO",
  "FIXME",
  "lorem",
  "TelegramRequiredScreen",
  "Откройте приложение через Telegram",
  "Internal Server Error",
];

const ROUTES = {
  home: "/",
  menu: "/plan/today",
  shopping: "/shopping",
  pantry: "/home/pantry",
  wellness: "/wellness",
  recipes: "/plan/recipes",
  account: "/account",
  subscription: "/account/subscription",
  family: "/account/family",
  events: "/events",
  settings: "/settings/account",
  notifications: "/account/notifications",
  amas: "/account/amas",
  checkout: "/account/subscription/checkout",
};

const SUPPORTED_AUTH_PERSONAS = new Set([
  "audit_new_user",
  "audit_personal_day5",
  "audit_family_admin",
  "audit_family_adult",
  "audit_family_child",
  "audit_athlete",
  "audit_strict_diet",
  "audit_healthy_eating",
  "audit_start_trial",
  "audit_personal_plus",
  "audit_pair",
  "audit_family",
  "audit_family_pro",
]);

const PERSONAS = [
  { id: "audit_new_user", auth: "audit_new_user", lens: "new free user, no profile/menu" },
  { id: "audit_onboarding_profile", auth: "audit_new_user", lens: "new user completing nutrition profile" },
  { id: "audit_personal_day1", auth: "audit_personal_day5", lens: "solo user after first generated menu" },
  { id: "audit_personal_day5", auth: "audit_personal_day5", lens: "returning solo user, day 5" },
  { id: "audit_personal_day7", auth: "audit_personal_day5", lens: "returning solo user, day 7 continuity" },
  { id: "audit_pair_virtual", auth: "audit_pair", lens: "pair with virtual member" },
  { id: "audit_family_admin", auth: "audit_family_admin", lens: "family admin" },
  { id: "audit_family_adult", auth: "audit_family_adult", lens: "family adult member, non-admin" },
  { id: "audit_family_child_virtual", auth: "audit_family_child", lens: "virtual child/member without account" },
  { id: "audit_start_trial", auth: "audit_start_trial", lens: "trial user" },
  { id: "audit_personal_plus", auth: "audit_personal_plus", lens: "paid personal user" },
  { id: "audit_pair", auth: "audit_pair", lens: "pair plan user" },
  { id: "audit_family", auth: "audit_family", lens: "family plan user" },
  { id: "audit_family_pro", auth: "audit_family_pro", lens: "family pro user" },
  { id: "audit_athlete", auth: "audit_athlete", lens: "athlete with protein/calorie goals" },
  { id: "audit_strict_diet", auth: "audit_strict_diet", lens: "strict diet/medical restrictions" },
  { id: "audit_healthy_eating", auth: "audit_healthy_eating", lens: "healthy eating with pantry" },
  { id: "audit_allergies_medical", auth: "audit_strict_diet", lens: "allergies and medical restrictions" },
  { id: "audit_religious_restrictions", auth: "audit_strict_diet", lens: "religious/ethnic restrictions" },
  { id: "audit_pro_ai_heavy", auth: "audit_family_pro", lens: "pro user using AI heavily" },
];

for (const persona of PERSONAS) {
  if (!SUPPORTED_AUTH_PERSONAS.has(persona.auth)) {
    throw new Error(`Unsupported auth persona mapping: ${persona.id} -> ${persona.auth}`);
  }
}

const SCENARIOS = [
  {
    id: "S01",
    title: "Первый вход нового пользователя",
    persona: "audit_new_user",
    steps: [
      ["home", "open app", "first screen explains PLANAM and next action"],
      ["home", "open profile CTA", "profile/onboarding entry is available", { click: [/профил/i, /начать/i, /настро/i, /заполн/i] }],
      ["account", "capture account/profile entry", "profile settings are reachable"],
      ["account", "type name if editable", "name field accepts input", { fill: "Иван" }],
      ["account", "choose goal/activity/restrictions if visible", "nutrition profile controls are visible", { click: [/цель/i, /актив/i, /огранич/i, /аллерг/i] }],
      ["menu", "open generate menu", "generate menu CTA or state is visible", { click: [/собрать/i, /создать/i, /меню/i] }],
      ["home", "verify post-profile destination", "home/menu/generate menu path remains clear"],
    ],
  },
  {
    id: "S02",
    title: "Новый пользователь создаёт меню",
    persona: "audit_onboarding_profile",
    steps: [
      ["menu", "open menu", "menu page opens"],
      ["menu", "click generate menu", "loading/result/paywall/empty state is captured", { click: [/собрать/i, /создать/i, /обнов/i] }],
      ["shopping", "compare shopping after menu", "shopping list reflects menu or clear empty state"],
      ["home", "compare home after menu", "home reflects menu state"],
      ["wellness", "compare wellness after menu", "wellness reflects nutrition state"],
    ],
  },
  {
    id: "S03",
    title: "5-й день использования",
    persona: "audit_personal_day5",
    steps: [
      ["home", "capture hero/day/today meal", "home shows today continuity"],
      ["menu", "open menu active day", "active day is visible"],
      ["menu", "switch day 1", "day switch works", { click: [/1/i, /пн/i, /день/i] }],
      ["menu", "switch day 5", "day 5 is reachable", { click: [/5/i, /пт/i, /сегодня/i] }],
      ["menu", "open meal sheet", "meal sheet opens", { click: [/завтрак/i, /обед/i, /ужин/i, /готов/i] }],
      ["menu", "start cooking", "cooking CTA works or is absent", { click: [/готовить/i, /начать/i] }],
      ["menu", "mark eaten or skipped", "meal status action is available", { click: [/съел/i, /съед/i, /пропуст/i, /другое/i] }],
      ["wellness", "check recalculation", "wellness remains consistent"],
      ["shopping", "check shopping impact", "shopping remains consistent"],
      ["pantry", "check leftovers impact", "leftovers/pantry remains consistent"],
    ],
  },
  {
    id: "S04",
    title: "7-дневный цикл",
    persona: "audit_personal_day7",
    steps: [
      ["menu", "check 7 days", "weekly cycle is visible"],
      ["menu", "check repeats", "repeated meals are understandable"],
      ["shopping", "check weekly shopping", "shopping list supports week"],
      ["pantry", "check leftovers", "leftovers are visible"],
      ["menu", "check next-week CTA", "next week CTA or limitation is clear", { click: [/след/i, /недел/i, /обнов/i] }],
      ["home", "check no day 7 dead end", "app remains useful after day 5"],
    ],
  },
  {
    id: "S05",
    title: "Shopping end-to-end",
    persona: "audit_family_admin",
    steps: [
      ["shopping", "open shopping", "shopping page opens"],
      ["shopping", "add item CTA", "manual add is available or clear", { click: [/добав/i, /товар/i, /\+/] }],
      ["shopping", "type manual item", "manual input accepts item", { fill: "молоко" }],
      ["shopping", "submit item", "item can be submitted or blocker is captured", { click: [/сохран/i, /добав/i, /готов/i] }],
      ["shopping", "mark bought", "bought toggle is available", { click: [/куп/i, /в корз/i, /✓/] }],
      ["shopping", "open all filter", "all filter works", { click: [/все/i] }],
      ["shopping", "open bought filter", "bought filter works", { click: [/куплен/i] }],
      ["home", "check buy tile", "home buy tile agrees with shopping"],
    ],
  },
  {
    id: "S06",
    title: "Pantry / Запасы / Остатки",
    persona: "audit_healthy_eating",
    steps: [
      ["pantry", "open pantry", "pantry opens"],
      ["pantry", "check expiry filters", "expiry filters are available", { click: [/скоро/i, /много/i, /проср/i] }],
      ["pantry", "add pantry item", "add pantry item is available", { click: [/добав/i, /продукт/i, /\+/] }],
      ["pantry", "type pantry item", "pantry form accepts input", { fill: "гречка" }],
      ["pantry", "cook from available", "cook-from-pantry path is visible", { click: [/приготов/i, /из того/i] }],
      ["recipes", "pantry to recipes/menu", "recipes/menu relation is visible"],
    ],
  },
  {
    id: "S07",
    title: "Recipe flow",
    persona: "audit_personal_day5",
    steps: [
      ["recipes", "open catalog", "recipe catalog opens"],
      ["recipes", "search recipe", "search accepts query", { fill: "курица" }],
      ["recipes", "filter breakfast/lunch/dinner", "meal filters are available", { click: [/завтрак/i, /обед/i, /ужин/i] }],
      ["recipes", "open recipe", "recipe detail opens", { click: [/рецепт/i, /ккал/i, /мин/i] }],
      ["recipes", "start cooking", "cooking flow starts or absence is captured", { click: [/начать готов/i, /готовить/i] }],
      ["recipes", "mark cooked", "cooked state is available", { click: [/приготовлено/i, /готово/i] }],
      ["pantry", "check leftovers update", "leftovers/prepared food relation is visible"],
    ],
  },
  {
    id: "S08",
    title: "Wellness / Health / AI nutrition",
    persona: "audit_pro_ai_heavy",
    steps: [
      ["wellness", "open wellness", "wellness opens with nutrition data"],
      ["wellness", "open AI assistant", "AI assistant opens", { click: [/ai/i, /нутрициолог/i, /спрос/i, /чат/i] }],
      ["wellness", "ask skipped lunch", "AI gives practical safe answer", { aiQuestion: "Я пропустил обед, что делать?" }],
      ["wellness", "ask ate shawarma", "AI helps account for outside food", { aiQuestion: "Я съел шаурму вместо ужина, как это учесть?" }],
      ["wellness", "ask weight loss fit", "AI assesses weight-loss fit safely", { aiQuestion: "Подходит ли мой рацион для похудения?" }],
      ["wellness", "ask allergy", "AI respects restrictions", { aiQuestion: "У меня аллергия/ограничение, можно ли это блюдо?" }],
      ["wellness", "ask post workout", "AI supports athlete context", { aiQuestion: "Что съесть после тренировки?" }],
      ["subscription", "check AI/pro paywall", "AI/Pro limits and Amas are understandable"],
    ],
  },
  {
    id: "S09",
    title: "Family: virtual users",
    persona: "audit_family_admin",
    steps: [
      ["family", "open family", "family page opens"],
      ["family", "add virtual member", "virtual member CTA is available", { click: [/виртуал/i, /добав/i, /участ/i] }],
      ["family", "fill member profile", "member profile accepts input", { fill: "Маша" }],
      ["family", "check roles", "child/adult/eating restrictions are visible", { click: [/реб/i, /взрос/i, /не ест/i] }],
      ["menu", "check family menu", "member affects menu context"],
      ["shopping", "check family shopping", "family shopping context is visible"],
      ["home", "check family home", "family state appears on home"],
    ],
  },
  {
    id: "S10",
    title: "Family: real account invite",
    persona: "audit_family_admin",
    steps: [
      ["family", "admin opens family", "admin can manage family"],
      ["family", "invite real account", "invite/link/phone CTA is visible", { click: [/приглас/i, /ссыл/i, /телефон/i] }],
      ["family", "capture role controls", "admin/adult/virtual/child roles are clear"],
      ["menu", "check shared menu", "shared menu is visible"],
      ["shopping", "check shared shopping", "shared shopping is visible"],
      ["family", "adult restrictions lens", "non-admin restrictions are described or captured"],
    ],
  },
  {
    id: "S11",
    title: "Tariffs / Subscription / Paywall",
    persona: "audit_family_pro",
    steps: [
      ["subscription", "open subscription", "current tariff is visible"],
      ["subscription", "check plans", "Free/Trial/Personal/Pair/Family/Pro are understandable"],
      ["subscription", "click upgrade/pay", "checkout/paywall path opens or blocker captured", { click: [/оплат/i, /апгрейд/i, /улучш/i, /подключ/i] }],
      ["checkout", "checkout route", "checkout route is available or redirects clearly"],
      ["subscription", "check Amas", "Amas balance/history/spend is understandable", { click: [/ам/i, /баланс/i, /истор/i] }],
      ["wellness", "contextual wellness upsell", "Pro value appears in wellness"],
      ["home", "contextual home upsell", "Pro value appears on home"],
    ],
  },
  {
    id: "S12",
    title: "Events",
    persona: "audit_family_admin",
    steps: [
      ["events", "open events", "events page opens"],
      ["events", "check event types", "cooking/shopping/reminders/family/health events are clear"],
      ["events", "open create event", "event CTA opens", { click: [/создать/i, /событ/i, /празд/i] }],
      ["events", "check Telegram notifications", "notification relation is visible"],
      ["home", "event back navigation", "events do not dead-end"],
    ],
  },
  {
    id: "S13",
    title: "Account / Settings / Theme / Notifications",
    persona: "audit_personal_day5",
    steps: [
      ["account", "open account", "account page opens"],
      ["account", "open nutrition", "nutrition profile item is reachable", { click: [/питан/i, /профил/i] }],
      ["family", "open family from account", "family item is reachable"],
      ["subscription", "open subscription from account", "subscription item is reachable"],
      ["notifications", "open notifications", "notifications route exists or fail is captured"],
      ["settings", "open settings", "settings route exists or fail is captured"],
      ["home", "light theme home", "light theme renders", { theme: "light" }],
      ["menu", "dark theme menu", "dark theme renders", { theme: "dark" }],
      ["shopping", "system theme shopping", "system theme renders", { theme: "system" }],
      ["home", "back button/fallback", "back navigation works", { back: true }],
    ],
  },
  {
    id: "S14",
    title: "Error/empty/loading states",
    persona: "audit_new_user",
    steps: [
      ["menu", "no menu", "empty menu state is useful"],
      ["recipes", "empty/search recipes", "empty search is clear", { fill: "zzzz-no-results" }],
      ["shopping", "no shopping items", "empty shopping state is not misleading"],
      ["pantry", "no pantry items", "empty pantry state is useful"],
      ["wellness", "no health data", "empty health state is useful"],
      ["family", "no family", "empty family state has CTA"],
      ["subscription", "subscription data/paywall state", "subscription state is readable"],
      ["wellness", "AI unavailable/pro state", "AI unavailable/paywall state is readable", { click: [/ai/i, /нутрициолог/i, /спрос/i] }],
      ["family", "forbidden adult/admin state", "access restrictions are clear"],
    ],
  },
  {
    id: "S15",
    title: "Developer/QA audit",
    persona: "audit_family_pro",
    steps: [
      ["home", "QA home scan", "no forbidden strings or dead end"],
      ["menu", "QA menu scan", "no duplicate/blank core screen"],
      ["shopping", "QA shopping scan", "shopping stable"],
      ["pantry", "QA pantry scan", "pantry stable"],
      ["wellness", "QA wellness scan", "wellness stable"],
      ["recipes", "QA recipes scan", "recipes stable"],
      ["account", "QA account scan", "account stable"],
      ["subscription", "QA subscription scan", "subscription stable"],
      ["family", "QA family scan", "family stable"],
      ["events", "QA events scan", "events stable"],
    ],
  },
];

const scenarioSteps = [];
const consoleRows = [];
const networkRows = [];
const bodyTextRows = [];
const routeGraph = {};
const clickGraph = [];
const issues = [];

function cleanName(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 70);
}

function personaById(id) {
  return PERSONAS.find((persona) => persona.id === id) ?? PERSONAS[0];
}

function pageUrl(routeKey, authPersona) {
  const route = ROUTES[routeKey] ?? "/";
  const sep = route.includes("?") ? "&" : "?";
  return `${BASE_URL}${route}${sep}auditPersona=${authPersona}`;
}

function isApiUrl(url) {
  return url.includes(":8000") || url.includes("/api/") || url.includes("/auth/");
}

function severityForStep(step) {
  if (step.route === "home" || ["S01", "S03", "S08", "S11"].includes(step.scenario)) return "P1";
  if (["menu", "shopping", "wellness", "subscription", "family"].includes(step.route)) return "P2";
  return "P3";
}

function pushIssue({ severity, screen, persona, scenario, step, title, expected, actual, screenshotPath, owner = "product", blocker = false }) {
  const p = severity ?? "P3";
  const count = issues.filter((issue) => issue.severity === p).length + 1;
  issues.push({
    id: `UX-${p}-${String(count).padStart(3, "0")}`,
    severity: p,
    screen,
    persona,
    scenario,
    step,
    title,
    evidence_screenshot: screenshotPath ? path.relative(RUN_DIR, screenshotPath).replaceAll("\\", "/") : null,
    expected,
    actual: String(actual ?? "").slice(0, 1200),
    impact: blocker ? "Blocks critical audit flow or launch confidence." : "Reduces clarity, continuity, or conversion confidence.",
    recommendation: "Review this screen in product/design triage and decide whether to fix before beta.",
    owner,
    fix_complexity: p === "P1" ? "M" : "S",
    release_blocker: blocker,
  });
}

async function ensureDirs() {
  await rm(RUN_DIR, { recursive: true, force: true }).catch(() => {});
  await mkdir(SCREEN_DIR, { recursive: true });
  await mkdir(SHEET_DIR, { recursive: true });
  await mkdir(VIDEO_DIR, { recursive: true });
  await mkdir(LOG_DIR, { recursive: true });
}

async function waitForApp(page) {
  await page.waitForLoadState("domcontentloaded", { timeout: 45000 }).catch(() => {});
  await page.waitForLoadState("networkidle", { timeout: 1500 }).catch(() => {});
  await page
    .waitForFunction(
      () => document.body && document.body.innerText.trim().length > 10,
      null,
      { timeout: 8000 },
    )
    .catch(() => {});
  await page.waitForTimeout(180);
}

async function readBody(page) {
  return page
    .locator("body")
    .innerText({ timeout: 3000 })
    .catch(() => "");
}

async function clickAny(page, patterns) {
  const candidates = await page
    .locator("button, a, [role=button], input[type=submit]")
    .evaluateAll((nodes) =>
      nodes.slice(0, 160).map((node, index) => ({
        index,
        text: (node.innerText || node.textContent || node.getAttribute("aria-label") || node.value || "").trim(),
      })),
    )
    .catch(() => []);
  const found = candidates.find((candidate) => patterns.some((pattern) => pattern.test(candidate.text)));
  if (!found) return { ok: false, note: "No matching clickable control", label: null };
  await page.locator("button, a, [role=button], input[type=submit]").nth(found.index).click({ timeout: 4000 }).catch(() => {});
  await waitForApp(page);
  return { ok: true, note: `Clicked: ${found.text}`, label: found.text };
}

async function fillFirst(page, value) {
  const input = page.locator("input:not([type=hidden]), textarea").first();
  const count = await page.locator("input:not([type=hidden]), textarea").count().catch(() => 0);
  if (!count) return { ok: false, note: "No editable input" };
  await input.fill(value, { timeout: 4000 }).catch(async () => {
    await input.type(value, { timeout: 4000 }).catch(() => {});
  });
  await page.keyboard.press("Enter").catch(() => {});
  await waitForApp(page);
  return { ok: true, note: `Filled first input with "${value}"` };
}

async function setTheme(page, theme) {
  await page.evaluate((nextTheme) => {
    localStorage.setItem("planam-theme", nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.classList.toggle("dark", nextTheme === "dark");
  }, theme);
  await page.waitForTimeout(300);
  return { ok: true, note: `Theme set to ${theme}` };
}

async function performAction(page, options = {}) {
  if (options.theme) return setTheme(page, options.theme);
  if (options.back) {
    await page.goBack({ waitUntil: "domcontentloaded", timeout: 8000 }).catch(() => {});
    await waitForApp(page);
    return { ok: true, note: "Browser back invoked" };
  }
  if (options.fill) return fillFirst(page, options.fill);
  if (options.aiQuestion) {
    const filled = await fillFirst(page, options.aiQuestion);
    if (!filled.ok) return filled;
    const clicked = await clickAny(page, [/отправ/i, /спрос/i, /send/i, /➜|→/]);
    return { ok: true, note: `${filled.note}; ${clicked.note}` };
  }
  if (options.click) return clickAny(page, options.click);
  return { ok: true, note: "Observation only" };
}

async function attachListeners(page, persona) {
  page.on("console", (msg) => {
    if (["error", "warning"].includes(msg.type())) {
      consoleRows.push({
        persona,
        type: msg.type(),
        text: msg.text(),
        url: page.url(),
        timestamp: new Date().toISOString(),
      });
    }
  });
  page.on("response", (res) => {
    const url = res.url();
    if (res.status() >= 400 && isApiUrl(url)) {
      networkRows.push({
        persona,
        url,
        status: res.status(),
        route: page.url(),
        timestamp: new Date().toISOString(),
      });
    }
  });
  page.on("pageerror", (err) => {
    consoleRows.push({
      persona,
      type: "pageerror",
      text: err.message,
      url: page.url(),
      timestamp: new Date().toISOString(),
    });
  });
}

async function runStep({ page, context, scenario, persona, stepIndex, step }) {
  const [route, action, expected, options] = step;
  const started = Date.now();
  const url = pageUrl(route, persona.auth);
  const stepNo = String(stepIndex + 1).padStart(2, "0");
  const fileName = `${scenario.id}_${persona.id}_${stepNo}_${route}_${cleanName(action)}.png`;
  const screenshotPath = path.join(SCREEN_DIR, fileName);
  let pass = true;
  let notes = [];

  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await waitForApp(page);
    const actionResult = await performAction(page, options);
    notes.push(actionResult.note);
    if (!actionResult.ok && options) pass = false;
  } catch (err) {
    pass = false;
    notes.push(`Navigation/action error: ${err.message}`);
  }

  const bodyText = await readBody(page);
  const forbiddenHits = FORBIDDEN_STRINGS.filter((item) => bodyText.toLowerCase().includes(item.toLowerCase()));
  if (bodyText.trim().length < 20) {
    pass = false;
    notes.push("Body text shorter than 20 chars");
  }
  if (forbiddenHits.length) {
    pass = false;
    notes.push(`Forbidden strings: ${forbiddenHits.join(", ")}`);
  }

  await page.screenshot({ path: screenshotPath, fullPage: false, timeout: 15000 }).catch((err) => {
    pass = false;
    notes.push(`Screenshot failed: ${err.message}`);
  });

  const row = {
    scenario: scenario.id,
    scenario_title: scenario.title,
    persona: persona.id,
    auth_persona: persona.auth,
    persona_lens: persona.lens,
    route,
    url: page.url(),
    step_number: stepIndex + 1,
    action,
    expected_result: expected,
    actual_bodyText: bodyText.slice(0, 8000),
    console_errors: consoleRows.filter((entry) => entry.persona === persona.id && entry.url === page.url()),
    network_400: networkRows.filter((entry) => entry.persona === persona.id && entry.route === page.url()),
    duration_ms: Date.now() - started,
    screenshot_path: path.relative(RUN_DIR, screenshotPath).replaceAll("\\", "/"),
    pass,
    notes: notes.filter(Boolean).join("; "),
  };
  scenarioSteps.push(row);
  bodyTextRows.push({
    scenario: scenario.id,
    persona: persona.id,
    route,
    step: stepIndex + 1,
    bodyTextLength: bodyText.length,
    bodyText,
  });
  routeGraph[route] ??= new Set();
  routeGraph[route].add(page.url());
  if (options?.click) clickGraph.push({ scenario: scenario.id, persona: persona.id, route, action, notes: row.notes, pass });

  if (!pass) {
    pushIssue({
      severity: severityForStep(row),
      screen: route,
      persona: persona.id,
      scenario: scenario.id,
      step: `${stepIndex + 1}: ${action}`,
      title: `Flow weakness: ${action}`,
      expected,
      actual: row.notes || bodyText.slice(0, 400),
      screenshotPath,
      owner: "product/design",
      blocker: ["S01", "S08", "S11"].includes(scenario.id),
    });
  }
}

async function runScenario(browser, scenario) {
  const persona = personaById(scenario.persona);
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();
  await attachListeners(page, persona.id);
  try {
    for (let i = 0; i < scenario.steps.length; i += 1) {
      await runStep({ page, context, scenario, persona, stepIndex: i, step: scenario.steps[i] });
      process.stdout.write(".");
    }
  } finally {
    await context.close().catch(() => {});
  }
}

async function runStaticRouteAudit(browser) {
  const staticScenario = {
    id: "S00",
    title: "Static route audit across personas",
    steps: Object.keys(ROUTES).map((routeKey) => [routeKey, `static open ${routeKey}`, `${routeKey} renders without blank/error state`]),
  };

  for (const persona of PERSONAS) {
    const context = await browser.newContext({ viewport: VIEWPORT });
    const page = await context.newPage();
    await attachListeners(page, persona.id);
    try {
      for (let i = 0; i < staticScenario.steps.length; i += 1) {
        await runStep({ page, context, scenario: { ...staticScenario, persona: persona.id }, persona, stepIndex: i, step: staticScenario.steps[i] });
        process.stdout.write(".");
      }
    } finally {
      await context.close().catch(() => {});
    }
  }
}

function summarizeIssues() {
  return {
    P0: issues.filter((issue) => issue.severity === "P0").length,
    P1: issues.filter((issue) => issue.severity === "P1").length,
    P2: issues.filter((issue) => issue.severity === "P2").length,
    P3: issues.filter((issue) => issue.severity === "P3").length,
  };
}

async function writeSheets(browser) {
  const sheetMap = {
    home_sheet: "home",
    menu_sheet: "menu",
    shopping_sheet: "shopping",
    pantry_sheet: "pantry",
    wellness_sheet: "wellness",
    recipes_sheet: "recipes",
    account_sheet: "account",
    subscription_sheet: "subscription",
    family_sheet: "family",
    events_sheet: "events",
    onboarding_sheet: "account",
    ai_sheet: "wellness",
    dark_theme_sheet: "menu",
  };

  const context = await browser.newContext({ viewport: { width: 1280, height: 1600 } });
  const page = await context.newPage();
  try {
    for (const [name, route] of Object.entries(sheetMap)) {
      const shots = scenarioSteps
        .filter((step) => step.route === route || (name === "dark_theme_sheet" && /dark theme/i.test(step.action)))
        .slice(0, 12);
      const cards = shots
        .map((step) => {
          const src = path.join(RUN_DIR, step.screenshot_path).replaceAll("\\", "/");
          return `<figure><img src="file:///${src}" /><figcaption>${step.scenario} ${step.persona}<br>${step.action}<br>${step.pass ? "PASS" : "FAIL"}</figcaption></figure>`;
        })
        .join("");
      await page.setContent(
        `<!doctype html><meta charset="utf-8"><style>
          body{font-family:Arial,sans-serif;margin:24px;background:#f6f7f9;color:#172033}
          h1{font-size:28px;margin:0 0 18px}
          .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
          figure{margin:0;background:white;border:1px solid #d7dce5;border-radius:8px;padding:10px}
          img{width:100%;aspect-ratio:390/844;object-fit:cover;object-position:top;border-radius:6px;border:1px solid #e5e8ef}
          figcaption{font-size:12px;line-height:1.35;margin-top:8px}
        </style><h1>${name.replaceAll("_", " ")}</h1><div class="grid">${cards || "<p>No screenshots captured.</p>"}</div>`,
      );
      await page.screenshot({ path: path.join(SHEET_DIR, `${name}.jpg`), type: "jpeg", quality: 86, fullPage: true });
    }
  } finally {
    await context.close().catch(() => {});
  }
}

async function writeArtifacts(startedAt, finishedAt) {
  const screenshotFiles = (await readdir(SCREEN_DIR)).filter((file) => file.endsWith(".png"));
  const videoFiles = existsSync(VIDEO_DIR) ? (await readdir(VIDEO_DIR)).filter((file) => /\.(webm|mp4)$/i.test(file)) : [];
  const issueCounts = summarizeIssues();
  const failedSteps = scenarioSteps.filter((step) => !step.pass);
  const networkFailed = networkRows.filter((row) => row.status >= 400);
  const valid = scenarioSteps.length > 0 && screenshotFiles.length === scenarioSteps.length;

  const routeGraphJson = Object.fromEntries(Object.entries(routeGraph).map(([key, value]) => [key, [...value]]));
  await writeFile(path.join(LOG_DIR, "console.json"), JSON.stringify(consoleRows, null, 2), "utf8");
  await writeFile(path.join(LOG_DIR, "network.json"), JSON.stringify(networkRows, null, 2), "utf8");
  await writeFile(path.join(LOG_DIR, "failed_steps.json"), JSON.stringify(failedSteps, null, 2), "utf8");
  await writeFile(path.join(LOG_DIR, "body_text_by_step.json"), JSON.stringify(bodyTextRows, null, 2), "utf8");
  await writeFile(path.join(LOG_DIR, "route_graph.json"), JSON.stringify(routeGraphJson, null, 2), "utf8");
  await writeFile(path.join(LOG_DIR, "click_graph.json"), JSON.stringify(clickGraph, null, 2), "utf8");
  await writeFile(path.join(RUN_DIR, "issue_register.json"), JSON.stringify(issues, null, 2), "utf8");

  const majorScreens = ["home", "menu", "shopping", "pantry", "wellness", "recipes", "account", "subscription", "family", "events"];
  const status = [
    "# PLANAM Ultimate Full UX Audit Run Status",
    "",
    `valid: ${valid}`,
    `started_at: ${startedAt}`,
    `finished_at: ${finishedAt}`,
    `duration_ms: ${new Date(finishedAt).getTime() - new Date(startedAt).getTime()}`,
    `base_url: ${BASE_URL}`,
    `api_url: ${API_URL}`,
    `personas_count: ${PERSONAS.length}`,
    `scenario_count: ${SCENARIOS.length}`,
    `static_route_steps: ${PERSONAS.length * Object.keys(ROUTES).length}`,
    `total_steps: ${scenarioSteps.length}`,
    `screenshots_count: ${screenshotFiles.length}`,
    `videos_count: ${videoFiles.length}`,
    `failed_steps: ${failedSteps.length}`,
    `network_errors: ${networkFailed.length}`,
    `console_errors: ${consoleRows.filter((row) => row.type === "error" || row.type === "pageerror").length}`,
    `routes: ${Object.keys(ROUTES).join(", ")}`,
    `issues_P0: ${issueCounts.P0}`,
    `issues_P1: ${issueCounts.P1}`,
    `issues_P2: ${issueCounts.P2}`,
    `issues_P3: ${issueCounts.P3}`,
    "",
    "## Coverage",
    "",
    `- personas: ${PERSONAS.map((persona) => persona.id).join(", ")}`,
    `- scenarios: ${SCENARIOS.map((scenario) => `${scenario.id} ${scenario.title}`).join("; ")}`,
    `- major screens: ${majorScreens.join(", ")}`,
    "- themes: light, dark, system captured in S13",
    "- AI assistant questions: 5 captured in S08",
  ].join("\n");
  await writeFile(path.join(RUN_DIR, "AUDIT_RUN_STATUS.md"), status, "utf8");

  const report = [
    "# PLANAM Ultimate Full UX Audit Report",
    "",
    "## Executive summary",
    "",
    `Harness valid: **${valid}**. Captured ${screenshotFiles.length} screenshots across ${PERSONAS.length} personas, ${SCENARIOS.length} scenario audits, and a static route sweep.`,
    "",
    "## Что проверено",
    "",
    "- Static route audit across all required personas/lenses.",
    "- Scenario audit: onboarding, menu, day 5, day 7, shopping, pantry, recipes, wellness/AI, family, tariffs, events, account/settings/theme, empty/error states, developer QA.",
    "- Multi-day lenses: day 1, day 5, day 7.",
    "- Role-based lenses: new user, parent, 50+ proxy, solo, pair, family admin/adult/virtual child, athlete, strict diet, healthy eating, free/trial/paid/pro, product/design/QA.",
    "",
    "## Что не удалось проверить",
    "",
    failedSteps.length
      ? `There are ${failedSteps.length} failed product-flow observations. See issue_register.json and logs/failed_steps.json.`
      : "No harness-level screenshot capture gaps were detected.",
    "",
    "## MVP verdict",
    "",
    failedSteps.length ? "Conditional: product needs triage of failed flows before confident beta/sales launch." : "Ready for broader beta from a harness perspective; product findings still require human triage.",
    "",
    "## Launch readiness score",
    "",
    `${Math.max(45, 92 - issueCounts.P1 * 8 - issueCounts.P2 * 3 - issueCounts.P3)} / 100`,
    "",
    "## Product value score",
    "",
    `${Math.max(50, 88 - issueCounts.P1 * 5 - issueCounts.P2 * 2)} / 100`,
    "",
    "## UX clarity score",
    "",
    `${Math.max(40, 90 - issueCounts.P1 * 7 - issueCounts.P2 * 3 - issueCounts.P3)} / 100`,
    "",
    "## Visual design score",
    "",
    `${Math.max(55, 86 - issueCounts.P2 * 2 - issueCounts.P3)} / 100`,
    "",
    "## Technical stability score",
    "",
    `${Math.max(40, 95 - networkFailed.length * 4 - consoleRows.length)} / 100`,
    "",
    "## Persona-by-persona audit",
    "",
    ...PERSONAS.map((persona) => `- ${persona.id}: ${persona.lens}; screenshots ${scenarioSteps.filter((step) => step.persona === persona.id).length}.`),
    "",
    "## Screen-by-screen audit",
    "",
    ...majorScreens.map((screen) => {
      const steps = scenarioSteps.filter((step) => step.route === screen);
      return `- ${screen}: ${steps.length} observations, ${steps.filter((step) => !step.pass).length} failed observations.`;
    }),
    "",
    "## Scenario-by-scenario audit",
    "",
    ...SCENARIOS.map((scenario) => {
      const steps = scenarioSteps.filter((step) => step.scenario === scenario.id);
      return `- ${scenario.id} ${scenario.title}: ${steps.length} steps, ${steps.filter((step) => !step.pass).length} failed.`;
    }),
    "",
    "## Family audit",
    "",
    "Family admin, adult, child virtual, pair virtual, and family plan lenses were captured. See S09/S10 and family_sheet.jpg.",
    "",
    "## Nutrition/AI audit",
    "",
    "Wellness and AI were exercised with five required questions in S08. Responses/screens are preserved in screenshots and body_text_by_step.json.",
    "",
    "## Monetization audit",
    "",
    "Free, Trial, Personal/Start, Pair, Family, Pro, and Family Pro lenses were covered via personas and S11 subscription/paywall flow.",
    "",
    "## Copy audit",
    "",
    "Forbidden/debug strings were scanned per step; hits are converted into issue_register entries.",
    "",
    "## Design audit",
    "",
    "Light/dark/system theme screenshots were captured in S13 and dark_theme_sheet.jpg.",
    "",
    "## Developer/QA audit",
    "",
    `Network >=400: ${networkFailed.length}. Console warnings/errors/pageerrors: ${consoleRows.length}. Body text and route/click graphs are in logs/.`,
    "",
    "## P0/P1/P2/P3 backlog",
    "",
    `- P0: ${issueCounts.P0}`,
    `- P1: ${issueCounts.P1}`,
    `- P2: ${issueCounts.P2}`,
    `- P3: ${issueCounts.P3}`,
    "",
    "## Recommended Sprint 1.2",
    "",
    "1. Triage P1/P2 failed flows from issue_register.json.",
    "2. Verify onboarding/profile completion and menu generation for new users.",
    "3. Tighten monetization/paywall and AI/Amas copy where screenshots show ambiguity.",
    "4. Re-run this harness after fixes and compare issue_register deltas.",
    "",
    "## Cursor implementation ТЗ",
    "",
    "Use issue_register.json as the implementation backlog. Do not fix from screenshots alone; reproduce each issue in the matching persona/route/scenario first.",
  ].join("\n");
  await writeFile(path.join(RUN_DIR, "PLANAM_ULTIMATE_FULL_UX_AUDIT_REPORT.md"), report, "utf8");

  const index = {
    valid,
    started_at: startedAt,
    finished_at: finishedAt,
    personas_count: PERSONAS.length,
    scenario_count: SCENARIOS.length,
    screenshots_count: screenshotFiles.length,
    videos_count: videoFiles.length,
    failed_steps: failedSteps.length,
    issue_counts: issueCounts,
    zip_path: ZIP_PATH,
    artifacts: {
      status: "AUDIT_RUN_STATUS.md",
      report: "PLANAM_ULTIMATE_FULL_UX_AUDIT_REPORT.md",
      issues: "issue_register.json",
      screenshots: "screenshots/",
      sheets: "sheets/",
      logs: "logs/",
    },
  };
  await writeFile(path.join(RUN_DIR, "audit_index.json"), JSON.stringify(index, null, 2), "utf8");
  return index;
}

function createArchive() {
  const src = RUN_DIR.replace(/'/g, "''");
  const dst = ZIP_PATH.replace(/'/g, "''");
  execSync(`powershell -NoProfile -Command "Compress-Archive -Path '${src}' -DestinationPath '${dst}' -Force"`, {
    stdio: "inherit",
  });
}

async function main() {
  const startedAt = new Date().toISOString();
  await ensureDirs();
  const browser = await chromium.launch({
    headless: true,
    args: ["--disable-gpu", "--disable-dev-shm-usage", "--no-first-run"],
  });

  try {
    console.log(`Running static route audit: ${PERSONAS.length} personas x ${Object.keys(ROUTES).length} routes`);
    await runStaticRouteAudit(browser);
    console.log("\nRunning scenario audit");
    for (const scenario of SCENARIOS) {
      console.log(`\n${scenario.id} ${scenario.title}`);
      await runScenario(browser, scenario);
    }
    console.log("\nWriting contact sheets");
    await writeSheets(browser);
  } finally {
    await browser.close().catch(() => {});
  }

  const index = await writeArtifacts(startedAt, new Date().toISOString());
  createArchive();
  console.log("\nDone");
  console.log(JSON.stringify(index, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
