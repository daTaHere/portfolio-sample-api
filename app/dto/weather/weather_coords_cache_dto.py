from typing import List, Tuple


class WeatherCoords:
    __slots__ = ("lat", "lon")

    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon


class WeatherCoordCacheDTO:
    __slots__ = ("coords", "data")

    def __init__(self, data: List[WeatherCoords], coords: str = "coords"):
        self.coords = coords
        self.data = data
