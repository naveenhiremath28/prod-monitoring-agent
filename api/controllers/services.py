from datetime import datetime
from uuid import UUID, uuid4
from fastapi import status
from sqlalchemy import Engine

from api.schemas.base_schema import ResponseParams
from api.schemas.schema import (
    IssueCreate, IssueUpdate,
    IssueListResponse, SingleIssueResponse,
    CreateIssueResponse, UpdateIssueResponse,
    DeleteIssueResponse,
)
from api.config.queries import IssueQueries
from api.controllers.postgres_service import PostgresService
from api.exceptions.exceptions import IssueException


class IssueService:
    def __init__(self, engine: Engine):
        self.db = PostgresService(engine)

    def get_issues(self) -> IssueListResponse:
        try:
            issues = self.db.execute_select_all(IssueQueries.GET_ALL_ISSUES)
            return IssueListResponse(
                id="api.issue.list",
                ver="v1",
                ts=datetime.now().isoformat(),
                params=ResponseParams(status="SUCCESS", msgid=uuid4()),
                responseCode="OK",
                result=issues,
            )
        except IssueException as ie:
            raise ie
        except Exception as e:
            raise IssueException(
                err_code="FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to get issues",
                error=e,
            )

    def get_issue_by_id(self, issue_id: UUID) -> SingleIssueResponse:
        try:
            issue = self.db.execute_select_one(
                IssueQueries.GET_ISSUE_BY_ID,
                {"issue_id": str(issue_id)}
            )
            if not issue:
                raise IssueException(
                    err_code="NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Issue with id {issue_id} not found",
                )

            return SingleIssueResponse(
                id="api.issue.get",
                ver="v1",
                ts=datetime.now().isoformat(),
                params=ResponseParams(status="SUCCESS", msgid=uuid4()),
                responseCode="OK",
                result=issue,
            )
        except IssueException as ie:
            raise ie
        except Exception as e:
            raise IssueException(
                err_code="FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to get issue",
                error=e,
            )

    def create_issue(self, request: IssueCreate) -> CreateIssueResponse:
        try:
            now = datetime.utcnow()
            params = {
                **request.model_dump(),
                "created_at": now,
                "updated_at": now,
            }
            result = self.db.execute_upsert(IssueQueries.CREATE_ISSUE, params)

            return CreateIssueResponse(
                id="api.issue.create",
                ver="v1",
                ts=datetime.now().isoformat(),
                params=ResponseParams(status="SUCCESS", msgid=uuid4()),
                responseCode="OK",
                result=result if result else {"message": "Issue created successfully"},
            )
        except IssueException as ie:
            raise ie
        except Exception as e:
            raise IssueException(
                err_code="FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create issue",
                error=e,
            )

    def update_issue(self, issue_id: UUID, request: IssueUpdate) -> UpdateIssueResponse:
        try:
            existing = self.db.execute_select_one(
                IssueQueries.GET_ISSUE_BY_ID,
                {"issue_id": str(issue_id)}
            )
            if not existing:
                raise IssueException(
                    err_code="NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Issue with id {issue_id} not found",
                )

            params = {
                **request.model_dump(),
                "updated_at": datetime.utcnow(),
                "issue_id": str(issue_id),
            }
            self.db.execute_upsert(IssueQueries.UPDATE_ISSUE, params)

            # Fetch the updated row fully
            updated_issue = self.db.execute_select_one(
                IssueQueries.GET_ISSUE_BY_ID,
                {"issue_id": str(issue_id)}
            )

            return UpdateIssueResponse(
                id="api.issue.update",
                ver="v1",
                ts=datetime.now().isoformat(),
                params=ResponseParams(status="SUCCESS", msgid=uuid4()),
                responseCode="OK",
                result=updated_issue,
            )
        except IssueException as ie:
            raise ie
        except Exception as e:
            raise IssueException(
                err_code="FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to update issue",
                error=e,
            )

    def delete_issue(self, issue_id: UUID, msgid: UUID) -> DeleteIssueResponse:
        try:
            existing = self.db.execute_select_one(
                IssueQueries.GET_ISSUE_BY_ID,
                {"issue_id": str(issue_id)}
            )
            if not existing:
                raise IssueException(
                    err_code="NOT_FOUND",
                    status_code=status.HTTP_404_NOT_FOUND,
                    message=f"Issue with id {issue_id} not found",
                )

            rows_affected = self.db.execute_update(
                IssueQueries.DELETE_ISSUE,
                {"issue_id": str(issue_id)}
            )
            if not rows_affected:
                raise IssueException(
                    err_code="FAILED",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Delete operation failed",
                )

            return DeleteIssueResponse(
                id="api.issue.delete",
                ver="v1",
                ts=datetime.now().isoformat(),
                params=ResponseParams(status="SUCCESS", msgid=msgid),
                responseCode="OK",
                result={"message": "Issue deleted successfully"},
            )
        except IssueException as ie:
            raise ie
        except Exception as e:
            raise IssueException(
                err_code="FAILED",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to delete issue",
                error=e,
            )