# Scope Feature: Global vs Workspace Configurations

## Overview

The team-config MCP server now supports **scope** control, allowing you to specify whether configurations should be applied **globally** (user-level) or to a **specific workspace** (project-level).

## Problem Solved

When running via `uvx` globally, the server needs to know:
- Should rules/workflows be placed in global user directories (~/.windsurf/)?
- Should they be placed in the current project workspace (.windsurf/)?
- Should both locations be updated?

The **scope** parameter gives you explicit control over this behavior.

## Scope Options

### `scope="auto"` (Default)
**Smart detection with fallback**

- First tries to detect a workspace using:
  - IDE environment variables (`VSCODE_CWD`, etc.)
  - Directory markers (`.windsurf/`, `.cursor/`, `.vscode/`, `.git/`)
- If workspace found → syncs to workspace
- If no workspace found → syncs to global
- **Best for:** Running from within a project

```python
sync(action="full")  # Auto-detects
```

### `scope="workspace"`
**Workspace-only mode**

- **Requires** a detectable workspace
- Only syncs to current project directories
- Returns error if no workspace detected
- **Best for:** Project-specific configurations

```python
sync(action="full", scope="workspace")
```

**Result:**
```
✓ /path/to/project/.windsurf/rules/
✓ /path/to/project/.cursor/rules/
✓ /path/to/project/.vscode/rules/
✗ Global directories (skipped)
```

### `scope="global"`
**Global-only mode**

- Ignores any detected workspace
- Only syncs to user home directories
- **Best for:** User-wide defaults and templates

```python
sync(action="full", scope="global")
```

**Result:**
```
✓ ~/windsurf-instructions/
✓ ~/cursor-instructions/
✓ ~/vscode-instructions/
✗ Workspace directories (skipped)
```

### `scope="both"`
**Dual-sync mode**

- Syncs to both global AND workspace
- Useful for maintaining consistency
- **Best for:** Setting up both personal defaults and project rules

```python
sync(action="full", scope="both")
```

**Result:**
```
✓ ~/windsurf-instructions/ (global)
✓ /path/to/project/.windsurf/rules/ (workspace)
✓ Both cursor and vscode locations
```

## File Locations

### Global Locations
User-level defaults, loaded for all projects:

```
~/.windsurf/
  └── (no rules here - Windsurf uses global settings)

~/windsurf-instructions/{profile}/
  ├── rules/
  ├── workflows/
  └── prompts/

~/cursor-instructions/{profile}/
  ├── rules/
  ├── workflows/
  └── prompts/

~/vscode-instructions/{profile}/
  ├── rules/
  ├── workflows/
  └── prompts/
```

### Workspace Locations
Project-specific, only for current workspace:

```
{workspace}/.windsurf/
  ├── rules/
  ├── workflows/
  └── prompts/

{workspace}/.cursor/
  ├── rules/
  ├── workflows/
  └── prompts/

{workspace}/.vscode/
  ├── rules/
  ├── workflows/
  └── prompts/
```

## Detection Methods

The server detects workspace using multiple strategies:

### 1. IDE Environment Variables
```bash
VSCODE_CWD           # VS Code workspace directory
VSCODE_WORKSPACE     # VS Code workspace file
CURSOR_WORKSPACE     # Cursor workspace (if available)
WINDSURF_WORKSPACE   # Windsurf workspace (if available)
```

### 2. Directory Markers
Walks up from current directory looking for:
- `.windsurf/` directory
- `.cursor/` directory
- `.vscode/` directory
- `.git/` directory

### 3. Manual Override
Set via environment variable:
```json
{
  "env": {
    "WORKSPACE_DIR": "/path/to/your/project"
  }
}
```

## Use Cases

### Use Case 1: Running Globally via uvx

**Scenario:** MCP server installed via `uvx` for all projects

```json
{
  "mcpServers": {
    "team-config": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/...", "mcp-team-config"],
      "env": { "..." }
    }
  }
}
```

**Options:**
```python
# Auto-detect (smart)
sync(action="full", scope="auto")

# Force workspace (fails if not in project)
sync(action="full", scope="workspace")

# Force global (always works)
sync(action="full", scope="global")
```

### Use Case 2: Project-Specific Rules

**Scenario:** Team project with custom rules

```bash
cd /path/to/team-project
```

```python
# Sync team rules to project only
sync(action="full", scope="workspace")
```

**Result:** Rules placed in `/path/to/team-project/.windsurf/rules/`

### Use Case 3: Personal Defaults

**Scenario:** Set up your personal defaults for all projects

```python
# Sync to global directories
sync(action="full", scope="global", profile_name="personal")
```

**Result:** Rules placed in `~/windsurf-instructions/personal/`

### Use Case 4: Hybrid Setup

**Scenario:** Global templates + project overrides

