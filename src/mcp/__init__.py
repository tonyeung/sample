"""Model Context Protocol (MCP) integration for Multi-Agent System"""

from .protocol import (
    MCPServer,
    MCPToolRegistry,
    MCPContextProvider,
    Tool,
    ToolType,
    ToolParameter,
    ToolCall,
    ToolResult
)

__all__ = [
    'MCPServer',
    'MCPToolRegistry',
    'MCPContextProvider',
    'Tool',
    'ToolType',
    'ToolParameter',
    'ToolCall',
    'ToolResult'
]
