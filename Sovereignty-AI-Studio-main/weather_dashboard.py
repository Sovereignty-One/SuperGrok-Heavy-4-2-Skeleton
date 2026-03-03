# Wrapper module to make weather_dashboard importable from root
# This allows test_weather.py to import from weather_dashboard directly
from apps.dashboards.weather_dashboard import app
