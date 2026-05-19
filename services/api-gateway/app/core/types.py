from typing import Any

from sqlalchemy.types import UserDefinedType


class CIText(UserDefinedType[str]):
    """PostgreSQL CITEXT — case-insensitive text. Requires citext extension."""

    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:
        return "CITEXT"

    def bind_processor(self, dialect: Any) -> None:
        return None

    def result_processor(self, dialect: Any, coltype: Any) -> None:
        return None
