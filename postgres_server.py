from typing import Any

import psycopg
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("postgres_server")


@mcp.tool()
def motherboard_brief(model: str) -> str:
    """
    Query motherboard's brief features.
    Args:
      model (str): motherboard name
    Returns:
        str: A string containing motherboard brief.
    """
    try:
        conn = psycopg.connect(
            conninfo="postgres://asrock:asrock@localhost:5432/mb_product"
        )
        cur = conn.cursor()
        model = model.lower()
        model = model.replace("asrock", "").strip()

        # Use parameterized query to prevent SQL injection -> tuple must be used in execute
        query = "SELECT brief FROM en WHERE model ILIKE %s"
        cur.execute(query, (f"{model}",))  # tuple

        result: tuple = cur.fetchone()  # type: ignore

        cur.close()
        conn.close()

        if result and result[0]:
            return result[0]
        return "Not Found"

    except Exception as e:
        print(f"Error querying database: {e}")
        return "Error occurred while retrieving motherboard brief"


if __name__ == "__main__":
    # # Test the motherboard_brief function
    # test_model = "B650E PG Riptide WiFi"
    # result = motherboard_brief(test_model)
    # print(f"Test result: {result}")

    mcp.run(transport="stdio")
