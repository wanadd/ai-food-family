from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.recipes.v2_service import favorite, list_published, recipe_detail, resolve_identifier
from app.v2.authorization import AuthorizedContext, authorized_context
from app.v2.errors import error

router = APIRouter(prefix="/api/v2", tags=["v2-recipes"])


def _context(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_planam_session: str | None = Header(default=None, alias="X-Planam-Session"),
) -> AuthorizedContext:
    return authorized_context(db, authorization=authorization, x_planam_session=x_planam_session)


@router.get("/recipes")
def recipes_list(
    q: str | None = Query(default=None, max_length=160),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: AuthorizedContext = Depends(_context),
) -> dict:
    items, total = list_published(db, query=q, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get("/recipes/{recipe_id}")
def recipe_read(recipe_id: str, db: Session = Depends(get_db), _: AuthorizedContext = Depends(_context)) -> dict:
    recipe, version, archive = resolve_identifier(db, recipe_id)
    if archive is not None:
        return {"status": "ARCHIVE_FALLBACK", "legacy_recipe_id": int(recipe_id), "archive": archive}
    if recipe is None or version is None:
        raise error("not_found", 404)
    return recipe_detail(db, recipe, version)


@router.post("/recipes/{recipe_id}/favorite")
def recipe_favorite(
    recipe_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    context: AuthorizedContext = Depends(_context),
) -> dict:
    if not idempotency_key:
        raise error("validation_error", 422, details={"header": "Idempotency-Key is required"})
    recipe, version, _ = resolve_identifier(db, recipe_id)
    if recipe is None or version is None:
        raise error("not_found", 404)
    result = favorite(db, account_id=context.account.account_id, recipe=recipe, version=version, idempotency_key=idempotency_key)
    db.commit()
    return result
