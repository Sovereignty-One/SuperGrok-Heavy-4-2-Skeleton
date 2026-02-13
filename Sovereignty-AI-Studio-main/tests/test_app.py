import pytest
from httpx import AsyncClient
from backend.app.main import app  # Import your FastAPI app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client

@pytest.mark.asyncio
async def test_homepage(client):
    response = await client.get('/')
    assert response.status_code == 200
    data = response.json()
    assert "Welcome to CreativeFlow AI" in data["message"]