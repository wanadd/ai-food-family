import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.menu import MenuVariant
from app.services.app_scope import AppScope
from app.services.ai import MenuAiResult, generate_menu_ai
from app.services.ai_errors import AiError, AiUnavailableError
from app.services.menu_context import MenuGenerationContext
from app.services.menu_recipe_builder import build_menus_from_recipes
logger = logging.getLogger(__name__)


async def generate_menus(
    context: MenuGenerationContext,
    *,
    db: Session | None = None,
    user: User | None = None,
    scope: AppScope | None = None,
    persons_count: int | None = None,
    drink_mode: str = "none",
    allow_alcohol: bool = False,
    plan_days: int = 1,
) -> tuple[list[MenuVariant], bool]:
    """OpenAI first (if configured), then recipe DB, then heuristic fallback."""
    if db and user and scope:
        try:
            result: MenuAiResult = await generate_menu_ai(
                context,
                db=db,
                user=user,
                scope=scope,
                persons_count=persons_count,
                drink_mode=drink_mode,
                allow_alcohol=allow_alcohol,
                plan_days=plan_days,
            )
            from app.services.menu_ai_legacy import _apply_leftovers

            menus = _apply_leftovers(result.menus, context.leftovers)
            return menus, True
        except AiUnavailableError:
            pass
        except AiError:
            logger.exception("OpenAI menu generation failed, trying recipe DB")
        except KeyError:
            logger.exception("OpenAI menu JSON parse KeyError, trying recipe DB")
        except Exception:
            logger.exception("OpenAI menu generation failed, trying recipe DB")

        recipe_menus = build_menus_from_recipes(
            db,
            user,
            context,
            scope,
            persons=persons_count or context.members_count,
            drink_mode=drink_mode,  # type: ignore[arg-type]
            allow_alcohol=allow_alcohol,
            plan_mode="healthy",
        )
        if recipe_menus:
            from app.services.menu_ai_legacy import _apply_leftovers

            return _apply_leftovers(recipe_menus, context.leftovers), False

    from app.services.menu_ai_legacy import _apply_leftovers, _generate_fallback

    menus = _generate_fallback(context)
    return _apply_leftovers(menus, context.leftovers), False


async def replace_meal(
    context: MenuGenerationContext,
    menu: MenuVariant,
    meal_index: int,
    hint: str | None,
    *,
    db: Session | None = None,
    user: User | None = None,
    scope: AppScope | None = None,
) -> MenuVariant:
    if meal_index < 0 or meal_index >= len(menu.meals):
        raise ValueError("Invalid meal index")

    from app.services.menu_ai_legacy import replace_meal as legacy_replace

    return await legacy_replace(
        context, menu, meal_index, hint, db=db, user=user, scope=scope
    )
