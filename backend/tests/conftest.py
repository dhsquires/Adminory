"""Pytest configuration and fixtures."""
from importlib.util import find_spec
from typing import AsyncGenerator

import pytest


if find_spec("pytest_cov") is None:

    def pytest_addoption(parser):
        """Accept repository coverage flags when pytest-cov is unavailable."""
        group = parser.getgroup("cov")
        group.addoption("--cov", action="append", default=[])
        group.addoption("--cov-report", action="append", default=[])


# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://adminory:adminory_dev_password@localhost:5432/adminory_test"


@pytest.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.database import Base

    test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[object, None]:
    """Get test database session."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    test_session_local = async_sessionmaker(
        setup_database,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with test_session_local() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: object) -> AsyncGenerator[object, None]:
    """Get test HTTP client."""
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock application settings."""
    # Add mocked settings here as needed
    pass
