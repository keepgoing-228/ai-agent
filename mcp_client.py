import asyncio
import json
import os
import sys
import traceback
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

    async def process_query(self, query: str, messages: list) -> list:
        # call the openai api with streaming, and use the tools
        try:
            messages.append({"role": "user", "content": query})

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

            # use run_in_executor to run the synchronous method
            # TODO: Stream the response
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=self.llm_model,
                    messages=messages,
                    tools=available_tools,
                    tool_choice="auto",
                ),
            )

            # handle the response context
            content = response.choices[0]
            if content.finish_reason == "tool_calls":
                tool_call = content.message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments

                # parse the JSON string to a Python dictionary
                tool_args_dict = json.loads(tool_args_str)

                result = await self.session.call_tool(tool_name, tool_args_dict)
                print(f"Tool {tool_name} called with args {tool_args_str}")

                # append the tool call to the messages
                messages.append(content.message.model_dump())
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content[0].text,
                    }
                )

                # use run_in_executor to call the OpenAI API again
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model=self.llm_model,
                        messages=messages,
                    ),
                )

            # in all cases, append the assistant response to the messages
            messages.append(
                {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                }
            )

            return messages

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            return "An error occurred while processing the query."

    async def chat_loop(self):
        message = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

        print("mcp client chat loop started, type 'exit' or 'quit' to quit")
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "exit" or query.lower() == "quit":
                    break
                history = await self.process_query(query, message)
                # print(json.dumps(history, indent=2))
                print(history[-1]["content"])

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
