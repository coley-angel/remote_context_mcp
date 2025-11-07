# Managed MCP Servers

## Overview

The team-config MCP tool now tracks which MCP servers it manages, allowing it to automatically clean up servers that are no longer in your profile while preserving manually configured ones.

## How It Works

### 1. Server Marking

When the tool configures an MCP server, it adds a special marker field:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {...},
      "_managed_by": "team-config"
    }
  }
}
```

The `_managed_by` field identifies servers managed by the tool.

### 2. Statefile Tracking

The tool maintains state files at `~/.mcp-team-config/state/` to track managed servers:

- `vscode_managed_servers.json` - VS Code global servers
- `cursor_managed_servers.json` - Cursor global servers  
- `windsurf_managed_servers.json` - Windsurf global servers
- `{ide}_workspace_{hash}.json` - Workspace-specific servers

Example statefile:

```json
{
  "profile": "default",
  "updated_at": "2025-11-06T21:00:00",
  "servers": {
    "github": {
      "profile": "default",
      "added_at": "2025-11-06T20:00:00",
      "command": "npx"
    }
  }
}
```

### 3. Automatic Cleanup

When you sync your profile, the tool:

1. **Reads** the statefile to see which servers it previously managed
2. **Compares** with the current profile's server list
3. **Removes** servers that:
   - Were previously managed (in statefile)
   - Are no longer in the active profile
   - Still have the `_managed_by` marker
4. **Preserves** servers that:
   - Don't have the `_managed_by` marker (manually configured)
   - Are not in the statefile

## Usage Examples

### Example 1: Removing a Server from Profile

**Before** (`team_config.yaml`):
```yaml
profiles:
  default:
    mcp_servers:
      - name: github
        command: npx
        enabled: true
      - name: gitlab
        command: npx
        enabled: true
```

**After removing gitlab** (`team_config.yaml`):
```yaml
profiles:
  default:
    mcp_servers:
      - name: github
        command: npx
        enabled: true
```

**Sync the profile:**
```bash
# The gitlab server will be automatically removed from all IDEs
```

### Example 2: Disabling a Profile

**Disable profile:**
```yaml
profiles:
  default:
    active: false
    mcp_servers: []  # Remove all servers
```

**Sync:**
```bash
# All managed servers will be removed, manual ones stay
```

### Example 3: Mixed Manual and Managed Servers

Your `mcp_config.json` has:
- `github` (managed by team-config)
- `my-custom-server` (manually added by you)

When you remove `github` from the profile and sync:
- ✅ `github` is removed (was managed)
- ✅ `my-custom-server` stays (not managed)

## Benefits

1. **Clean Configuration**: No orphaned servers cluttering your IDE configs
2. **Safe**: Manually configured servers are never touched
3. **Automatic**: Works seamlessly when you update profiles
4. **Transparent**: Easy to see which servers are managed (via marker and statefile)
5. **Reliable**: Dual tracking (marker + statefile) ensures accuracy

## Troubleshooting

### View Managed Servers

Check the statefile for your IDE:

```bash
cat ~/.mcp-team-config/state/windsurf_managed_servers.json
```

### Manually Remove Management

If you want to convert a managed server to manual:

1. Remove the `_managed_by` field from the server config in `mcp_config.json`
2. The tool will now treat it as manually configured

### Reset All Managed Servers

To clear all tracking and start fresh:

```bash
rm -rf ~/.mcp-team-config/state/
```

Then resync your profile - all current servers will be marked as managed.

## Technical Details

- **Merge mode** (default): Removes only managed servers not in profile, preserves manual ones
- **Replace mode**: Removes all managed servers, then adds profile servers
- **Statefile format**: JSON with profile name, timestamps, and server metadata
- **Marker field**: `_managed_by: "team-config"` added to all managed server configs
