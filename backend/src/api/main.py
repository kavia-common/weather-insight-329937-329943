from __future__ import annotations

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.cache import TTLCache
from src.api.models import CurrentWeather, ErrorResponse, ForecastResponse
from src.api.openweather import OpenWeatherClient
from src.api.settings import Settings, get_settings

openapi_tags = [
    {"name": "Health", "description": "Service health and status endpoints."},
    {"name": "Weather", "description": "Weather and forecast endpoints (OpenWeatherMap)."},
]

app = FastAPI(
    title="Weather Insight Backend API",
    description=(
        "Backend API for the Weather Insight Flutter app.\n\n"
        "Uses OpenWeatherMap upstream APIs to provide:\n"
        "- Current weather by city\n"
        "- 5-day forecast by city\n\n"
        "Set `OPENWEATHER_API_KEY` in the environment to enable weather endpoints."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mobile clients typically do not require strict CORS.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = TTLCache()


def _get_weather_client(settings: Settings = Depends(get_settings)) -> OpenWeatherClient:
    return OpenWeatherClient(settings=settings, cache=_cache)


@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Simple health check to verify the backend service is running.",
)
# PUBLIC_INTERFACE
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict[str, str]: Basic status payload.
    """
    return {"message": "Healthy"}


@app.get(
    "/weather/current",
    response_model=CurrentWeather,
    tags=["Weather"],
    summary="Get current weather by city",
    description=(
        "Fetches current weather conditions for a given city.\n\n"
        "Example: `/weather/current?city=London`"
    ),
    responses={
        404: {"model": ErrorResponse, "description": "City not found (or invalid API key)."},
        502: {"model": ErrorResponse, "description": "Upstream weather service failure."},
    },
    operation_id="get_current_weather",
)
# PUBLIC_INTERFACE
async def get_current_weather(
    city: str = Query(..., min_length=1, max_length=100, description="City name to look up."),
    client: OpenWeatherClient = Depends(_get_weather_client),
) -> CurrentWeather:
    """Return current weather for a city.

    Args:
        city: City name (e.g., 'London').
        client: Injected OpenWeather client.

    Returns:
        CurrentWeather: normalized weather response.
    """
    return await client.get_current_weather(city=city)


@app.get(
    "/weather/forecast",
    response_model=ForecastResponse,
    tags=["Weather"],
    summary="Get 5-day forecast by city",
    description=(
        "Fetches 5-day / 3-hour forecast for a given city.\n\n"
        "Example: `/weather/forecast?city=London`"
    ),
    responses={
        404: {"model": ErrorResponse, "description": "City not found (or invalid API key)."},
        502: {"model": ErrorResponse, "description": "Upstream weather service failure."},
    },
    operation_id="get_forecast",
)
# PUBLIC_INTERFACE
async def get_forecast(
    city: str = Query(..., min_length=1, max_length=100, description="City name to look up."),
    client: OpenWeatherClient = Depends(_get_weather_client),
) -> ForecastResponse:
    """Return 5-day forecast for a city.

    Args:
        city: City name (e.g., 'London').
        client: Injected OpenWeather client.

    Returns:
        ForecastResponse: normalized forecast response.
    """
    return await client.get_forecast(city=city)
