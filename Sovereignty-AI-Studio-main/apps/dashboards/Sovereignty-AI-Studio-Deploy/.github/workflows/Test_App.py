import pytest
from httpx import AsyncClient
from your_quart_app import create_app  # Import your Quart app

@pytest.fixture
async def client():
    app = create_app()  # Adjust to your app initialization
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client

@pytest.mark.asyncio
async def test_homepage(client):
    response = await client.get('/')
    assert response.status_code == 200
    assert "Welcome" in response.text  # Adjust as necessary for your app
