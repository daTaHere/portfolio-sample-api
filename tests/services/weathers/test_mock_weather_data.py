from typing import Any, Dict, List, Tuple


DEFAULT_WEATHER_CITIES = [
    (34.05, -118.24),  # LA
    (40.71, -74.00),  # NYC
    (41.87, -87.62),  # Chicago
    (29.76, -95.36),  # Houston
    (25.76, -80.19),  # Miami
    (51.51, -0.13),  # London
    (35.68, 139.69),  # Tokyo
    (39.90, 116.40),  # Beijing
    (30.03, 31.23),  # Cairo
    (-33.86, 151.21),  # Sydney
]


def mock_weather_input_test_data(city_name: str) -> Dict[str, Any]:
    """
    Returns a template mocking the OpenWeatherMap API response structure
        args:
            city_name (str): Name of the city to include in the mock data
        returns:
            dict: Mocked weather data for the specified city
    """
    return {
        "base": "stations",
        "clouds": {"all": 0},
        "cod": 200,
        "coord": {"lat": 34.05, "lon": -118.24},
        "dt": 1767903197,
        "id": 5368361,
        "main": {
            "feels_like": 288.58,
            "grnd_level": 997,
            "humidity": 39,
            "pressure": 1016,
            "sea_level": 1016,
            "temp": 289.81,
            "temp_max": 291.15,
            "temp_min": 287.9,
        },
        "name": city_name,
        "sys": {
            "country": "US",
            "id": 2075946,
            "sunrise": 1767884344,
            "sunset": 1767920397,
            "type": 2,
        },
        "timezone": -28800,
        "visibility": 10000,
        "weather": [
            {"description": "clear sky", "icon": "01d", "id": 800, "main": "Clear"}
        ],
        "wind": {"deg": 280, "gust": 2.28, "speed": 4.12},
    }


def mock_weather_expected_data(
    city_name: str, lat: float = 34.05, lon: float = -118.24
) -> Dict[str, Any]:
    """
    Returns a object mocking expected processed weather data structure
        args:
            city_name (str): Name of the city to include in the mock data
            lat (float): Latitude of the city
            lon (float): Longitude of the city
        returns:
            dict: Mocked processed weather data for the specified city
    """
    return {
        "conditions": {
            "clouds": {"all": 0},
            "extra_details": {
                "feels_like": 288.58,
                "humidity": 39,
                "pressure": 1016,
                "sunrise": 1767884344,
                "sunset": 1767920397,
            },
            "visibility": 10000,
            "wind": {"deg": 280, "gust": 2.28, "speed": 4.12},
        },
        "coord": {"lat": lat, "lon": lon},
        "country": "US",
        "dt": 1767903197,
        "id": 5368361,
        "name": city_name,
        "temperature": {"current": 289.81, "temp_high": 291.15, "temp_low": 287.9},
        "weather": [
            {"description": "clear sky", "icon": "01d", "id": 800, "main": "Clear"}
        ],
    }
