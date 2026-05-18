---
description: Generate an Alembic migration for the current service
argument-hint: <description>
---

Generate an Alembic migration with description `$ARGUMENTS`.

Steps:

1. Determine which service we're working in. If the user is in `services/<name>/`, that's the target. Otherwise, ASK.
2. Confirm the SQLAlchemy models for the change are already written. If not, stop and tell the user to write the models first.
3. From the service directory, run:
   ```
   alembic revision --autogenerate -m "$ARGUMENTS"
   ```
4. Open the generated migration file in `alembic/versions/`.
5. Review the migration for correctness:
   - Are all expected `op.create_table` / `op.add_column` operations present?
   - Are foreign keys correct with `ondelete` policies?
   - Are indexes included?
   - For TimescaleDB hypertables: was `op.execute("SELECT create_hypertable(...)")` added? (Alembic won't autogenerate this.)
   - For pgvector columns: was the extension created? `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`
   - Are there any unwanted operations from autogeneration noise?
6. Make any manual adjustments needed.
7. Update `docs/architecture/02-database-schema.md` to reflect the new schema.
8. Show the user the final migration and ask for confirmation before running `alembic upgrade head`.

NEVER run `alembic upgrade head` without confirmation in this command. The user runs it themselves after review.

NEVER write to or modify production / staging databases here. This command only generates migrations against local Postgres.
