#!/bin/bash
# Wrapper script to run MCP server with explicit environment variables
# This ensures environment variables are set even if mcp_config.json doesn't pass them correctly

export GITHUB_TOKEN="${GITHUB_TOKEN:-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}"
export TEAM_CONFIG_REPO="${TEAM_CONFIG_REPO:-https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles}"
export TEAM_CONFIG_FILE="${TEAM_CONFIG_FILE:-team_config.yaml}"
export TEAM_CONFIG_BRANCH="${TEAM_CONFIG_BRANCH:-main}"

# Change to script directory
cd "$(dirname "$0")" || exit 1

# Forward signals to child process
trap 'kill $PID 2>/dev/null' TERM INT

# Run the MCP server in background and wait
uv run python main.py &
PID=$!
wait $PID
