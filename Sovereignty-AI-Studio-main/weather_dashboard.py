from quart import Quart, render_template, request, jsonify
import requests
import os
from datetime import datetime

app = Quart(__name__)
app.config['PROVIDE_AUTOMATIC_OPTIONS'] = True

# OpenWeatherMap API configuration
# Users should set their own API key as an environment variable
API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'your_api_key_here')
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'

@app.route('/')
async def index():
    return await render_template('weather_dashboard.html')

@app.route('/api/weather', methods=['GET'])
async def get_weather():
    city = request.args.get('city', 'London')
    
    # Return dummy data for CI/testing if no API key is set
    if API_KEY == 'your_api_key_here':
        return jsonify({
            'city': city,
            'country': 'GB',
            'temperature': 15.0,
            'feels_like': 14.0,
            'description': 'Cloudy',
            'icon': '03d',
            'humidity': 80,
            'pressure': 1013,
            'wind_speed': 3.5,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    try:
        # Get current weather
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        weather_data = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': round(data['main']['temp'], 1),
            'feels_like': round(data['main']['feels_like'], 1),
            'description': data['weather'][0]['description'].capitalize(),
            'icon': data['weather'][0]['icon'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'timestamp': datetime.fromtimestamp(data['dt']).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(weather_data)
    
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': 'City not found or API error'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast', methods=['GET'])
async def get_forecast():
    city = request.args.get('city', 'London')
    
    # Return dummy data for CI/testing if no API key is set
    if API_KEY == 'your_api_key_here':
        return jsonify([
            {
                'time': '12:00',
                'temperature': 15.0,
                'description': 'Cloudy',
                'icon': '03d'
            },
            {
                'time': '15:00',
                'temperature': 16.0,
                'description': 'Sunny',
                'icon': '01d'
            }
        ])
    
    try:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric',
            'cnt': 8  # Get 24 hours forecast (8 * 3 hours)
        }
        
        response = requests.get(FORECAST_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        forecast_list = []
        for item in data['list']:
            forecast_list.append({
                'time': datetime.fromtimestamp(item['dt']).strftime('%H:%M'),
                'temperature': round(item['main']['temp'], 1),
                'description': item['weather'][0]['description'].capitalize(),
                'icon': item['weather'][0]['icon']
            })
        
        return jsonify(forecast_list)
    
    except requests.exceptions.HTTPError as e:
        return jsonify({'error': 'City not found or API error'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9898, debug=True)