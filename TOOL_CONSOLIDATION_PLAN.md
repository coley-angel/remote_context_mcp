# MCP Tool Consolidation Plan

## Current Tools (13 total)
1. sync_team_config
2. cleanup_profile_rules
3. list_profiles
4. set_active_profile
5. check_for_updates
6. validate_content_security
7. update_mcp_servers
8. list_installed_ides
9. get_current_ide_info
10. set_ide
11. get_config
12. reload_config
13. clear_cache

## Proposed Consolidation (6 tools)

### 1. **profile** (consolidates 4 → 1)
Replaces: list_profiles, set_active_profile, get_config, cleanup_profile_rules

```python
async def profile(
    action: str = "list",  # list, activate, show, cleanup
    profile_name: Optional[str] = None,
    auto_sync: bool = True
) -> str
```

**Actions:**
- `list` - Show all profiles (was list_profiles)
- `activate` - Set active profile (was set_active_profile)
- `show` - Show detailed config (was get_config)
- `cleanup` - Remove profile rules (was cleanup_profile_rules)

### 2. **sync** (consolidates 3 → 1)
Replaces: sync_team_config, check_for_updates, reload_config

```python
async def sync(
    action: str = "full",  # full, check, reload
    profile_name: Optional[str] = None,
    force_update: bool = False,
    sync_to_ides: bool = True
) -> str
```

**Actions:**
- `full` - Full sync (was sync_team_config)
- `check` - Check for updates only (was check_for_updates)
- `reload` - Reload config (was reload_config)

### 3. **mcp_servers** (consolidates 1 tool, clearer name)
Replaces: update_mcp_servers

```python
async def mcp_servers(
    action: str = "update",  # update, list
    profile_name: Optional[str] = None,
    reload: bool = True
) -> str
```

**Actions:**
- `update` - Update MCP server configs (was update_mcp_servers)
- `list` - List configured servers (new, useful addition)

### 4. **ide** (consolidates 3 → 1)
Replaces: list_installed_ides, get_current_ide_info, set_ide

```python
async def ide(
    action: str = "info",  # info, list, set
    ide_name: Optional[str] = None
) -> str
```

**Actions:**
- `info` - Current IDE info (was get_current_ide_info)
- `list` - List installed IDEs (was list_installed_ides)
- `set` - Set IDE explicitly (was set_ide)

### 5. **validate** (keep as-is, specific use case)
Replaces: validate_content_security

```python
async def validate(
    content: str,
    content_type: str = "general",
    filename: str = "unknown"
) -> str
```

### 6. **cache** (keep as-is, dangerous operation)
Replaces: clear_cache

```python
async def cache(
    action: str = "clear",  # clear, info
    cache_type: str = "all"
) -> str
```

## Benefits

**Before:** 13 tools
**After:** 6 tools (54% reduction)

### Advantages:
1. **Clearer organization** - Related actions grouped together
2. **Fewer tools to remember** - Easier for AI to use correctly
3. **Consistent interface** - All use action parameter
4. **Easy to extend** - Add new actions without new tools
5. **Better discoverability** - Related functionality in one place

### Example Usage:

```python
# Before
list_profiles()
set_active_profile("production", auto_sync=True)
sync_team_config("production", force_update=True)
update_mcp_servers("production")

# After
profile(action="list")
profile(action="activate", profile_name="production", auto_sync=True)
sync(action="full", profile_name="production", force_update=True)
mcp_servers(action="update", profile_name="production")
```

## Implementation Notes

- Maintain backward compatibility by keeping old function implementations
- Use action parameter with clear validation and error messages
- Document all actions in tool descriptions
- Add action="list" to show available actions when no action specified
