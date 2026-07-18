"""Common API response wrappers."""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class CamelModel(BaseModel):
    """Base model that (de)serializes using camelCase aliases for fields."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: "".join(
            [field_name.split("_")[0], *(w.capitalize() for w in field_name.split("_")[1:])]
        ),
    )


class Meta(BaseModel):
    page: Optional[int] = None
    size: Optional[int] = None
    total: Optional[int] = None


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: Optional[Meta] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class BoundingBox(CamelModel):
    x: float
    y: float
    width: float
    height: float


def ok(data: Any, meta: Optional[Meta] = None) -> dict:
    """Build a success envelope dict."""
    payload: dict = {"data": data}
    if meta is not None:
        payload["meta"] = meta.model_dump(exclude_none=True)
    return payload


def err(code: str, message: str, details: Optional[Any] = None) -> dict:
    """Build an error envelope dict."""
    return {"error": {"code": code, "message": message, "details": details}}