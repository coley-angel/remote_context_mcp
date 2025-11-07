# Team-Config Tracking System

## Overview

The team-config MCP server now tracks **all content and configurations** it manages, enabling automatic cleanup when profiles change while preserving manually added items.

## What Gets Tracked

### 1. MCP Servers
- Server configurations in IDE mcp.json/mcp_config.json files
- Marked with `_managed_by: "team-config"` field
- Tracked in `~/.mcp-team-config/state/{ide}_managed_servers.json`

### 2. Content Files
- Instructions (.md files in instructions/)
- Rules (.md files in rules/)
- Workflows (.md files in workflows/)
- Prompts (.md files in prompts/)
- Tracked in `~/.mcp-team-config/state/content_{profile}.json`
- Marker files: `.team-config-managed.json` in each content directory

### 3. Instruction Locations
- IDE settings entries for instruction file paths
- Tracked in `~/.mcp-team-config/state/{ide}_managed_instructions.json`

## How It Works

### State Files

All tracking data is stored in `~/.mcp-team-config/state/`:

```
~/.mcp-team-config/state/
├── vscode_managed_servers.json          # VS Code MCP servers
├── cursor_managed_servers.json          # Cursor MCP servers
├── windsurf_managed_servers.json        # Windsurf MCP servers
├── vscode_managed_instructions.json     # VS Code instruction paths
├── cursor_managed_instructions.json     # Cursor instruction paths
├── windsurf_managed_instructions.json   # Windsurf instruction paths
└── content_default.json                 # Content files for "default" profile
```

### MCP Server Tracking

**When Adding Server:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "..."},
      "_managed_by": "team-config"  // ← Tracking marker
    }
  }
}
```

**Statefile:**
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

### Content File Tracking

**Statefile (`content_default.json`):**
```json
{
  "profile": "default",
  "updated_at": "2025-11-06T21:00:00",
  "content": {
    "instructions": {
      "/path/to/instruction_0.md": {
        "source": "github:org/repo/instructions/coding.md",
        "size": 1234,
        "added_at": "2025-11-06T20:00:00"
      }
    },
    "rules": {},
    "workflows": {},
    "prompts": {}
  }
}
```

**Marker File (`.team-config-managed.json` in each directory):**
```json
{
  "managed_by": "team-config",
  "content_type": "instructions",
  "created_at": "2025-11-06T20:00:00",
  "files": [
    "/path/to/instruction_0.md",
    "/path/to/instruction_1.md"
  ]
}
```

### Instruction Location Tracking

**Statefile:**
```json
{
  "updated_at": "2025-11-06T21:00:00",
  "paths": {
    "/Users/name/vscode-instructions/default/instructions": true
  }
}
```

## Automatic Cleanup

### When Profile Changes

**Scenario 1: Removing an MCP Server**

```yaml
# Before
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

```yaml
# After - gitlab removed
profiles:
  default:
    mcp_servers:
      - name: github
        command: npx
        enabled: true
```

**Result after sync:**
- ✅ `github` server: kept (still in profile)
- ✅ `gitlab` server: **automatically removed** (no longer in profile)
- ✅ `my-custom-server`: kept (not managed by tool)

**Scenario 2: Removing Content Sources**

```yaml
# Before
profiles:
  default:
    instructions:
      - repo: org/repo
        paths: ["*.md"]
```

```yaml
# After - source removed
profiles:
  default:
    instructions: []  # Empty
```

**Result after sync:**
- ✅ All managed instruction files: **automatically removed**
- ✅ Instruction path from IDE settings: **automatically removed**
- ✅ Manually created .md files in same directory: kept (not in tracking)

**Scenario 3: Disabling Profile**

```yaml
profiles:
  default:
    active: false
    mcp_servers: []
    instructions: []
    rules: []
    workflows: []
    prompts: []
```

**Result after sync:**
- ✅ All managed MCP servers: **removed**
- ✅ All managed content files: **removed**
- ✅ All managed instruction paths: **removed**
- ✅ Manual additions: **preserved**

## Safety Features

