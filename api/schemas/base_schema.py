from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

T = TypeVar('T')

class RequestParams(BaseModel):
    msgid: UUID = Field(default_factory=uuid4)

class BaseRequest(BaseModel, Generic[T]):
    id: str
    ver: str = "v1"
    ts: datetime = Field(default_factory=datetime.now)
    params: RequestParams = Field(default_factory=RequestParams)
    request: T

class ResponseParams(BaseModel):
    status: str
    msgid: UUID
    resmsgid: UUID = Field(default_factory=uuid4)

class BaseResponse(BaseModel, Generic[T]):
    id: str
    ver: str = "v1"
    ts: datetime = Field(default_factory=datetime.now)
    params: ResponseParams
    responseCode: str
    result: T = None  # Default value will be overridden by child classes
