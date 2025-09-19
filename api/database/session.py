from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Database connection parameters
DB_PARAMS = {
    "dbname": "prod_monitoring",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432",
    "max_connections": 20  # Default pool size
}

# Create SQLAlchemy engine with psycopg driver
engine = create_engine(
    f"postgresql+psycopg://{DB_PARAMS['user']}:{DB_PARAMS['password']}"
    f"@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['dbname']}",
    pool_size=int(DB_PARAMS["max_connections"]),
    max_overflow=0,
)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
