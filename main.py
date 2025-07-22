# /// script
# dependencies = [
#   "fastmcp",
# ]
# ///

from fastmcp import FastMCP
from fastmcp.tools.tool import Tool, ToolResult
from fastmcp.tools.tool_transform import forward

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

async def custom_output(**kwargs) -> ToolResult:
    result = await forward(**kwargs)
    return ToolResult(structured_content={"Foo": "Bar", "original": result.content})  # Custom output structure

async def main():
    """Setup the proxy and configure tools"""
    
    original_tool = (await proxy.get_tool("repo_get_repo_by_name_or_id")).copy()
    
    # Create a local copy that you can modify
    modified_tool = Tool.from_tool(original_tool, transform_fn=custom_output)

    # Add the local copy to your server
    proxy.add_tool(modified_tool)
    
    # Now you can disable YOUR copy
    
    original_tool.disable()  # Disable the mirrored tool in the proxy

    await proxy.run_async()

# Run the server with stdio transport for local access
if __name__ == "__main__":

    import asyncio
    asyncio.run(main())  # Setup the proxy and tools
