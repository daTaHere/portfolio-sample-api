import asyncio

from app.services.cache_service import cache_set, cache_get
from app.routes.weather_routes import DEFAULT_CITIES, fetch_with_index, batches
from app.utils.logger_helper import debug_logger


_logger = debug_logger("weather_tasks")


def process_refresh_data(lat: float, lon: float, data: dict):
    cache_key = f"{lat},{lon}"
    fresh_weather_data = data
    city_name = fresh_weather_data.get("name")
    cache_set(cache_key, fresh_weather_data, ttl=300)  # store weather
    cache_set(str(city_name).lower(), (lat, lon), ttl=300)


def fetch_weather_updates():
    """Wrapper to run async batch in scheduler"""
    cache_loc_list = cache_get("weather_coords_list") or DEFAULT_CITIES

    async def _runner():
        for batch in batches(cache_loc_list, 5):
            tasks = [fetch_with_index(0, lat, lon) for lat, lon in batch]
            coords = await asyncio.gather(*tasks)

            for idx, lat, lon, data in coords:
                process_refresh_data(lat, lon, data)
        cache_set("weather_coords_list", cache_loc_list, ttl=600)

    asyncio.run(_runner())

    _logger.info("Weather cache refresh complete =======")

    data = cache_get("weather_coords_list")
    _logger.debug(f"Refreshed coords list: {data}  ============")
