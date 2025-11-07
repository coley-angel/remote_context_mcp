# Profile Deactivate Feature

## Summary

Added a new **`deactivate`** action to the `profile()` tool that performs a complete cleanup of a profile, including MCP servers, rules, workflows, and prompts.

## Usage

```python
profile(action="deactivate", profile_name="default")
```

## What It Does

The `deactivate` action performs a **complete cleanup** in three steps:

### Step 1: Remove MCP Servers
- Removes all MCP servers managed by the profile
- Updates all configured IDEs (VS Code, Cursor, Windsurf)
- Uses the statefile tracking system to identify managed servers
- Protects manually configured servers (never touches them)

### Step 2: Clean Up Content
- Removes rules from all IDEs
- Removes workflows from all IDEs
- Removes prompts from all IDEs
- Clears tracking statefiles

### Step 3: Mark Profile Inactive
- Sets the profile's `active` flag to `false` (if using local config)
- Skips this step for remote configurations (read-only)

## Response Format

```json
{
  "success": true,
  "profile": "default",
  "results": {
    "mcp_servers_removed": {
      "vscode": true,
      "cursor": true,
      "windsurf": true
    },
    "content_cleaned": {
      "vscode": true,
      "windsurf": true
    },
    "profile_marked_inactive": true
  },
  "message": "Profile 'default' fully deactivated",
  "details": {
    "mcp_servers_count": 4,
    "rules_sources": 1,
    "workflows_sources": 1,
    "prompts_sources": 0
  }
}
```

## Comparison: cleanup vs deactivate

### `profile(action="cleanup")`
**Partial cleanup** - Only removes content:
- ✓ Removes rules, workflows, prompts
- ✗ Leaves MCP servers in place
- ✗ Doesn't mark profile as inactive
- **Use when:** You want to temporarily clear content but keep MCP servers

### `profile(action="deactivate")`
**Complete cleanup** - Removes everything:
- ✓ Removes MCP servers managed by the profile
- ✓ Removes rules, workflows, prompts
- ✓ Marks profile as inactive (if local config)
- **Use when:** You want to fully deactivate and clean up a profile

## Safety Features

### Protected Servers
- **NEVER removes** servers without tracking in the statefile
- **NEVER modifies** manually configured servers
- Only removes servers that were added by team-config

### Tracking System
For Windsurf (which has strict JSON schema):
- Uses separate statefile: `~/.mcp-team-config/state/windsurf_managed_servers.json`
- Tracks which servers are managed by team-config
- Preserves servers not in the statefile

For Cursor/VS Code:
- Uses `_managed_by: "team-config"` marker in JSON
- Same protection guarantees

## Example Workflow

### Scenario: Switch from team profile to personal setup

```python
# 1. Check what will be removed
profile(action="list")  # Shows active profile and MCP servers

# 2. Fully deactivate the team profile
profile(action="deactivate", profile_name="default")

# Result:
# - All 4 MCP servers removed from Windsurf, Cursor, VS Code
# - All rules and workflows cleaned up
# - Profile marked as inactive
# - Your manually configured MCP servers remain untouched
```

## Implementation Details

### Location
- Function: `deactivate_profile()` in `main.py` (line 627)
- Tool integration: `profile()` tool (line 1237)

### Key Code
```python
async def deactivate_profile(profile_name: Optional[str] = None) -> str:
    # Step 1: Remove MCP servers by updating with empty list
    ide_manager.update_mcp_servers(
        ide_type,
        [],  # Empty list removes all managed servers
        WORKSPACE_DIR,
        merge=True,
        profile_name=profile_name
    )
    
    # Step 2: Cleanup content
    ide_manager.cleanup_all_ides(profile_name, WORKSPACE_DIR)
    
    # Step 3: Mark inactive (local config only)
    profile.active = False
    ConfigLoader.save_to_file(config, config_path)
```

## Testing Recommendations

1. **Before deactivation:**
   - Run `profile(action="list")` to see what will be removed
   - Run `mcp_servers(action="list")` to see managed servers

2. **After deactivation:**
   - Verify MCP servers are removed from `mcp_config.json`
   - Check rules directory is empty
   - Confirm statefile is cleared: `~/.mcp-team-config/state/`
   - Verify manually configured servers remain

3. **Reload IDE:**
   - Restart Windsurf/Cursor/VS Code to apply changes
   - Verify no team-config MCP servers are loaded

## Files Modified

- `/main.py` - Added `deactivate_profile()` function and integrated into `profile()` tool
- `/README.md` - Added documentation for deactivate action
- `/CONSOLIDATION_CHANGES.md` - Updated tool list to include deactivate
- `/DEACTIVATE_FEATURE.md` - This file (new)

## Benefits

1. **One-Command Cleanup**: Single command removes everything
2. **Complete Reset**: Returns to clean state
3. **Safe**: Protects manually configured servers
4. **Transparent**: Clear reporting of what was removed
5. **Reversible**: Can reactivate profile with `profile(action="activate")`
