# routes.py
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Engine
from starlette.requests import Request

from api.database.session import engine
from api.schemas.schema import (
    IssueCreateRequest, IssueResponse, IssueUpdateRequest,
    IssueListResponse, SingleIssueResponse,
    CreateIssueResponse, UpdateIssueResponse,
    DeleteIssueResponse
)
from api.schemas.base_schema import ResponseParams
from api.controllers.services import IssueService
from api.exceptions.exceptions import IssueException

router = APIRouter()
service = IssueService(engine)


@router.get("/issues", response_model=IssueListResponse)
def get_issues():
    return service.get_issues()


@router.get("/issues/{issue_id}", response_model=SingleIssueResponse)
def get_issue(issue_id: UUID):
    return service.get_issue_by_id(issue_id=issue_id)


@router.post("/issues", response_model=CreateIssueResponse)
def create_issue(request: IssueCreateRequest):
    return service.create_issue(request=request.request)


@router.patch("/issues/{issue_id}", response_model=UpdateIssueResponse)
def update_issue(issue_id: UUID, request: IssueUpdateRequest):
    return service.update_issue(issue_id=issue_id, request=request.request)


@router.delete("/issues/{issue_id}", response_model=DeleteIssueResponse)
def delete_issue(issue_id: UUID):
    return service.delete_issue(issue_id=issue_id)