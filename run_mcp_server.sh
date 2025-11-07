#!/bin/bash
# MCP Server Launcher for Windsurf
# This ensures uv is in the PATH and runs the server correctly

cd "$(dirname "$0")"
exec /opt/homebrew/bin/uv run python main.py
