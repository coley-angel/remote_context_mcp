# MCP Tools Assessment for V2

## Current Tools Status

### ✅ KEEP - V2 Core Tools

1. **`sync()`** - V2 version
   - **Status**: ✅ Keep - Core V2 functionality
   - **Actions**: list_ides, full, check, reload
   - **Usage**: User selects IDE explicitly

2. **`profile()`** 
   - **Status**: ⚠️ Keep but simplify
   - **Actions**: list, activate, show, cleanup, deactivate
   - **Issue**: cleanup and deactivate use V1 ide_manager
   - **Fix**: Remove or simplify cleanup/deactivate actions

3. **`diagnose_config()`**
   - **Status**: ✅ Keep - Useful diagnostic tool
   - **Purpose**: Check config loading and GitHub connection

### ❌ REMOVE - V1 Only Tools

4. **`ide()`** tool
   - **Status**: ❌ Remove - V1 only
   - **Actions**: info, list, set
   - **Reason**: V2 doesn't track current IDE
   - **Replacement**: Use `sync(action='list_ides')` instead

5. **`mcp_servers()`** 
   - **Status**: ❌ Remove or simplify heavily
   - **Actions**: update, list
   - **Reason**: Uses ide_manager, global paths
   - **V2 approach**: MCP configs could be static in workspace
   - **Decision**: Remove for now, add back if needed

### 🔧 UTILITY Tools

6. **`validate_content_security()`**
   - **Status**: ✅ Keep
   - **Issue**: ⚠️ DUPLICATE definition (appears twice!)
   - **Fix**: Remove duplicate

7. **`clear_cache()`**
   - **Status**: ✅ Keep  
   - **Issue**: ⚠️ DUPLICATE definition (appears twice!)
   - **Fix**: Remove duplicate

## Issues to Fix

### 1. Duplicate Tool Definitions

```
Tool already exists: validate_content_security
Tool already exists: clear_cache
```

**Location**: Both tools defined twice in main.py
- First at ~line 1208 and 1807
- Second at ~line 2095 and 2142

**Fix**: Remove second definitions

### 2. V1 Functions Still Called

**`profile()` tool** calls V1 functions:
- `cleanup_profile_rules()` - uses ide_manager
- `deactivate_profile()` - uses ide_manager  

**Options**:
a. Remove cleanup and deactivate actions entirely
b. Rewrite them for V2 (workspace-only, no IDE manager)
c. Mark as deprecated/unsupported in V2

**Recommendation**: Remove for simplicity

### 3. `ide()` Tool

Entire tool is V1-only:
- `get_current_ide_info()` - uses IDE detection
- `list_installed_ides()` - detects installed IDEs
- `set_ide()` - sets current IDE state

**Fix**: Remove entire tool

### 4. `mcp_servers()` Tool

Uses ide_manager heavily:
- Updates MCP configs across multiple IDEs
- Handles global vs workspace paths
- Requires IDE detection

**V2 approach**: 
- MCP configs are static (in repo)
- User manages them manually
- Or: Simplified version that just copies configs

**Recommendation**: Remove for now

## Final V2 Tool Set

### Core Tools (4)
1. **`sync()`** - Main sync functionality
2. **`profile()`** - List, activate, show profiles (simplified)
3. **`validate_content_security()`** - Security validation
4. **`clear_cache()`** - Cache management

### Diagnostic Tools (1)
5. **`diagnose_config()`** - Configuration diagnostics

## Removal Plan

```python
# Remove these @mcp.tool() functions:
- ide() - entire tool (~50 lines)
- mcp_servers() - entire tool (~70 lines)

# Simplify profile():
- Remove "cleanup" action (or rewrite for V2)
- Remove "deactivate" action (or rewrite for V2)

# Fix duplicates:
- Remove second validate_content_security() (~45 lines)
- Remove second clear_cache() (~40 lines)
```

## Lines Saved

| Item | Lines | Status |
|------|-------|--------|
| ide() tool | ~50 | Remove |
| mcp_servers() tool | ~70 | Remove |
| Duplicate validate_content_security() | ~45 | Remove |
| Duplicate clear_cache() | ~40 | Remove |
| profile() cleanup action | ~45 | Remove |
| profile() deactivate action | ~86 | Remove |
| **Total** | **~336 lines** | - |

## Testing Checklist

After cleanup:
- [ ] `sync(action='list_ides')` works
- [ ] `sync(action='full', workspace_path='...', ide_choice=1)` works
- [ ] `profile(action='list')` works
- [ ] `profile(action='activate', profile_name='...')` works
- [ ] `validate_content_security()` works (no duplicate)
- [ ] `clear_cache()` works (no duplicate)
- [ ] `diagnose_config()` works
- [ ] No warnings about duplicate tools
- [ ] `uv run python -c "import main"` succeeds

## Summary

**Before**: 8+ tools (with duplicates and V1 cruft)
**After**: 5 clean V2 tools

**Reduction**: ~336 lines of tool code
**Benefits**:
- Simpler API surface
- No V1/V2 confusion  
- Clearer documentation
- Faster loading
