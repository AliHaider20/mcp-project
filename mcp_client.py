from google import genai
from google.genai import types
from os import getenv
from typing import List


from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.available_tools: List[dict] = []

    def _build_generation_config(self) -> types.GenerateContentConfig:
        gemini_tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters_json_schema=tool["input_schema"],
                    )
                ]
            )
            for tool in self.available_tools
        ]
        return types.GenerateContentConfig(
            tools=gemini_tools,
            temperature=0.0,
            system_instruction=(
                "You are a helpful financial assistant. "
                "Always keep your answers concise and professional."
            ),
        )

    async def _chat_loop(
        self,
        session: ClientSession,
        client: genai.Client,
        config: types.GenerateContentConfig,
    ) -> None:
        while True:
            user_input = input("User:")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat.")
                break

            contents = [user_input]
            while True:
                response = await client.aio.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=contents,
                    config=config,
                )
                function_calls = response.function_calls or []
                if not function_calls:
                    print(response.text or "The model returned no text.")
                    break

                contents.append(response.candidates[0].content)
                function_responses = []
                for function_call in function_calls:
                    tool_result = await session.call_tool(
                        function_call.name,
                        arguments=function_call.args,
                    )
                    result = tool_result.structured_content
                    if result is None:
                        result = [
                            getattr(item, "text", str(item))
                            for item in tool_result.content
                        ]
                    function_responses.append(
                        types.Part.from_function_response(
                            name=function_call.name,
                            response={
                                "result": result,
                                "is_error": tool_result.is_error,
                            },
                        )
                    )
                contents.append(
                    types.Content(role="user", parts=function_responses)
                )

    async def chat(self):
        server_params = StdioServerParameters(
            command = "python",
            args=['mcp_server.py'],
            env=None
        )

        client = genai.Client(api_key=getenv("GOOGLE_AI_STUDIO_API_KEY"))
        print("Starting chat. Type 'exit' or 'quit' to end the chat.")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                print("Connected to server with tools:", [tool.name for tool in response.tools])

                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema
                    } for tool in response.tools
                ]

                config = self._build_generation_config()
                await self._chat_loop(session, client, config)



if __name__ == "__main__":
    import asyncio
    mcp_client = MCPClient()
    asyncio.run(mcp_client.chat())

    # schema = asyncio.run(read_schema())