import asyncio

from app.services.cache_service import cache_get
from app.services.weather.weather_builders import DEFAULT_CITIES, create_weather_model

from app.services.weather.weather_fetchers import fetch_all
from app.dto.weather.weather_coords_cache_schema import WeatherCoordsCacheSchema
from app.utils.logger_helper import handle_log


async def fetch_weather_updates_async():
    handle_log(
        "Scheduled task started.",
        log_level="info",
        event_key="REFRESH_CITIES",
        service_method="fetch_weather_updates",
    )

    try:
        raw = cache_get("weather_coords_list")
        coords = (
            WeatherCoordsCacheSchema().load(raw)["coords"] if raw else DEFAULT_CITIES
        )

        fresh_data = await fetch_all(coords)
        fresh_models = create_weather_model(fresh_data)

        handle_log(
            "Fetched weather updates",
            log_level="info",
            event_key="SUCCESS",
            service_method="fetch_weather_updates",
            cities=[m.name for m in fresh_models],
        )

    except Exception as e:
        handle_log(
            f"Error fetching weather updates: {str(e)}",
            log_level="error",
            event_key="ERROR",
            service_method="fetch_weather_updates",
        )


def fetch_weather_updates():
    asyncio.run(fetch_weather_updates_async())
