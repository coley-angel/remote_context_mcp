# MCP Configuration Fix for Remote Config Loading

## Problem

The MCP server was not loading configuration from the private GitHub repository due to two issues:
1. Windsurf `mcp_config.json` environment variables weren't being passed properly
2. The server was using `raw.githubusercontent.com` which doesn't work with private repos

## Root Cause

1. **Environment Variables**: Windsurf's MCP server environment variable passing has inconsistent behavior
2. **Private Repository Access**: `raw.githubusercontent.com` requires different authentication for private repos
   - The GitHub API endpoint works better with token authentication for private repositories

## Solution: Use Shell Wrapper

### Option 1: Update mcp_config.json to use wrapper script (RECOMMENDED)

Update your `~/.codeium/windsurf/mcp_config.json` to use the wrapper script:

```json
{
  "mcpServers": {
    "team-config": {
      "command": "/Users/coangel/Documents/Development/CiscoOpsStack/remote_context_mcp/run_with_env.sh",
      "disabled": false,
      "disabledTools": []
    }
  }
}
```

The wrapper script (`run_with_env.sh`) explicitly sets the environment variables before running the MCP server.

### Option 2: Set environment variables in shell profile

Add to your `~/.zshrc` or `~/.bash_profile`:

```bash
export GITHUB_TOKEN="your_token_here"
export TEAM_CONFIG_REPO="https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles"
export TEAM_CONFIG_FILE="team_config.yaml"
export TEAM_CONFIG_BRANCH="main"
```

Then restart your terminal and Windsurf.

## Verification

After updating the configuration:

1. **Quit Windsurf** (⌘+Q)
2. **Reopen Windsurf**
3. **Check the logs** in the MCP server output (if accessible)
4. **Test with Cascade**:
   ```
   list profiles
   ```
   Should show "Ops Stack Team" instead of "default"

## How It Works

1. The wrapper script `run_with_env.sh` sets environment variables explicitly
2. The MCP server's `main.py` checks for `TEAM_CONFIG_REPO` environment variable
3. If set, it constructs the GitHub API URL for **private repository support**:
   ```
   https://api.github.com/repos/CiscoOpsStack/Ops_Stack_Dev_Profiles/contents/team_config.yaml?ref=main
   ```
4. It fetches the config using GitHub API with token authentication
5. The API returns base64-encoded content which is decoded automatically
6. No local `team_config.yaml` file is needed

## Code Changes Made

### 1. GitHub API Integration (main.py)
- Changed from `raw.githubusercontent.com` to `api.github.com/repos/.../contents/...`
- Added base64 decoding for GitHub API responses
- Improved token authentication headers

### 2. Enhanced Logging
- Added detailed environment variable logging
- Shows Python executable and script location
- Helps diagnose configuration issues

## Debugging

Check if environment variables are being set:

```bash
# From the project directory
./run_with_env.sh
# Look for the startup logs showing TEAM_CONFIG_REPO
```

## Files Created

- `run_with_env.sh` - Shell wrapper that sets environment variables
- `team_config.yaml.backup` - Backup of the local config (removed from active use)
- Enhanced logging in `main.py` to debug environment variable issues
