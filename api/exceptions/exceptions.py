from fastapi import status

class IssueException(Exception):
    def __init__(
        self,
        err_code: str = "FAILED",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "An error occurred",
        error: Exception = None
    ):
        self.err_code = err_code
        self.status_code = status_code
        self.message = message
        self.error = error
        super().__init__(self.message)
