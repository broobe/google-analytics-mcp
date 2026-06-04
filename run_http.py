#!/usr/bin/env python3
"""HTTP entry point for the GA4 MCP server supporting both SSE and Streamable HTTP."""

import asyncio
import os
import sys
import analytics_mcp.coordinator as coordinator
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.responses import JSONResponse
import uvicorn


API_KEY = os.environ.get("MCP_API_KEY", "")

sse_transport = SseServerTransport("/messages/")
streamable_transport = StreamableHTTPServerTransport(
    mcp_session_id=None,
    is_json_response_enabled=True,
)


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    from starlette.requests import Request
    request = Request(scope, receive)

    if request.method == "GET":
        accept = request.headers.get("accept", "")
        if "text/event-stream" in accept:
            async with sse_transport.connect_sse(scope, receive, send) as streams:
                read_stream, write_stream = streams
                await coordinator.app.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=coordinator.app.name,
                        server_version="1.0.0",
                        capabilities=coordinator.app.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        else:
            response = JSONResponse({"status": "ok", "message": "MCP Server"})
            await response(scope, receive, send)
        return

    if request.method == "OPTIONS":
        response = JSONResponse({"ok": True})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        await response(scope, receive, send)
        return

    # POST - Auth check
    if API_KEY:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {API_KEY}":
            response = JSONResponse({"error": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

    # Route POST messages to SSE handler if they have session_id
    query = request.url.query
    if "session_id" in query or "/messages" in request.url.path:
        await sse_transport.handle_post_message(scope, receive, send)
        return

    # Default: Streamable HTTP
    await streamable_transport.handle_request(scope, receive, send)


async def run_mcp_server():
    async with streamable_transport.connect() as streams:
        read_stream, write_stream = streams
        await coordinator.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=coordinator.app.name,
                server_version="1.0.0",
                capabilities=coordinator.app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


async def main():
    if API_KEY:
        print(f"MCP Server starting on port 8080 (auth enabled, dual SSE+HTTP)", file=sys.stderr)
    else:
        print(f"MCP Server starting on port 8080 (no auth, dual SSE+HTTP)", file=sys.stderr)

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        lifespan="off",
    )
    server = uvicorn.Server(config)
    await asyncio.gather(
        server.serve(),
        run_mcp_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
