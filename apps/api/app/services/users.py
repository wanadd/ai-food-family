import re

from sqlalchemy.orm import Session

from app.models.user import User
from app.telegram.validate import TelegramWebAppUser

PHONE_REQUIRED_MESSAGE = (
    "Подтвердите номер телефона в боте: отправьте /start "
    "и нажмите «Поделиться номером»."
)


def normalize_phone(phone: str) -> str:
    cleaned = phone.strip()
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if digits:
        return f"+{digits}"
    return cleaned


def phone_lookup_variants(phone: str) -> list[str]:
    normalized = normalize_phone(phone)
    digits = re.sub(r"\D", "", normalized)
    variants = {phone.strip(), normalized}
    if digits:
        variants.add(f"+{digits}")
        if len(digits) == 11:
            variants.add(f"+{digits}")
            variants.add(digits)
            variants.add(f"8{digits[1:]}")
    return [value for value in variants if value]


def find_user_by_phone(db: Session, phone: str) -> User | None:
    for variant in phone_lookup_variants(phone):
        user = (
            db.query(User).filter(User.phone_number == variant).one_or_none()
        )
        if user is not None:
            return user
    return None


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    return (
        db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    )


def user_has_verified_phone(user: User | None) -> bool:
    return bool(user and user.phone_number and user.phone_number.strip())


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "—"
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 4:
        return f"***{digits[-4:]}"
    return "***"


def upsert_user_from_bot(
    db: Session,
    *,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    language_code: str | None = None,
    phone_number: str | None = None,
) -> tuple[User, bool]:
    user = db.query(User).filter(User.telegram_id == telegram_id).one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            phone_number=phone_number,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.language_code = language_code
    if phone_number:
        user.phone_number = normalize_phone(phone_number)
    db.commit()
    db.refresh(user)
    return user, False


def get_or_create_user(db: Session, telegram_user: TelegramWebAppUser) -> tuple[User, bool]:
    user = db.query(User).filter(User.telegram_id == telegram_user.id).one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code,
            photo_url=telegram_user.photo_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, True

    user.username = telegram_user.username
    user.first_name = telegram_user.first_name
    user.last_name = telegram_user.last_name
    user.language_code = telegram_user.language_code
    user.photo_url = telegram_user.photo_url
    db.commit()
    db.refresh(user)
    return user, False
