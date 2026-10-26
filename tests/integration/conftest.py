import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from nature_screening.db.connection import get_engine

# Deliberately not a real Finnish kiinteistötunnus — safe to insert/delete
# in a real (even shared) dev database without colliding with actual data.
TEST_PROPERTY_ID = "999-999-9999-9999"


@pytest.fixture(scope="session", autouse=True)
def _require_postgis():
    try:
        with get_engine().connect():
            pass
    except OperationalError:
        pytest.skip("PostGIS not reachable — start it with `docker compose up -d db`.")


@pytest.fixture
def clean_test_parcel():
    """Deletes any leftover row for TEST_PROPERTY_ID before and after the
    test, so a prior failed run (or the test itself) never leaves data
    behind in core.parcels."""

    def _delete():
        with get_engine().begin() as connection:
            connection.execute(
                text("DELETE FROM core.parcels WHERE property_id = :property_id"),
                {"property_id": TEST_PROPERTY_ID},
            )

    _delete()
    yield TEST_PROPERTY_ID
    _delete()
