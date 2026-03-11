from __future__ import annotations

from typing import Literal

IFlowErrorCategory = Literal[
    "validation",
    "auth",
    "permission",
    "not_found",
    "business",
    "external",
    "infrastructure",
    "unexpected",
]


class IFlowError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        category: IFlowErrorCategory,
        status: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.status = status

    def body(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category,
                "status": self.status,
            }
        }
