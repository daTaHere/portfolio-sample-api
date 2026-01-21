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
        """Initialize WeatherModel instance from raw weather data dictionary."""
        main = weather_data["main"]
        sys = weather_data["sys"]

        self._id: int = weather_data["id"]
        self.name: str = weather_data["name"]
        self.country: str = sys["country"]
        self.coord: Dict[str, float] = weather_data["coord"]
        self.dt: int = weather_data.get("dt")
        self.temperature: Dict[str, float] = {
            "current": main["temp"],
            "temp_high": main["temp_max"],
            "temp_low": main["temp_min"],
        }
        self.weather: List[Dict[str, Any]] = weather_data["weather"]
        self.conditions: Dict[str, Any] = {
            "wind": weather_data.get("wind"),
            "visibility": weather_data.get("visibility"),
            "clouds": weather_data.get("clouds"),
            "extra_details": {
                "pressure": main.get("pressure"),
                "humidity": main.get("humidity"),
                "feels_like": main.get("feels_like"),
                "sunrise": sys.get("sunrise"),
                "sunset": sys.get("sunset"),
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
