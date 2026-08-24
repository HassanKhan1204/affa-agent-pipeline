"""
Every test gets its own throwaway in-memory SQLite database, seeded with a
few known leads, with the app's get_db dependency pointed at it — the real
DATABASE_URL / Postgres is never touched by the test suite.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Lead

SEED_LEADS = [
    dict(
        category="funder",
        name="Test Foundation",
        subtype="foundation",
        focus_area="Food access",
        fit_reason="Fits well",
        url="https://example.org/test-foundation",
        contact_name="Jane Grants",
        contact_email="jane@example.org",
        contact_phone="555-0100",
        contact_page="https://example.org/contact",
        outreach_message="Hi Jane, ...",
        status="drafted",
    ),
    dict(
        category="partner",
        name="Test Community Org",
        subtype="community_org",
        focus_area="Youth programming",
        fit_reason="Great synergy",
        url="https://example.org/test-partner",
        contact_name="",
        contact_email="",
        contact_phone="",
        contact_page="https://example.org/partner-contact",
        outreach_message="",
        status="new",
    ),
]


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    session.add_all(Lead(**data) for data in SEED_LEADS)
    session.commit()
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
