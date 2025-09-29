"""
Weather Intelligence MCP Server for Google Cloud Run

This MCP server provides weather tools, resources, and prompts using OpenWeatherMap API.
Based on Google Cloud's official MCP server pattern.
"""

import asyncio
import logging
import os
import requests
from typing import List, Dict, Optional

from fastmcp import FastMCP
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Weather Intelligence MCP Server")

# --- Pydantic Models for Data Structuring ---

class CurrentWeather(BaseModel):
    location: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    pressure: int

class ForecastItem(BaseModel):
    date: str
    temperature: float
    description: str

class WeatherForecast(BaseModel):
    location: str
    forecast: List[ForecastItem]

# --- MCP Server Configuration ---

WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
if not WEATHER_API_KEY:
    logger.warning("⚠️  WARNING: OPENWEATHERMAP_API_KEY environment variable not set!")
    logger.warning("   The weather tools will not work without an API key.")
    logger.warning("   Get one from: https://openweathermap.org/api")

WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"

# --- Refactored MCP Tools ---

@mcp.tool()
def get_current_weather(location: str) -> str:
    """
    Get current weather for a specific location and return it as a formatted string.
    
    Args:
        location: City name or location (e.g., "London", "New York", "Tokyo")
        
    Returns:
        Formatted string with current weather information or an error message.
    """
    logger.info(f">>> 🛠️ Tool: 'get_current_weather' called for location '{location}'")
    
    try:
        url = f"{WEATHER_BASE_URL}/weather"
        params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        weather = CurrentWeather(
            location=location,
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"].title(),
            wind_speed=data["wind"]["speed"],
            pressure=data["main"]["pressure"]
        )

        logger.info(f"Weather data retrieved for {location}: {weather.temperature}°C")

        return f"""Current weather in {weather.location}:
- Temperature: {weather.temperature}°C (feels like {weather.feels_like}°C)
- Condition: {weather.description}
- Humidity: {weather.humidity}%
- Wind Speed: {weather.wind_speed} m/s
- Pressure: {weather.pressure} hPa"""

    except Exception as e:
        logger.error(f"Failed to get weather for {location}: {str(e)}")
        return f"Error: Failed to get weather for {location}: {str(e)}"

@mcp.tool()
def get_weather_forecast(location: str, days: int = 3) -> str:
    """
    Get weather forecast for a specific location and return it as a formatted string.
    
    Args:
        location: City name or location
        days: Number of days to forecast (max 5)
        
    Returns:
        Formatted string with forecast information or an error message.
    """
    logger.info(f">>> 🛠️ Tool: 'get_weather_forecast' called for location '{location}' and {days} days")
    
    try:
        url = f"{WEATHER_BASE_URL}/forecast"
        params = {"q": location, "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        daily_forecasts = []
        processed_dates = set()
        for item in data["list"]:
            date = item["dt_txt"].split()[0]
            if date not in processed_dates and len(daily_forecasts) < days:
                daily_forecasts.append(ForecastItem(
                    date=date,
                    temperature=item["main"]["temp"],
                    description=item["weather"][0]["description"].title()
                ))
                processed_dates.add(date)

        weather_forecast = WeatherForecast(location=location, forecast=daily_forecasts)

        result_str = f"{len(weather_forecast.forecast)}-day weather forecast for {weather_forecast.location}:\n"
        for day in weather_forecast.forecast:
            result_str += f"- {day.date}: {day.temperature}°C, {day.description}\n"
        
        logger.info(f"Forecast data retrieved for {location}: {len(daily_forecasts)} days")
        return result_str

    except Exception as e:
        logger.error(f"Failed to get forecast for {location}: {str(e)}")
        return f"Error: Failed to get forecast for {location}: {str(e)}"

if __name__ == "__main__":
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
