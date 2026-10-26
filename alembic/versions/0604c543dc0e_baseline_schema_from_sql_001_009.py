"""baseline schema from sql 001-009

Applies sql/001-009 in order (each is idempotent), reproducing what
docker-entrypoint-initdb.d used to set up. Existing databases are stamped
at this revision instead of re-running these files.

Revision ID: 0604c543dc0e
Revises:
Create Date: 2026-10-26 16:46:48.626130

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0604c543dc0e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"

BASELINE_FILES = [
    "001_init.sql",
    "002_schema.sql",
    "003_indexes.sql",
    "004_forest_stand_features.sql",
    "005_forest_stand_fetch_log.sql",
    "006_parcels_unique_property_id.sql",
    "007_special_habitat_features.sql",
    "008_special_habitat_fetch_log.sql",
    "009_backfill_nan_numeric_columns.sql",
]


def upgrade() -> None:
    for filename in BASELINE_FILES:
        op.execute((SQL_DIR / filename).read_text())


def downgrade() -> None:
    # First revision — downgrading means dropping the whole schema.
    raise NotImplementedError("No downgrade path before the baseline revision.")
