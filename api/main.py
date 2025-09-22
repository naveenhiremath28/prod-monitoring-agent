from fastapi import FastAPI
from api.routes import routes
from api.models.models import Base
from api.database.session import engine
from api.exceptions.exceptions import IssueException
from api.middleware.error_handler import issue_exception_handler
import uvicorn

app = FastAPI(title="Issues API")

# Register exception handler
app.add_exception_handler(IssueException, issue_exception_handler)

# Sync function to handle DB initialization
def init_models():
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

if __name__ == "__main__":
    # Run sync DB init before starting the server
    init_models()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Register routes after DB is ready
app.include_router(routes.router, prefix="/api/v1", tags=["issues"])