# File Tracking Gap Analysis

## Issue

Not all team-managed files are tracked for removal on profile switch.

## Currently Tracked ✅

Files with `.team-config.{profile}` suffix in:
- Rules directory
- Workflows directory  
- Prompts directory
- Instructions directory

## NOT Tracked ❌

### 1. MCP Config Files

**Problem:**
- `.cursor/mcp.json`, `.vscode/mcp.json`, etc.
- Not synced by V2 `sync_with_ide_config()`
- If created manually or by V1, they persist
- No cleanup on profile switch

**Impact:**
- Old profile's MCP servers remain active
- May cause conflicts with new profile
- User confusion about which MCPs are active

### 2. IDE Settings Files

**Problem:**
- `.cursor/settings.json`, `.vscode/settings.json`
- Never managed by team-config system
- No cleanup needed (user-managed)

**Impact:**
- None (expected behavior)

## Root Cause

```python
# In cleanup_profile_files()
for content_type in ['rules', 'workflows', 'prompts', 'instructions']:
    # MCP configs missing from this list!
```

## Solutions

### Option 1: Track MCP Configs (Recommended)

Add MCP config tracking to V2 sync:

```python
# In sync_with_ide_config()
if profile.mcp_servers and ide_config.paths.mcp_config:
    mcp_config_path = workspace_dir / ide_config.paths.mcp_config
    
    # Save with team-config suffix
    config_name = f"mcp.team-config.{profile.name}.json"
    mcp_file = mcp_config_path.parent / config_name
    
    # Write MCP config
    mcp_content = generate_mcp_config(profile.mcp_servers, ide_name)
    mcp_file.write_text(json.dumps(mcp_content, indent=2))
```

```python
# In cleanup_profile_files()
for content_type in ['rules', 'workflows', 'prompts', 'instructions', 'mcp_config']:
    # Now includes MCP configs!
```

**Pros:**
- ✅ Complete tracking
- ✅ Clean profile switches
- ✅ No orphaned MCP configs

**Cons:**
- ⚠️ Need to implement MCP config sync in V2
- ⚠️ Windsurf doesn't support local MCP configs

### Option 2: Document the Gap

Add to documentation:

```markdown
## MCP Config Management

**Note:** MCP config files are NOT tracked by the team-config system.

When switching profiles:
- Rules, workflows, prompts, instructions are cleaned up
- MCP config files are NOT cleaned up

To manually clean up MCP configs:
```bash
rm .cursor/mcp.json
rm .vscode/mcp.json
```

**Pros:**
- ✅ Simple
- ✅ No code changes

**Cons:**
- ❌ Manual cleanup required
- ❌ User confusion

### Option 3: Hybrid Approach

Track MCP configs for IDEs that support local configs:

```python
if ide_config.paths.mcp_config:  # None for Windsurf
    # Track MCP config for this IDE
    # Skip for Windsurf (uses global only)
```

**Pros:**
- ✅ Works with IDE limitations
- ✅ Tracks what can be tracked

**Cons:**
- ⚠️ Inconsistent behavior across IDEs

## Recommendation

**Implement Option 1 (Full MCP Config Tracking)**

1. Add MCP config sync to `sync_with_ide_config()`
2. Add `mcp_config` to cleanup loop
3. Handle Windsurf special case (skip if mcp_config is None)
4. Add suffix to MCP config files

## Implementation Plan

### Step 1: Add MCP Config Sync

```python
async def sync_with_ide_config(...):
    # ... existing content sync ...
    
    # Sync MCP configs (if IDE supports local configs)
    if profile.mcp_servers and ide_config.paths.mcp_config:
        mcp_config_dir = workspace_dir / ide_config.paths.mcp_config
        mcp_config_dir = mcp_config_dir.parent if mcp_config_dir.suffix else mcp_config_dir
        mcp_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate MCP config with team-config suffix
        config_filename = f"mcp.team-config.{profile.name}.json"
        mcp_config_file = mcp_config_dir / config_filename
        
        # Build MCP config
        mcp_config = {
            "mcpServers": {}
        }
        
        for server in profile.mcp_servers:
            server_config = {
                "command": server.command,
                "args": server.args,
                "env": server.env
            }
            if server.disabled:
                server_config["disabled"] = True
            if server.autoApprove:
                server_config["autoApprove"] = server.autoApprove
            
            mcp_config["mcpServers"][server.name] = server_config
        
        # Write with suffix
        mcp_config_file.write_text(json.dumps(mcp_config, indent=2))
        logger.info(f"✓ Synced MCP config: {mcp_config_file.relative_to(workspace_dir)}")
```

### Step 2: Update Cleanup

```python
def cleanup_profile_files(...):
    for content_type in ['rules', 'workflows', 'prompts', 'instructions', 'mcp_config']:
        content_path = getattr(ide_config.paths, content_type, None)
        if not content_path:
            continue  # Skip if None (e.g., Windsurf MCP)
        
        # Special handling for MCP config (it's a file, not a directory)
        if content_type == 'mcp_config':
            mcp_file = workspace_dir / content_path
            mcp_dir = mcp_file.parent if mcp_file.suffix else mcp_file
            if mcp_dir.exists():
                # Look for mcp.team-config.{profile}.json
                for file in mcp_dir.glob(f"mcp.team-config.{profile_name}.json"):
                    try:
                        file.unlink()
                        deleted.append(str(file.relative_to(workspace_dir)))
                        logger.info(f"✓ Removed: {file.relative_to(workspace_dir)}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file}: {e}")
        else:
            # Existing logic for content directories
            ...
```

### Step 3: Update Documentation

```markdown
## Tracked Files

All team-managed files have `.team-config.{profile}` suffix:
- Rules: `rule1.team-config.default.md`
- Workflows: `workflow1.team-config.default.md`
- Prompts: `prompt1.team-config.default.md`
- Instructions: `instruction1.team-config.default.md`
- MCP Configs: `mcp.team-config.default.json` (Cursor, VS Code only)

Note: Windsurf uses global MCP config only, so no local tracking.
```

## Testing Checklist

- [ ] MCP config synced with suffix
- [ ] MCP config cleaned up on profile switch
- [ ] Windsurf skips MCP config (mcp_config is None)
- [ ] VS Code and Cursor sync MCP configs
- [ ] User files without suffix preserved
- [ ] Multiple profiles can coexist temporarily

## Priority

**HIGH** - This affects profile switching functionality and can cause confusion.

## Workaround (Until Fixed)

Manual cleanup when switching profiles:

```bash
# After switching profiles
rm .cursor/mcp.json  # If exists
rm .vscode/mcp.json  # If exists

# Then sync new profile
sync(action='full', workspace_path='/path', ide_choice=2)
```
