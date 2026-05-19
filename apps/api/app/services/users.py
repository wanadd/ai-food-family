from sqlalchemy.orm import Session

from app.models.user import User
from app.telegram.validate import TelegramWebAppUser


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
