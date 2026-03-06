from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status

from src.api.cache import TTLCache
from src.api.models import (
    CurrentWeather,
    ForecastItem,
    ForecastResponse,
    WeatherCondition,
)
from src.api.settings import Settings

_OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
_ICON_BASE_URL = "https://openweathermap.org/img/wn"


def _icon_url(icon_code: str) -> str:
    return f"{_ICON_BASE_URL}/{icon_code}@2x.png"


def _dt_utc_from_epoch_seconds(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


class OpenWeatherClient:
    """Client for OpenWeatherMap Current Weather and 5-day Forecast APIs."""

    def __init__(self, settings: Settings, cache: TTLCache) -> None:
        self._settings = settings
        self._cache = cache

    async def get_current_weather(self, city: str) -> CurrentWeather:
        cache_key = f"current::{city.strip().lower()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        params = {
            "q": city,
            "appid": self._settings.openweather_api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{_OPENWEATHER_BASE_URL}/weather", params=params)
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Upstream request failed: {exc.__class__.__name__}",
                ) from exc

        if resp.status_code != 200:
            # OpenWeather returns helpful JSON but we keep error shape simple for the app.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND
                if resp.status_code in (401, 404)
                else status.HTTP_502_BAD_GATEWAY,
                detail="Unable to fetch current weather for that city.",
            )

        data: dict[str, Any] = resp.json()
        conditions = [
            WeatherCondition(
                main=w.get("main", ""),
                description=w.get("description", ""),
                icon=w.get("icon", ""),
            )
            for w in (data.get("weather") or [])
        ]
        icon_code = conditions[0].icon if conditions else ""
        model = CurrentWeather(
            city=data.get("name") or city,
            country=(data.get("sys") or {}).get("country") or "",
            timestamp_utc=_dt_utc_from_epoch_seconds(int(data.get("dt") or 0)),
            temp_c=float((data.get("main") or {}).get("temp") or 0.0),
            feels_like_c=float((data.get("main") or {}).get("feels_like") or 0.0),
            humidity=int((data.get("main") or {}).get("humidity") or 0),
            wind_mps=float((data.get("wind") or {}).get("speed") or 0.0),
            conditions=conditions,
            icon_url=_icon_url(icon_code) if icon_code else "",
        )

        self._cache.set(cache_key, model, self._settings.weather_cache_ttl_seconds)
        return model

    async def get_forecast(self, city: str) -> ForecastResponse:
        cache_key = f"forecast::{city.strip().lower()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        params = {
            "q": city,
            "appid": self._settings.openweather_api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    f"{_OPENWEATHER_BASE_URL}/forecast", params=params
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Upstream request failed: {exc.__class__.__name__}",
                ) from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND
                if resp.status_code in (401, 404)
                else status.HTTP_502_BAD_GATEWAY,
                detail="Unable to fetch forecast for that city.",
            )

        data: dict[str, Any] = resp.json()
        city_info = data.get("city") or {}
        items: list[ForecastItem] = []
        for item in data.get("list") or []:
            conditions = [
                WeatherCondition(
                    main=w.get("main", ""),
                    description=w.get("description", ""),
                    icon=w.get("icon", ""),
                )
                for w in (item.get("weather") or [])
            ]
            icon_code = conditions[0].icon if conditions else ""
            items.append(
                ForecastItem(
                    timestamp_utc=_dt_utc_from_epoch_seconds(int(item.get("dt") or 0)),
                    temp_c=float((item.get("main") or {}).get("temp") or 0.0),
                    conditions=conditions,
                    icon_url=_icon_url(icon_code) if icon_code else "",
                )
            )

        model = ForecastResponse(
            city=city_info.get("name") or city,
            country=city_info.get("country") or "",
            items=items,
        )
        self._cache.set(cache_key, model, self._settings.weather_cache_ttl_seconds)
        return model
