# V2 Cleanup Analysis - Obsolete Code & Simplification Opportunities

## Summary

The V2 refactor has made significant portions of the codebase obsolete. This document identifies files and functions that can be deleted or simplified.

## Files to DELETE

### 1. **main_new_tools.py**
- **Status**: Empty file
- **Action**: Delete
- **Reason**: No content

### 2. **ide_adapter.py** (91 lines)
- **Status**: Obsolete
- **Action**: Delete
- **Reason**: 
  - Provided compatibility layer between IDE configs and ide_manager
  - V2 loads IDE configs directly from YAML (no conversion needed)
  - Functions like `loadIdeConfigsFromTeamConfig()` no longer used
- **Current imports**: Used in `main.py:217` - can be removed

### 3. **mcp_tools.py** (216 lines)
- **Status**: Obsolete
- **Action**: Delete
- **Reason**:
  - Contains old `sync_profile_tool()` function
  - Logic replaced by new `sync_with_ide_config()` in main.py
  - Used generic content directories and IDE detection
  - V2 uses IDE-specific paths from config
- **Current imports**: Used in `main.py:788` (old sync_team_config) - can be removed

### 4. **mcp_tools_consolidated.py** (9801 bytes)
- **Status**: Likely obsolete
- **Action**: Review and delete if not used
- **Reason**: Consolidated old tool functions

## Functions to DELETE in main.py

### IDE Detection & Management (No longer needed in V2)

1. **`detect_current_ide()`** (Lines 234-293, ~60 lines)
   - Checks environment variables to detect IDE
   - V2 requires explicit user selection
   - **Delete**: Yes

2. **`get_current_ide()`** (Lines 296-305, ~10 lines)
   - Returns detected or user-specified IDE
   - V2 doesn't track "current IDE"
   - **Delete**: Yes

3. **`set_current_ide()`** (Lines 307-315, ~9 lines)
   - Sets IDE explicitly
   - V2 doesn't maintain IDE state
   - **Delete**: Yes

4. **`detect_workspace_root()`** (Lines 318-370, ~53 lines)
   - Auto-detects workspace from markers
   - V2 requires explicit `workspace_path`
   - **Delete**: Yes

5. **`get_workspace_dir()`** (Lines 373-387, ~15 lines)
   - Gets workspace directory
   - V2 requires explicit path
   - **Delete**: Yes

6. **`get_ide_content_dir()`** (Lines 390-433, ~44 lines)
   - Returns IDE-specific content directory
   - V2 uses paths from IDE config
   - **Delete**: Yes

7. **`get_ide_manager()`** (Lines 213-221, ~9 lines)
   - Creates IDE manager with configs
   - May not be needed in V2
   - **Review**: Check if used by legacy functions

### Legacy Tool Functions

8. **`sync_team_config()`** (Lines 730-875, ~145 lines)
   - Old sync function with scope logic
   - Replaced by `sync_with_ide_config()`
   - **Delete**: Yes (keep new V2 version)

9. **`cleanup_profile_rules()`** (Lines 888-932, ~45 lines)
   - Uses ide_manager.cleanup_all_ides()
   - V2 doesn't need cleanup (workspace-only)
   - **Simplify or Delete**: User can delete workspace dirs manually

10. **`deactivate_profile()`** (Lines 943-1028, ~86 lines)
    - Deactivates profile, cleans up MCP servers and rules
    - Uses ide_manager heavily
    - **Simplify**: Just deactivate in config, no cleanup needed

11. **`update_mcp_servers()`** (Lines 1267-1326, ~60 lines)
    - Updates MCP servers using ide_manager
    - V2 may not need this (MCP configs could be static)
    - **Review**: Depends on MCP management strategy

12. **`list_installed_ides()`** (Lines 1329-1372, ~44 lines)
    - Detects installed IDEs
    - V2 lists available IDE configs from profile instead
    - **Delete**: Replaced by `list_ide_configs()`

13. **`get_current_ide_info()`** (Lines 1375-1418, ~44 lines)
    - Gets current IDE information
    - V2 doesn't track current IDE
    - **Delete**: Yes

14. **`set_ide()`** (Lines 1421-1461, ~41 lines)
    - Sets IDE explicitly
    - V2 doesn't maintain IDE state
    - **Delete**: Yes

### MCP Tool Wrappers

15. **`ide()` tool** (Lines 1738-1768, ~31 lines)
    - Wrapper for IDE management (info, list, set)
    - V2 doesn't need IDE management
    - **Delete**: Yes

## Functions to SIMPLIFY

### 1. **main.py - Global Variables**

**Current:**
```python
_ide_manager = None
_current_ide: Optional[IDEType] = None
```

**Simplified:**
```python
# Remove these - not needed in V2
```

### 2. **main.py - Imports**

**Current:**
```python
from ide_manager import create_ide_manager
from ide_adapter import loadIdeConfigsFromTeamConfig
```

**Simplified:**
```python
# Remove these imports
```

### 3. **profile() tool** 

