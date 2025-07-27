# /// script
# dependencies = [
#   "fastmcp",
#   "jq"
# ]
# ///

from typing import Literal
from fastmcp import FastMCP
from fastmcp.tools.tool import Tool, ToolResult
from fastmcp.tools.tool_transform import forward
from mcp.types import TextContent
import asyncio
import json
import jq
import argparse


# Create a proxy directly from a config dictionary
config = {
    "mcpServers": {
        "default": {  # For single server configs, 'default' is commonly used
            "command": "npx",
            "args": ["-y", "@azure-devops/mcp", "msazure"],    
            "timeout": 30000
        }
    }
}

# Create a proxy to the configured server (auto-creates ProxyClient)
proxy = FastMCP.as_proxy(config, name="ADO MCP Proxy")

# Tool transformations configuration
TOOL_TRANSFORMATIONS = {
    "repo_get_repo_by_name_or_id": '{"id", "name", "defaultBranch", "remoteUrl"}',
    "repo_get_pull_request_by_id": 'walk(if type == "object" then with_entries(select(.key | test("^(_links|.*[Uu]rl|href)$") | not)) else . end)',
    "*": 'walk(if type == "object" then with_entries(select(.key | IN("_links", "url", "href") | not)) else . end)',
}

# Pre-compile jq filters for performance
COMPILED_TRANSFORMATIONS = {
    tool_name: jq.compile(jq_string) 
    for tool_name, jq_string in TOOL_TRANSFORMATIONS.items()
}

def create_custom_output(jq_command):
    """Higher-order function that takes a jq_command and returns the transformation function"""
    async def custom_output(**kwargs) -> ToolResult:
        result = await forward(**kwargs)
        if (
            len(result.content) == 1
            and isinstance(result.content[0], TextContent)
        ):
            try:
                parsed = json.loads(result.content[0].text)
                filtered = jq_command.input_value(parsed).first()

                if filtered is not None and not isinstance(filtered, dict):
                    filtered = {"result": filtered}
                
                return ToolResult(structured_content=filtered)
            except Exception:
                pass
        return result
    return custom_output

async def main(transport: Literal["stdio", "sse"] = "stdio"):
    """Setup the proxy and configure tools"""
    
    # Get all available tools from proxy
    available_tools = await proxy.get_tools()

    for tool_name, tool in available_tools.items():
        compiled_jq = COMPILED_TRANSFORMATIONS.get(tool_name) or COMPILED_TRANSFORMATIONS.get("*")

        copied_tool = tool.copy()  # Copy original tool to modify
            
        # Create transformation function for this tool
        custom_output = create_custom_output(compiled_jq)
        
        # Create modified tool with transformation
        modified_tool = Tool.from_tool(copied_tool, transform_fn=custom_output)
        
        # Add modified tool and disable original
        proxy.add_tool(modified_tool)
        copied_tool.disable()

    await proxy.run_async(transport=transport)

# Run the server with stdio transport for local access
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Azure DevOps MCP Transform Proxy Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    
    args = parser.parse_args()

    asyncio.run(main(args.transport))  # Setup the proxy and tools
