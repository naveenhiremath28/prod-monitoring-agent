from fastapi import FastAPI
from api.routes import routes
from api.models.models import Base
from api.database.session import engine
from api.exceptions.exceptions import IssueException
from api.middleware.error_handler import issue_exception_handler
import asyncio

app = FastAPI(title="Issues API")

# Register exception handler
app.add_exception_handler(IssueException, issue_exception_handler)

# Async function to handle DB initialization
async def init_models():
    async with engine.begin() as conn:
        # Drop tables first, then create (if that's what you want)
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    # Run async DB init
    asyncio.run(init_models())

# Register routes after DB is ready
app.include_router(routes.router, prefix="/api/v1", tags=["issues"])