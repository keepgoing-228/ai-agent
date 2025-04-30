import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()


class MCPClient:
    def __init__(self):
        # used to manage the lifecycle of the session
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm_base_url = os.getenv("LLM_BASE_URL")
        self.llm_model = os.getenv("LLM_MODEL")

        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.llm_base_url,
        )

    async def connect_to_weather_server(self, server_script_path: str):
        """Connect to the weather server"""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("server_script_path must end with .py or .js")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        # Start MCP server and create the stdio transport
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        # Create the client session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()

        # List MCP server's tools
        response = await self.session.list_tools()
        tools = response.tools
        print(f"Supported tools:")
        for tool in tools:
            print(f"  {tool.name}: {tool.description}")

    async def process_query(self, query: str, message: list) -> list:
        # call the openai api with streaming, and use the tools
        try:
            full_response = ""
            message.append({"role": "user", "content": query})

            response = await self.session.list_tools()

            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    },
                }
                for tool in response.tools
            ]

            print("Response: ", end="", flush=True)

            # Create a streaming response
            stream = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=self.llm_model,
                    messages=message,
                    tools=available_tools,
                    tool_choice="auto",
                    stream=True,  # Enable streaming
                ),
            )

            # Process the stream chunks
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            print()  # Add a newline at the end

            # append the full response to the message
            message.append({"role": "assistant", "content": full_response})
            return message

        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while processing the query."

    async def chat_loop(self):
        message = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

        print("mcp client chat loop started, type 'exit' to quit")
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "exit" or query.lower() == "quit":
                    break
                await self.process_query(query, message)
                # history = await self.process_query(query, message)
                # history = json.dumps(history, indent=2)
                # print(history)

            except Exception as e:
                print(f"Error: {e}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) != 2:
        print("Usage: python mcp_client.py <server_script_path>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_weather_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
