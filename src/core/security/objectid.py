from typing import Annotated, Any

from bson import ObjectId
from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema


def _validate_object_id(value: Any) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError(f"Invalid ObjectId: {value}")


PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(_validate_object_id),
    PlainSerializer(lambda v: str(v), return_type=str),
    WithJsonSchema({"type": "string"}, mode="serialization"),
]
