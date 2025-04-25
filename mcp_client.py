import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession


class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack() # used to manage the lifecycle of the session

    async def connect_to_mock_server(self):
        print("Connecting to MCP...")

    async def chat_loop(self):
        print("mcp client chat loop started, type 'exit' to quit")

        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "exit":
                    break
                print(f"MCP: {query}")
            except Exception as e:
                print(f"Error: {e}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient()
    try:
        await client.connect_to_mock_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
