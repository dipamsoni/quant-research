from sqlalchemy.types import UserDefinedType


class CIText(UserDefinedType):
    """PostgreSQL CITEXT — case-insensitive text. Requires citext extension."""

    cache_ok = True

    def get_col_spec(self, **kw):
        return "CITEXT"

    def bind_processor(self, dialect):
        return None

    def result_processor(self, dialect, coltype):
        return None
