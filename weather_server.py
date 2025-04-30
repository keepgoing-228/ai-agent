import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Initialize MCP server
mcp = FastMCP("weather_server")

WEATHER_API_URL = os.getenv("WEATHER_API_URL")
API_KEY = os.getenv("WEATHER_API_KEY")
USER_AGENT = os.getenv("WEATHER_USER_AGENT")


async def get_weather(city: str) -> dict[str, Any]:
    """Get the weather in a given city"""
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    headers = {"User-Agent": USER_AGENT}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                WEATHER_API_URL, params=params, headers=headers, timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error occurred: {e}")
        except Exception as e:
            raise Exception(f"An error occurred: {e}")


def format_weather(data: dict[str, Any]) -> str:
    """Format the weather data into a string"""
    if isinstance(data, dict):
        try:
            return f"Weather in {data['name']}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
            # return json.dumps(data)
        except Exception as e:
            return f"Error formatting weather data: {e}"

    return str(data)


@mcp.tool()
async def query_weather(city: str) -> str:
    """Query the weather in a given city"""
    data = await get_weather(city)
    return format_weather(data)


if __name__ == "__main__":

    # test the query_weather function
    import asyncio

    async def test():
        result = await query_weather("Taipei")
        print(f"Test result: {result}")

    asyncio.run(test())

    # mcp.run(transport="stdio")
