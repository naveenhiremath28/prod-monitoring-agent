from typing import Any, List, Optional
from sqlalchemy import text, create_engine, Engine
from sqlalchemy.orm import Session

class PostgresService:
    def __init__(self, engine: Engine):
        self.engine = engine

    # --- Single row ---
    def execute_select_one(self, sql: str, params: dict = {}) -> Optional[dict]:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params).fetchone()
            return dict(result._mapping) if result else None

    # --- Multiple rows ---
    def execute_select_all(self, sql: str, params: dict = {}) -> List[dict]:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return [dict(row._mapping) for row in result.fetchall()]

    # --- Insert or update and return row (like UPSERT) ---
    def execute_upsert(self, sql: str, params: dict = {}) -> Optional[dict]:
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), params)
            row = result.fetchone()
            return dict(row._mapping) if row else None

    # --- Insert only, return affected rows ---
    def execute_insert(self, sql: str, params: dict = {}) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), params)
            return result.rowcount

    # --- Generic query returning list of dicts ---
    def execute_query(self, sql: str, params: dict = {}) -> List[dict]:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return [dict(row._mapping) for row in result.fetchall()]

    # --- Update only, return affected rows ---
    def execute_update(self, sql: str, params: dict = {}) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), params)
            return result.rowcount

    # --- Select one scalar value ---
    def execute_select_one_field(self, sql: str, params: dict = {}) -> Any:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            return result.scalar_one_or_none()