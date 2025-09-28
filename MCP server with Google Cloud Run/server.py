"""
Weather Intelligence MCP Server for Google Cloud Run

This MCP server provides weather tools, resources, and prompts using OpenWeatherMap API.
Based on Google Cloud's official MCP server pattern.
"""

import asyncio
import logging
import os
import json
import requests
from typing import List, Dict

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Weather Intelligence MCP Server")

# Configuration
WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
if not WEATHER_API_KEY:
    logger.warning("⚠️  WARNING: OPENWEATHERMAP_API_KEY environment variable not set!")
    logger.warning("   The weather tools will not work without an API key.")
    logger.warning("   Get one from: https://openweathermap.org/api")

WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"

@mcp.tool()
def get_current_weather(location: str) -> dict:
    """
    Get current weather for a specific location using OpenWeatherMap API 2.5.
    
    Args:
        location: City name or location (e.g., "London", "New York", "Tokyo")
        
    Returns:
        Dictionary with current weather information
    """
    logger.info(f">>> 🛠️ Tool: 'get_current_weather' called for location '{location}'")
    
    # Use the internal helper function
    result = _get_weather_data(location)
    
    if "error" not in result:
        logger.info(f"Weather data retrieved for {location}: {result['temperature']}°C")
    
    return result

@mcp.tool()
def get_weather_forecast(location: str, days: int = 3) -> dict:
    """
    Get weather forecast for a specific location using OpenWeatherMap API 2.5.
    
    Args:
        location: City name or location
        days: Number of days to forecast (max 5)
        
    Returns:
        Dictionary with forecast information
    """
    logger.info(f">>> 🛠️ Tool: 'get_weather_forecast' called for location '{location}' and {days} days")
    
    try:
        url = f"{WEATHER_BASE_URL}/forecast"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Process forecast data
        daily_forecasts = []
        processed_dates = set()
        
        for item in data["list"]:
            date = item["dt_txt"].split()[0]
            if date not in processed_dates and len(daily_forecasts) < days:
                daily_forecasts.append({
                    "date": date,
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"]
                })
                processed_dates.add(date)
        
        result = {
            "location": location,
            "forecast": daily_forecasts
        }
        
        logger.info(f"Forecast data retrieved for {location}: {len(daily_forecasts)} days")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get forecast for {location}: {str(e)}")
        return {"error": f"Failed to get forecast for {location}: {str(e)}"}

def _get_weather_data(location: str) -> dict:
    """
    Internal helper function to get weather data (not exposed as MCP tool)
    """
    try:
        url = f"{WEATHER_BASE_URL}/weather"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        return {
            "location": location,
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"],
            "pressure": data["main"]["pressure"]
        }
        
    except Exception as e:
        return {"error": f"Failed to get weather for {location}: {str(e)}"}

if __name__ == "__main__":
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', 8080)}")
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )