from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from api.schemas.base_schema import BaseRequest, BaseResponse

class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    analysis: Optional[str] = None
    application_type: Optional[str] = None
    occurrence: Optional[int] = 0
    status: str = "open"
    severity: str
    error_type: Optional[str] = None

class IssueCreate(IssueBase):
    pass

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    analysis: Optional[str] = None
    application_type: Optional[str] = None
    occurrence: Optional[int] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    error_type: Optional[str] = None

class IssueResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    analysis: Optional[str]
    application_type: Optional[str]
    occurrence: int
    status: str
    severity: Optional[str] = None
    error_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Request Models
class IssueCreateRequest(BaseRequest[IssueCreate]):
    pass

class IssueUpdateRequest(BaseRequest[IssueUpdate]):
    pass

# Response Models
class IssueListResponse(BaseResponse[List[IssueResponse]]):
    result: List[IssueResponse] = []

class SingleIssueResponse(BaseResponse[Optional[IssueResponse]]):
    result: Optional[IssueResponse] = None

class CreateIssueResponse(BaseResponse[Optional[IssueResponse]]):
    result: Optional[IssueResponse] = None

class UpdateIssueResponse(BaseResponse[Optional[IssueResponse]]):
    result: Optional[IssueResponse] = None

class DeleteIssueResponse(BaseResponse[dict]):
    result: dict = {"message": ""}
