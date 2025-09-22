import os
from fastapi import FastAPI
from api.routes import routes
from api.models.models import Base
from api.database.session import engine
from api.exceptions.exceptions import IssueException
from api.middleware.error_handler import issue_exception_handler
from dotenv import load_dotenv
import uvicorn
import threading

load_dotenv()

app = FastAPI(title="Issues API")

# Register exception handler
app.add_exception_handler(IssueException, issue_exception_handler)

# Sync function to handle DB initialization
def init_models():
    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

# # Start log monitoring in a separate thread
# def start_log_monitoring():
#     log_file = "/Users/naveenvhiremath/Documents/testing/logs_testing/sample.log"  # Update this path
#     monitor = LogMonitorAgent(log_file)
#     monitor.monitor()

if __name__ == "__main__":
    # Run sync DB init before starting the server
    init_models()
    
    # Start log monitoring in a background thread
    # monitor_thread = threading.Thread(target=start_log_monitoring, daemon=True)
    # monitor_thread.start()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)

# Register routes after DB is ready
app.include_router(routes.router, prefix="/api/v1", tags=["issues"])