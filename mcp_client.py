import asyncio
import json
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mcp import ClientSession
from openai import OpenAI

load_dotenv()


class MCPClient:
    def __init__(self):
        # self.session = None
        self.exit_stack = AsyncExitStack() # used to manage the lifecycle of the session

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")

        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            base_url=self.base_url,
        )

    async def process_query(self, query: str, message: list) -> list:
        # call the openai api with streaming
        try:
            full_response = ""
            message.append({"role": "user", "content": query})

            print("Response: ", end="", flush=True)

            # Create a streaming response
            stream = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=message,
                    stream=True,  # Enable streaming
                )
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



    # async def connect_to_mock_server(self):
    #     print("Connecting to MCP...")

    async def chat_loop(self):
        message = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]

        print("mcp client chat loop started, type 'exit' to quit")
        while True:
            try:
                query = input("Query: ").strip()
                if query.lower() == "exit":
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
    client = MCPClient()
    try:
        # await client.connect_to_mock_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