```python
# Step 1: Set up global defaults
sync(action="full", scope="global", profile_name="defaults")

# Step 2: Add project-specific rules
cd /path/to/project
sync(action="full", scope="workspace", profile_name="team-project")
```

**Result:**
- Global: `~/windsurf-instructions/defaults/`
- Project: `/path/to/project/.windsurf/rules/`

### Use Case 5: Sync Everything

**Scenario:** Mirror configuration everywhere

```python
# Update both global and workspace
sync(action="full", scope="both")
```

## Response Format

All sync operations return scope information:

```json
{
  "success": true,
  "profile": "default",
  "scope": "workspace",
  "workspace_path": "/path/to/project",
  "synced_ides": ["windsurf", "cursor", "vscode"],
  "rules_synced": 5,
  "workflows_synced": 3
}
```

**Scope values in response:**
- `"workspace"` - Synced to detected workspace
- `"global"` - Synced to global directories
- `"both"` - Synced to both locations

## MCP Server Configurations

MCP servers are handled differently based on IDE:

### Windsurf
- **Global MCP config:** `~/.codeium/windsurf/mcp_config.json`
- **Workspace rules:** Respects scope parameter
- **MCP servers always global** (Windsurf design)

### Cursor
- **Workspace MCP config:** `{workspace}/.cursor/mcp.json`
- **Workspace rules:** Respects scope parameter
- **Both respect scope**

### VS Code
- **Workspace MCP config:** `{workspace}/.vscode/mcp.json`
- **Workspace rules:** Respects scope parameter
- **Both respect scope**

## Error Handling

### No Workspace Detected (scope="workspace")

```json
{
  "success": false,
  "error": "No workspace detected. Use scope='global' or scope='auto' instead.",
  "hint": "Ensure you're in a git repository or have .windsurf/, .cursor/, or .vscode/ directory"
}
```

**Solution:**
- Use `scope="auto"` or `scope="global"`
- Ensure you're in a project directory
- Initialize git: `git init`
- Create IDE directory: `mkdir .windsurf`

### Workspace Detection Failed (scope="auto")

Falls back to global automatically:

```json
{
  "success": true,
  "scope": "global",
  "message": "No workspace detected, using global scope"
}
```

## Examples

### Example 1: First-time Setup

```python
# Set up global defaults for all projects
sync(action="full", scope="global", profile_name="defaults")
```

### Example 2: Join Team Project

```python
# Clone repo
cd /path/to/team-repo

# Sync team rules to workspace
sync(action="full", scope="workspace", profile_name="team-rules")
```

### Example 3: Multi-Project Consistency

```python
# Sync to both for maximum consistency
sync(action="full", scope="both", profile_name="standards")
```

### Example 4: Quick Auto-Detection

```python
# Let it figure out what to do
sync(action="full")  # Uses scope="auto" by default
```

## Best Practices

### ✅ Do

- Use `scope="auto"` for most cases (smart detection)
- Use `scope="workspace"` when in a project directory
- Use `scope="global"` for personal templates
- Use `scope="both"` when setting up new machines

### ❌ Don't

- Don't use `scope="workspace"` when running globally
- Don't assume workspace detection always works
- Don't mix scopes without understanding the implications

## Troubleshooting

### Issue: Scope returns "global" but I'm in a project

**Check:**
1. Is there a `.git/`, `.windsurf/`, `.cursor/`, or `.vscode/` directory?
2. Are you running from the project root or subdirectory?
3. Check server logs for detection messages

**Solution:**
```bash
# Create IDE directory
mkdir .windsurf

# Or initialize git
git init

# Then sync again
sync(action="full", scope="workspace")
```

### Issue: Rules appear in wrong location

**Check:** What scope was used in the response

**Solution:**
```python
# Explicitly set the scope
sync(action="full", scope="workspace")  # Force workspace
sync(action="full", scope="global")     # Force global
```

### Issue: Workspace not detected via uvx

**Problem:** IDE environment variables may not be set when running via uvx

**Solution:** Use manual override
```json
{
  "env": {
    "WORKSPACE_DIR": "/path/to/project"
  }
}
```

## Migration from Old Behavior

### Before (No Scope Parameter)
```python
sync(action="full")  # Always used detected workspace or cwd
```

### After (With Scope Parameter)
```python
sync(action="full")                    # Auto-detect (smart fallback)
sync(action="full", scope="workspace") # Explicit workspace
sync(action="full", scope="global")    # Explicit global
```

**Backward Compatible:** Default `scope="auto"` maintains similar behavior with smarter fallback.

## Summary

The **scope** feature gives you precise control over where team configurations are applied:

- **`auto`** - Smart detection with fallback (recommended)
- **`workspace`** - Project-specific (requires workspace)
- **`global`** - User-wide defaults
- **`both`** - Maximum coverage

This solves the "where do files go?" problem when running the MCP server globally via uvx, while still supporting workspace-specific configurations.
