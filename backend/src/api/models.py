from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class WeatherCondition(BaseModel):
    """A single weather condition descriptor."""

    main: str = Field(..., description="Group of weather parameters (Rain, Snow, etc.).")
    description: str = Field(..., description="Condition description (human-readable).")
    icon: str = Field(..., description="OpenWeatherMap icon code (e.g., 10d).")


class CurrentWeather(BaseModel):
    """Current weather conditions for a city."""

    city: str = Field(..., description="City name.")
    country: str = Field(..., description="Country code.")
    timestamp_utc: datetime = Field(..., description="Observation timestamp in UTC.")
    temp_c: float = Field(..., description="Temperature in Celsius.")
    feels_like_c: float = Field(..., description="Feels-like temperature in Celsius.")
    humidity: int = Field(..., description="Humidity percentage.")
    wind_mps: float = Field(..., description="Wind speed in meters/sec.")
    conditions: List[WeatherCondition] = Field(..., description="Weather conditions list.")
    icon_url: str = Field(..., description="Convenience URL for the primary icon.")


class ForecastItem(BaseModel):
    """A single forecast data point (3-hour step from OpenWeatherMap forecast API)."""

    timestamp_utc: datetime = Field(..., description="Forecast time in UTC.")
    temp_c: float = Field(..., description="Temperature in Celsius.")
    conditions: List[WeatherCondition] = Field(..., description="Weather conditions list.")
    icon_url: str = Field(..., description="Convenience URL for the primary icon.")


class ForecastResponse(BaseModel):
    """5-day forecast response for a city."""

    city: str = Field(..., description="City name.")
    country: str = Field(..., description="Country code.")
    items: List[ForecastItem] = Field(..., description="Forecast items (3-hour increments).")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message.")
