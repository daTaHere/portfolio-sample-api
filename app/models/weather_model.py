"""This module defines the WeatherModel class for handling weather data."""

from typing import Any, Dict, List


class WeatherModel:
    """
    This class defines the internal WeatherModel data model.
    """

    __slots__ = (
        "_id",
        "name",
        "country",
        "coord",
        "dt",
        "temperature",
        "weather",
        "conditions",
    )

    def __init__(self, weather_data: Dict[str, Any]):
        self._id: int = weather_data.get("id")
        self.name: str = weather_data.get("name")
        self.country: str = weather_data.get("sys", {}).get("country")
        self.coord: Dict[str, float] = weather_data.get("coord")
        self.dt: int = weather_data.get("dt")
        self.temperature: Dict[str, float] = {
            "current": weather_data.get("main", {}).get("temp"),
            "temp_high": weather_data.get("main", {}).get("temp_max"),
            "temp_low": weather_data.get("main", {}).get("temp_min"),
        }
        self.weather: List[Dict[str, Any]] = weather_data.get("weather")
        self.conditions: Dict[str, Any] = {
            "wind": weather_data.get("wind", None),
            "visibility": weather_data.get("visibility", None),
            "clouds": weather_data.get("clouds", None),
            "extra_details": {
                "pressure": weather_data.get("main", {}).get("pressure", None),
                "humidity": weather_data.get("main", {}).get("humidity", None),
                "feels_like": weather_data.get("main", {}).get("feels_like", None),
                "sunrise": weather_data.get("sys", {}).get("sunrise", None),
                "sunset": weather_data.get("sys", {}).get("sunset", None),
            },
        }

    # id property read-only
    @property
    def id(self) -> int:
        return self._id

    def to_dict(self) -> Dict[str, Any]:
        """Convert WeatherModel instance to dictionary."""
        return {
            "id": self._id,
            "name": self.name,
            "country": self.country,
            "coord": self.coord,
            "dt": self.dt,
            "temperature": self.temperature,
            "weather": self.weather,
            "conditions": self.conditions,
        }
