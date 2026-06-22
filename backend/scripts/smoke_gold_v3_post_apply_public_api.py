"""Public API smoke checks for upgraded Gold V3 recipes (read-only HTTP)."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "backend" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_gold_v3_post_apply_common import (  # noqa: E402
    extract_upgraded_recipe_ids,
    fetch_recipe_rows,
    has_source_leakage,
    has_user_facing_garbage,
    import_sqlalchemy,
    now,
    write_json,
)


REPORT_JSON = ROOT / "reports" / "SPRINT_1_3M_PUBLIC_API_SMOKE.json"
REPORT_MD = ROOT / "reports" / "SPRINT_1_3M_PUBLIC_API_SMOKE.md"
DEFAULT_API_BASE = os.environ.get("PLANAM_AUDIT_API_URL") or os.environ.get("API_URL") or "http://localhost:8000"


def http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: int = 20) -> tuple[int, str, Any | None]:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = None
    return status, body, parsed


def obtain_audit_headers(api_base: str) -> dict[str, str]:
    persona = os.environ.get("PLANAM_AUDIT_PERSONA", "audit_personal_day5")
    status, _, payload = http_post_json(f"{api_base}/auth/audit-login?persona={urllib.parse.quote(persona)}", {})
    if status != 200 or not isinstance(payload, dict):
        return {}
    token = payload.get("audit_init_data")
    if not token:
        return {}
    return {"Authorization": f"tma {token}"}


def http_get(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> tuple[int, str, dict[str, Any] | list[Any] | None]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    parsed = None
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = None
    return status, body, parsed


def sample_search_terms(rows: list[dict[str, Any]]) -> list[str]:
    terms = []
    for row in rows[:5]:
        title = str(row.get("display_title") or row.get("title") or "").strip()
        if title:
            terms.append(title.split()[0])
    return [term for term in terms if len(term) >= 4][:3]


def evaluate_payload(payload: Any) -> list[str]:
    text = json.dumps(payload, ensure_ascii=False).lower()
    blockers = []
    if has_user_facing_garbage(text):
        blockers.append("user_facing_garbage")
    if has_source_leakage(text):
        blockers.append("source_leakage")
    return blockers


def build_report() -> dict[str, Any]:
    api_base = DEFAULT_API_BASE.rstrip("/")
    id_report = extract_upgraded_recipe_ids()
    recipe_ids = id_report.get("recipe_ids") or []
    checks: list[dict[str, Any]] = []
    hard_fail = 0
    auth_headers = obtain_audit_headers(api_base)
    http_auth_available = bool(auth_headers)

    list_status, _, list_payload = http_get(f"{api_base}/recipes?limit=200", auth_headers)
    list_blockers = []
    if list_status in {401, 403} and not http_auth_available:
        list_blockers.append("auth_required")
    elif list_status != 200:
        list_blockers.append(f"http_{list_status}")
    elif isinstance(list_payload, dict):
        list_blockers.extend(evaluate_payload(list_payload))
        items = list_payload.get("items") or list_payload.get("recipes") or []
        list_ids = {int(item.get("id")) for item in items if isinstance(item, dict) and item.get("id") is not None}
        if recipe_ids[:5] and not any(recipe_id in list_ids for recipe_id in recipe_ids[:5]):
            list_blockers.append("upgraded_recipes_not_visible_in_first_page")
    else:
        list_blockers.append("invalid_list_payload")
    if list_blockers and "auth_required" not in list_blockers:
        hard_fail += 1
    checks.append({"name": "recipes_list", "url": f"{api_base}/recipes?limit=200", "status": list_status, "blockers": list_blockers})

    detail_rows = []
    if import_sqlalchemy() is not None:
        try:
            detail_rows, _, _ = fetch_recipe_rows(recipe_ids[:5])
        except Exception:
            detail_rows = []
    search_terms = sample_search_terms(detail_rows)

    for recipe_id in recipe_ids:
        status, _, payload = http_get(f"{api_base}/recipes/{recipe_id}", auth_headers)
        blockers = []
        if status in {401, 403} and not http_auth_available:
            blockers.append("auth_required")
        elif status != 200:
            blockers.append(f"http_{status}")
        elif isinstance(payload, dict):
            blockers.extend(evaluate_payload(payload))
            if not (payload.get("title") or payload.get("display_title")):
                blockers.append("missing_title")
        else:
            blockers.append("invalid_detail_payload")
        if blockers and "auth_required" not in blockers:
            hard_fail += 1
        checks.append(
            {
                "name": f"recipe_detail_{recipe_id}",
                "url": f"{api_base}/recipes/{recipe_id}",
                "status": status,
                "blockers": blockers,
            }
        )

    for term in search_terms:
        query = urllib.parse.quote(term)
        status, _, payload = http_get(f"{api_base}/recipes?q={query}&limit=50", auth_headers)
        blockers = []
        if status in {401, 403} and not http_auth_available:
            blockers.append("auth_required")
        elif status != 200:
            blockers.append(f"http_{status}")
        elif isinstance(payload, dict):
            blockers.extend(evaluate_payload(payload))
            items = payload.get("items") or payload.get("recipes") or []
            if not items:
                blockers.append("search_no_results")
        else:
            blockers.append("invalid_search_payload")
        if blockers and "auth_required" not in blockers:
            hard_fail += 1
        checks.append(
            {
                "name": f"search_{term}",
                "url": f"{api_base}/recipes?q={query}&limit=50",
                "status": status,
                "blockers": blockers,
            }
        )

    auth_only = all(
        check.get("blockers") == ["auth_required"] or not check.get("blockers")
        for check in checks
        if check.get("blockers")
    ) and not http_auth_available

    return {
        "generated_at": now(),
        "ok": hard_fail == 0,
        "hard_fail": hard_fail,
        "api_base": api_base,
        "http_auth_available": http_auth_available,
        "http_auth_skipped": auth_only,
        "recipe_id_count": len(recipe_ids),
        "search_terms": search_terms,
        "checks": checks,
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 1.3M Public API Smoke",
        "",
        f"Generated: `{report['generated_at']}`",
        f"ok: `{report.get('ok')}`",
        f"hard_fail: `{report.get('hard_fail')}`",
        f"api_base: `{report.get('api_base')}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks") or []:
        if check.get("blockers"):
            lines.append(f"- FAIL `{check['name']}` status={check['status']} blockers={check['blockers']}")
        else:
            lines.append(f"- OK `{check['name']}` status={check['status']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    write_json(REPORT_JSON, report)
    REPORT_MD.write_text(render(report), encoding="utf-8")
    print(f"Wrote {REPORT_MD}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
