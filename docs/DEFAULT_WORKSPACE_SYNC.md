# Default Workspace (Local) Sync Behavior

## Overview

As of the latest version, the MCP server **defaults to workspace (local) sync** instead of falling back to global sync. This ensures rules and workflows are placed in your project's local IDE directories (`.windsurf/`, `.cursor/`, `.vscode/`) rather than global user directories.

## What Changed

### Before
- Default scope was `"auto"`
- Would fall back to global sync if workspace couldn't be detected
- Rules might end up in `~/.windsurf/`, `~/.cursor/`, etc. instead of your project

### After
- Default scope is `"workspace"` (local)
- Requires explicit workspace path or auto-detection
- Errors if workspace cannot be determined (instead of silently falling back to global)
- Rules go to project-local directories: `.windsurf/`, `.cursor/`, `.vscode/`

## Sync Scope Options

### `workspace` (DEFAULT)
Syncs only to your project's local IDE directories.

**Files go to:**
- `.windsurf/` for Windsurf
- `.cursor/rules/` for Cursor  
- `.vscode/rules/` for VS Code

**Usage:**
```python
sync(action='full', workspace_path='/absolute/path/to/project')
# or
sync(action='full', workspace_path='/absolute/path/to/project', scope='workspace')
```

### `global`
Syncs only to global user directories.

**Files go to:**
- `~/windsurf-instructions/{profile}/` for Windsurf
- `~/cursor-instructions/{profile}/` for Cursor
- `~/vscode-instructions/{profile}/` for VS Code

**Usage:**
```python
sync(action='full', scope='global')
```

### `both`
Syncs to both local workspace and global directories.

**Usage:**
```python
sync(action='full', workspace_path='/absolute/path/to/project', scope='both')
```

### `auto`
Legacy behavior - tries to detect workspace, falls back to global if not found.

**Usage:**
```python
sync(action='full', scope='auto')
```

## Why This Change?

### Benefits of Local (Workspace) Sync

1. **Project-Specific Rules**: Each project gets its own set of rules
2. **Version Control**: Local rules can be committed to git (if desired)
3. **Team Consistency**: All team members see the same rules in the same project
4. **No Global Pollution**: Global directories stay clean
5. **Explicit Behavior**: You always know where your rules are

### When to Use Global Sync

Use `scope='global'` when:
- You want rules to apply to ALL projects
- You're setting up personal defaults
- You don't want rules in version control
- You work on many small projects

## IDE-Specific Considerations

### Windsurf
- **Local rules**: `.windsurf/` in project root
- **Global rules**: `~/windsurf-instructions/{profile}/`
- **MCP config**: ALWAYS global at `~/.codeium/windsurf/mcp_config.json`
  - Windsurf doesn't support local MCP configs
  - MCP config is automatically managed globally

### Cursor
- **Local rules**: `.cursor/rules/` in project root
- **Global rules**: `~/cursor-instructions/{profile}/`
- **MCP config**: Can be local (`.cursor/mcp.json`) or global

### VS Code
- **Local rules**: `.vscode/rules/` in project root
- **Global rules**: `~/vscode-instructions/{profile}/`
- **MCP config**: Can be local (`.vscode/mcp.json`) or global

## Migration Guide

If you were relying on the old `auto` behavior:

### Option 1: Update Your Calls (Recommended)
Always provide `workspace_path`:
```python
# Before
sync(action='full')

# After
sync(action='full', workspace_path='/absolute/path/to/project')
```

### Option 2: Use Global Scope
If you want global sync:
```python
sync(action='full', scope='global')
```

### Option 3: Use Auto Scope
To keep old behavior:
```python
sync(action='full', scope='auto')
```

## Error Messages

### "No workspace provided or detected"
**Cause**: Default is workspace sync, but no workspace path was provided and auto-detection failed.

**Fix:**
```python
# Provide explicit path
sync(action='full', workspace_path='/absolute/path/to/project')

# OR use global sync
sync(action='full', scope='global')

# OR use auto scope (legacy)
sync(action='full', scope='auto')
```

## Best Practices

### ✅ Recommended Approach
```python
# Always be explicit about where you're syncing
sync(
    action='full',
    workspace_path='/absolute/path/to/your/project',
    scope='workspace'  # Optional since it's the default
)
```

### ✅ For Global Rules
```python
# Explicitly request global sync
sync(
    action='full',
    scope='global'
)
```

### ❌ Avoid
```python
# Don't rely on auto-detection without explicit path
sync(action='full')  # Will error if workspace not detected

# Don't use 'auto' scope in new code (legacy behavior)
sync(action='full', scope='auto')
```

## Workspace Detection

The MCP server auto-detects workspace by:

1. **Environment variables**: `VSCODE_CWD`, `CURSOR_WORKSPACE`, etc.
2. **Directory markers**: Looking for `.windsurf/`, `.cursor/`, `.vscode/`, `.git/`
3. **Walking up**: From current directory to root

If detection fails, you'll get a clear error message asking for `workspace_path`.

## Summary

- **Default changed**: `auto` → `workspace` (local)
- **Always provide**: `workspace_path` for workspace sync
- **Explicit errors**: Instead of silent fallback to global
- **MCP configs**: Windsurf MCP is always global (IDE limitation)
- **Rules/Workflows**: Default to local project directories
- **Use `scope='global'`**: When you want global sync
