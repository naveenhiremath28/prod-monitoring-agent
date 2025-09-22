from datetime import datetime
import uuid
from sqlalchemy import ARRAY, TEXT, Column, String, Integer, DateTime, Enum, event, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import expression

Base = declarative_base()

class Issue(Base):
    __tablename__ = "issues"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    analysis = Column(String, nullable=True)
    application_type = Column(String, nullable=True)
    occurrence = Column(Integer, default=0)
    issue_logs = Column(
        ARRAY(TEXT),
        nullable=True,
        default=list
    )
    status = Column(
        Enum("open", "in_progress", "resolved", "closed", name="issue_status"),
        default="open"
    )
    severity = Column(
        Enum("low", "medium", "high", "critical", name="issue_severity"),
        nullable=False
    )
    error_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# SQLAlchemy event listener to update updated_at on any column change
@event.listens_for(Issue, 'before_update')
def receive_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
