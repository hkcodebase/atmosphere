import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import subprocess
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    # methods will go here

    async def call_gemma4(self, prompt: str) -> str:
        result = await asyncio.to_thread(subprocess.run, ['docker', 'model', 'run', 'ai/gemma4', prompt], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Docker model error: {result.stderr}")
        return result.stdout.strip()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Gemma4 and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Build initial prompt with clear instructions about tool call format
        prompt = f"User: {query}\n"
        if available_tools:
            tools_desc = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
            prompt += f"Available tools:\n{tools_desc}\n"
            prompt += """IMPORTANT: When you need to call a tool, output ONLY this format on a new line:
Tool Call: tool_name(param1="value1", param2="value2")

For location queries: First use get_location to get coordinates, then use get_forecast.
Example: If user asks for temperature in NYC:
1. Tool Call: get_location(location="New York City")
2. Wait for result
3. Tool Call: get_forecast(latitude="<result>", longitude="<result>")
4. Provide the answer

Never output empty content or arrays. Always respond with either text or a tool call."""
        prompt += "\nAssistant:"

        max_iterations = 15  # Prevent infinite loops
        for iteration in range(max_iterations):
            # Call Gemma4
            response_text = await self.call_gemma4(prompt)

            # Handle empty responses
            if not response_text or response_text == "[]" or response_text.strip() == "":
                return "No response from model. Please try again."

            # Check for tool calls in the response
            tool_call_pattern_old = r'<\|tool_call\|>call:\s*(\w+)\{([^}]*)\}<\|tool_call\|>'
            tool_call_pattern_new = r'\*\*Tool Call\*\*:\s*(\w+)\(([^)]*)\)'
            tool_call_pattern_simple = r'Tool Call:\s*(\w+)\(([^)]*)\)'
            match = re.search(tool_call_pattern_old, response_text)
            if not match:
                match = re.search(tool_call_pattern_new, response_text)
            if not match:
                match = re.search(tool_call_pattern_simple, response_text)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2).strip()
                try:
                    # Parse args
                    args = {}
                    if args_str:
                        if '{' in args_str:  # Old format {key: "value"}
                            # Simple parsing: split by comma, then key: value
                            pairs = [p.strip() for p in args_str.split(',')]
                            for pair in pairs:
                                if ':' in pair:
                                    key, val = pair.split(':', 1)
                                    key = key.strip()
                                    val = val.strip().strip('"')
                                    args[key] = val
                        else:  # New format key="value"
                            pairs = [p.strip() for p in args_str.split(',')]
                            for pair in pairs:
                                if '=' in pair:
                                    key, val = pair.split('=', 1)
                                    key = key.strip()
                                    val = val.strip().strip('"')
                                    args[key] = val
                    # Call the tool
                    result = await self.session.call_tool(tool_name, args)
                    tool_result = result.content[0].text if result.content else "No result"

                    # Append to messages
                    messages.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Tool result for {tool_name}: {tool_result}"
                    })

                    # Build new prompt with tool result
                    prompt = ""
                    for msg in messages:
                        role = msg['role']
                        content = msg['content']
                        prompt += f"{role.capitalize()}: {content}\n"
                    prompt += "Continue answering the user's query. If you need more tools, use: Tool Call: tool_name(param=\"value\")\nAssistant:"
                except Exception as e:
                    return f"Error calling tool {tool_name}: {str(e)}"
            else:
                return response_text
        return "Max iterations reached, stopping."

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run client.py weather.py")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())