Currently has cleanup and deactivate actions that use ide_manager.

**Simplify:**
- Remove cleanup action (or make it workspace-only)
- Simplify deactivate (just update config, no IDE cleanup)

## Files to SIMPLIFY

### 1. **ide_manager.py** (~37,649 bytes)

Large file with many functions for IDE detection and global path management.

**Functions likely obsolete:**
- `detect_installed_ides()` - V2 lists configs, not installed IDEs
- `get_settings_path()` - V2 doesn't need global settings paths
- Global path construction logic
- IDE-specific directory creation

**Functions to keep:**
- MCP config management (if still needed)
- Potentially some helper functions

**Recommendation**: Create minimal `mcp_config_manager.py` with just MCP config logic

### 2. **content_tracker.py** (~11,484 bytes)

May have logic for tracking content in global directories.

**Review needed**: Check if tracks global vs workspace paths

## Test Files to UPDATE/DELETE

Located in `/tests/`:
- `test_config_parse.py` - May need updates for V2 config
- `test_env.py` - Check if tests IDE detection
- `test_frontmatter.py` - Should still work
- `test_mcp_tools.py` - Tests old mcp_tools.py - **Delete or update**
- `test_server.py` - May need updates
- `test_sync_mcp.py` - Tests sync logic - **Update for V2**

## Schemas to CLEAN

### schemas.py

**Legacy code to remove:**
```python
# Lines ~337-420: get_default_ide_configs() - Old IDE configs
# Can mark as deprecated or remove entirely
```

**Keep:**
- IDEPaths, IDEProfile, FrontmatterConfig (V2 structures)
- get_default_ide_profiles() (V2 defaults)

## Cleanup Priority

### Priority 1: Quick Wins (Low Risk)
1. Delete `main_new_tools.py` (empty)
2. Delete `ide_adapter.py` (remove import from main.py)
3. Delete `mcp_tools.py` (remove import from main.py)
4. Delete obsolete docs (already done in your repo)

### Priority 2: Function Removal (Medium Risk)
1. Remove IDE detection functions
2. Remove workspace detection functions
3. Remove old `sync_team_config()`
4. Remove `set_ide()`, `get_current_ide_info()`
5. Remove `list_installed_ides()`

### Priority 3: Simplification (Higher Risk)
1. Simplify or remove `cleanup_profile_rules()`
2. Simplify or remove `deactivate_profile()`
3. Review `update_mcp_servers()` necessity
4. Simplify `ide_manager.py` or create minimal replacement

### Priority 4: Test Updates
1. Update or remove test files
2. Create V2-specific tests

## Estimated Lines of Code Reduction

| Category | Current | After Cleanup | Reduction |
|----------|---------|---------------|-----------|
| Deleted files | ~500 lines | 0 | -500 |
| main.py functions | ~600 lines | 0 | -600 |
| ide_manager.py | ~1,200 lines | ~300 | -900 |
| Total | ~2,300 lines | ~300 | **-2,000 lines (~87%)** |

## Implementation Plan

```bash
# Phase 1: Safe deletions
rm main_new_tools.py
rm ide_adapter.py
rm mcp_tools.py
rm mcp_tools_consolidated.py

# Phase 2: Update main.py
# Remove imports
# Remove obsolete functions
# Update profile() tool
# Clean up global variables

# Phase 3: Simplify ide_manager.py
# Extract MCP config logic to mcp_config_manager.py
# Remove IDE detection and global path logic

# Phase 4: Test
python -m pytest tests/
# Update failing tests for V2

# Phase 5: Documentation
# Update README.md to remove references to deleted functions
# Add V2 migration guide
```

## Backward Compatibility

**Breaking Changes:**
- All IDE detection removed
- All auto-workspace detection removed
- Global paths removed
- Scope parameter removed

**Migration Required:**
- Users must provide explicit `ide_choice` or `ide_name`
- Users must provide explicit `workspace_path`
- Update all tool calls to V2 format

## Recommendation

**Immediate Actions:**
1. ✅ Delete empty and obsolete files (Priority 1)
2. ✅ Remove obsolete functions from main.py (Priority 2)
3. ⚠️  Keep ide_manager.py for now (review MCP config needs first)
4. ⏸️  Defer test updates until after cleanup

**Rationale:**
- Reduces maintenance burden
- Makes codebase clearer
- Enforces V2 patterns
- Removes confusion from having both V1 and V2 code

## Files Summary

### DELETE (4 files, ~800 lines):
- ❌ `main_new_tools.py` (empty)
- ❌ `ide_adapter.py` (91 lines)
- ❌ `mcp_tools.py` (216 lines)
- ❌ `mcp_tools_consolidated.py` (~500 lines)

### SIMPLIFY (2 files):
- ⚠️  `main.py` (remove ~600 lines of obsolete functions)
- ⚠️  `ide_manager.py` (remove ~900 lines, keep MCP config logic)

### REVIEW (1 file):
- 🔍 `content_tracker.py` (check for global path tracking)

**Total cleanup potential: ~2,000 lines of code**
