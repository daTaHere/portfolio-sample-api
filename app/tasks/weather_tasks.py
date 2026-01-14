import asyncio

from app.services.cache_service import cache_get
from app.services.weather.weather_builders import DEFAULT_CITIES, create_weather_model

from app.services.weather.weather_fetchers import fetch_all
from app.dto.weather.weather_coords_cache_schema import WeatherCoordsCacheSchema
from app.utils.logger_helper import debug_logger


_logger = debug_logger("weather_tasks")


def fetch_weather_updates():
    raw = cache_get("weather_coords_list")

    if raw:
        # raw is already a Python dict (json.loads ran)
        coords = WeatherCoordsCacheSchema().load(raw)["coords"]
    else:
        coords = DEFAULT_CITIES

    async def _runner():
        fresh_data = await fetch_all(coords)
        fresh_models = create_weather_model(fresh_data)

        _logger.debug(
            "Fetched weather updates",
            extra={
                "service_method": "fetch_weather_updates",
                "cities": [m.name for m in fresh_models],
            },
        )

    asyncio.run(_runner())
