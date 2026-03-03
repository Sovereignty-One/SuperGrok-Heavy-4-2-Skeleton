import pytest
from weather_dashboard import app

@pytest.mark.asyncio
async def test_weather_endpoint():
    test_client = app.test_client()
    response = await test_client.get('/api/weather?city=London')
    assert response.status_code == 200
    data = await response.get_json()
    assert 'city' in data
    assert data['city'] == 'London'