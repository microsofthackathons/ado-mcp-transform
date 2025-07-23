# Azure DevOps MCP Transform

> **⚠️ Proof of Concept (POC)** - Created for the July 2025 AzNet ILDC AI Hackathon

A Model Context Protocol (MCP) proxy server that transforms Azure DevOps API responses by filtering out verbose metadata and URLs, providing cleaner, more focused data for AI applications.

## Overview

This project implements an MCP proxy that wraps the official Azure DevOps MCP server (`@azure-devops/mcp`) and applies jq-based transformations to tool responses. The proxy intercepts specific tool calls and filters out unnecessary fields like `_links`, URLs, dates, and other metadata that can clutter AI context windows. It additionally writes to the new `structuredContent` response field for more intelligent client handling.

## Architecture

### MCP Proxy Pattern
- **Upstream Server**: `@azure-devops/mcp` (npm package)
- **Proxy Layer**: FastMCP-based transformation server
- **Transform Engine**: Pre-compiled jq filters for performance
- **Transport**: stdio/SSE protocols

### Transformation Pipeline
1. Client calls transformed tool
2. Proxy forwards request to upstream Azure DevOps MCP server
3. Response intercepted and processed through jq filter
4. Cleaned response returned to client

## Deployment Models

### Single-File Execution (Production)
The `main.py` file uses script dependencies and can be executed directly:

```bash
# Run with default stdio transport
uv run main.py

# Run with specific transport
uv run main.py --transport sse
```

### Development Setup (This Repository)
For development, testing, and modification:

```bash
# Clone and setup development environment
git clone https://github.com/microsofthackathons/ado-mcp-transform.git
cd ado-mcp-transform

# Install dependencies
uv sync

# Run in development mode
python main.py

python main.py --transport sse
```

Use the SSE server launch settings provided by `launch.json` for debugging in VS Code.

## Current Transformations

The current transformations have been defined (other files remain unchanged:)

### `repo_get_repo_by_name_or_id`
**Filter**: `{"id", "name", "defaultBranch", "remoteUrl"}`

### `repo_get_pull_request_by_id`
**Filter**: Removes `_links`, URLs, and `href` fields recursively

### `repo_list_pull_request_threads`
**Filter**: Complex filter for thread cleanup
- Filters out deleted threads
- Removes properties, links, dates, descriptors
- Keeps only active discussion threads

## Development

### Adding New Transformations
1. Add jq filter to `TOOL_TRANSFORMATIONS` dictionary:
```python
TOOL_TRANSFORMATIONS["new_tool_name"] = 'your_jq_filter_here'
```

2. The transformation will be automatically applied if the tool exists in the upstream server.

### Testing jq Filters
Test filters independently:
```bash
echo '{"test": "data"}' | jq 'your_filter_here'
```

It is helpful to use an LLM and/or the jq playground for developing the expressions.

## Transport Support

- **stdio** (default) - Standard input/output for local MCP clients
- **sse** - Server-Sent Events for debugging

Transport can be configured via:
1. Command line flag: `--transport stdio` or `--transport sse`

## Future Work

- The architecture here is configuration-based, so it could theoretically be applied to any json-based LLM by passing in a path to an appropriate configuration file.
- Logging, etc is not present
- additional tools
- Filter out unneeded tools with the [new `tool_transformations` support](https://github.com/jlowin/fastmcp/pull/1132/)
