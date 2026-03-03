import pytest
from apps.dashboards.weather_dashboard import app


@pytest.mark.asyncio
async def test_weather_endpoint():
    """Test the weather API endpoint returns valid data."""
    test_client = app.test_client()
    response = await test_client.get('/api/weather?city=London')
    assert response.status_code == 200
    data = await response.get_json()
    assert 'city' in data
    assert data['city'] == 'London'


@pytest.mark.asyncio
async def test_forecast_endpoint():
    """Test the forecast API endpoint returns valid data."""
    test_client = app.test_client()
    response = await test_client.get('/api/forecast?city=London')
    assert response.status_code == 200
    data = await response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0