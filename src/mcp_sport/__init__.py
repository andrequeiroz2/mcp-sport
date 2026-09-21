"""Package entrypoint for the mcp-sport console script."""


def main() -> None:
    """Start the F1 MCP server on stdio."""
    from mcp_sport.server import mcp

    mcp.run()