### Dual Verification
Content is only removed if:
1. **In statefile** (was previously managed)
2. **Has marker** (`_managed_by` field or in marker file)
3. **Not in current profile** (removed from config)

### Protection for Manual Content
Items are **never** removed if:
- Missing the `_managed_by` marker
- Not in the statefile
- Manually added to IDE config

### Fail-Safe Operations
- All file operations are logged
- Errors don't stop the entire sync process
- State files are written atomically

## Usage Examples

### Example 1: Clean Sync After Profile Change

```bash
# 1. Edit team_config.yaml - remove some servers and content sources
# 2. Sync profile
```

The tool will:
1. Read previous state from statefiles
2. Compare with new profile configuration
3. Remove obsolete managed items
4. Add/update new items
5. Update statefiles

### Example 2: Convert Managed to Manual

To stop tracking a specific MCP server:

```json
// In mcp_config.json, remove the marker:
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["..."],
      // Remove this line:
      // "_managed_by": "team-config"
    }
  }
}
```

The tool will now treat `my-server` as manually configured.

### Example 3: View Current Tracking

```bash
# View tracked MCP servers
cat ~/.mcp-team-config/state/windsurf_managed_servers.json

# View tracked content files
cat ~/.mcp-team-config/state/content_default.json

# View tracked instruction paths
cat ~/.mcp-team-config/state/windsurf_managed_instructions.json
```

### Example 4: Reset Tracking

```bash
# Clear all tracking data
rm -rf ~/.mcp-team-config/state/

# Next sync will re-track everything as managed
```

## Sync Response

The sync response now includes cleanup information:

```json
{
  "success": true,
  "profile": "default",
  "synced_content": {
    "instructions": 5,
    "rules": 3,
    "workflows": 2,
    "prompts": 1
  },
  "removed_content": {
    "instructions": 2,
    "rules": 1,
    "workflows": 0,
    "prompts": 0
  },
  "ide_sync": {
    "vscode": true,
    "windsurf": true
  }
}
```

## Benefits

### 1. **Clean Configuration**
- No orphaned MCP servers
- No stale content files
- No outdated instruction paths

### 2. **Safe Operations**
- Manual additions are never touched
- Dual verification before removal
- Comprehensive error handling

### 3. **Transparent**
- Easy to see what's managed (marker fields)
- State files are human-readable JSON
- Detailed logging of all operations

### 4. **Automatic**
- No manual cleanup needed
- Works seamlessly with profile changes
- Handles edge cases gracefully

### 5. **Flexible**
- Can convert managed to manual anytime
- Easy to reset tracking
- Works across multiple profiles

## Troubleshooting

### View What Will Be Removed

Before syncing, check state files to see what's currently tracked.

### Preserve Specific Items

Remove the `_managed_by` marker to convert managed items to manual.

### Debugging

Check logs for detailed operation information:
```bash
# Logs show each removal with reason
[INFO] Removing managed server 'gitlab' (no longer in profile)
[INFO] Removed managed instructions file: /path/to/file.md
```

### Reset If Needed

If tracking gets out of sync:
```bash
rm -rf ~/.mcp-team-config/state/
# Then re-sync to rebuild clean state
```

## Technical Implementation

### State File Format

All state files use consistent JSON structure:
- `updated_at`: ISO 8601 timestamp
- `profile`: Profile name (for content and servers)
- Content-specific data (servers, paths, files)

### Marker Strategy

- **MCP Servers**: `_managed_by` field in server config
- **Content Files**: `.team-config-managed.json` in each directory
- **Instruction Paths**: Tracked in dedicated statefile

### Atomic Operations

1. Read current state
2. Read new configuration
3. Calculate differences
4. Apply changes (with error handling)
5. Update state files
6. Write marker files

## Migration from Old System

If you previously used team-config without tracking:

1. **First sync** will create state files for all current items
2. All existing items will be marked as managed
3. Future syncs will properly track changes

To preserve existing manual items before first sync:
- They won't have markers yet
- They'll be preserved automatically
- Only new synced items get markers
