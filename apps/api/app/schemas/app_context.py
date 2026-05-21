from typing import Literal

from pydantic import BaseModel

from app.schemas.family import FamilyResponse

AppModeType = Literal["personal", "family"]


class AppContextResponse(BaseModel):
    active_mode: AppModeType
    has_family: bool
    can_use_family_mode: bool
    family: FamilyResponse | None = None


class AppContextUpdate(BaseModel):
    active_mode: AppModeType
