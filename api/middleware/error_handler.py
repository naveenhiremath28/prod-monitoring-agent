from fastapi import Request
from fastapi.responses import JSONResponse
from uuid import uuid4
from datetime import datetime

from api.exceptions.exceptions import IssueException
from api.schemas.base_schema import ResponseParams

async def issue_exception_handler(request: Request, exc: IssueException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "id": request.url.path,
            "ver": "v1",
            "ts": datetime.now().isoformat(),
            "params": {
                "status": "FAILED",
                "msgid": str(uuid4()),
                "errmsg": exc.message
            },
            "responseCode": exc.err_code,
            "result": None
        }
    )
