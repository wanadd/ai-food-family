from datetime import datetime

from pydantic import BaseModel, Field


class DeferredAdviceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=2000)


class DeferredAdviceResponse(BaseModel):
    id: int
    advice_key: str
    title: str
    body: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeferredAdviceUpdate(BaseModel):
    status: str = Field(max_length=16)
