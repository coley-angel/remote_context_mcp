# Dynamic Workspace Detection

## Overview

The team-config MCP server now dynamically detects the workspace root directory where IDE configuration files (.windsurf/, .cursor/, .vscode/) should be placed. This ensures that files are created in the correct location regardless of where the MCP server process is started.

## How It Works

### Detection Strategy

The server walks up the directory tree from the current working directory, looking for:

1. **IDE-specific markers** (prioritized by detected IDE):
   - `.windsurf/` directory (Windsurf/Cascade)
   - `.cursor/` directory (Cursor)
   - `.vscode/` directory (VS Code)

2. **Git repository marker** (fallback):
   - `.git/` directory

3. **Current working directory** (final fallback)

### Detection Flow

```
1. Check WORKSPACE_DIR environment variable (if set)
   ↓
2. Detect which IDE is running (Windsurf/Cursor/VS Code)
   ↓
3. Walk up directory tree looking for IDE markers
   ↓
4. Fall back to .git/ directory
   ↓
5. Fall back to current working directory
```

## Functions

### `detect_workspace_root(ide_type, start_path)`

Searches for workspace root by walking up the directory tree.

**Parameters:**
- `ide_type` - IDE to search for (optional, searches all if None)
- `start_path` - Starting path (optional, uses cwd if None)

**Returns:**
- Path to workspace root, or None if not found

**Example:**
```python
# Detect for specific IDE
workspace = detect_workspace_root(IDEType.WINDSURF)

# Detect for any IDE
workspace = detect_workspace_root()
```

### `get_workspace_dir(ide_type)`

Gets the workspace directory with full fallback chain.

**Parameters:**
- `ide_type` - IDE type for targeted detection (optional)

**Returns:**
- Path to workspace directory (always returns a valid path)

**Priority:**
1. `WORKSPACE_DIR` environment variable
2. Dynamic detection via `detect_workspace_root()`
3. Current working directory

**Example:**
```python
current_ide = get_current_ide()
workspace = get_workspace_dir(current_ide)
```

## Usage in Tools

All MCP tools now use dynamic workspace detection:

### Before (Static)
```python
async def sync_team_config(...):
    # Used static WORKSPACE_DIR
    workspace = WORKSPACE_DIR
```

### After (Dynamic)
```python
async def sync_team_config(...):
    # Detects workspace per-request
    current_ide = get_current_ide()
    workspace = get_workspace_dir(current_ide)
```

## IDE-Specific Behavior

### Windsurf
- **Global config**: `~/.codeium/windsurf/mcp_config.json`
- **Workspace rules**: Detected workspace + `.windsurf/rules/`
- Uses `None` for MCP server operations (global)
- Uses detected workspace for rules/workflows

### Cursor
- **Workspace config**: Detected workspace + `.cursor/mcp.json`
- **Workspace rules**: Detected workspace + `.cursor/rules/`
- Uses detected workspace for all operations

### VS Code
- **Workspace config**: Detected workspace + `.vscode/mcp.json`
- **Workspace rules**: Detected workspace + `.vscode/rules/`
- Uses detected workspace for all operations

## Environment Variable Override

You can still manually specify the workspace:

```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "env": {
        "WORKSPACE_DIR": "/path/to/your/project"
      }
    }
  }
}
```

This takes precedence over dynamic detection.

## Examples

### Example 1: Windsurf Project

```
/Users/you/projects/my-app/
├── .windsurf/          ← Detected as workspace root
│   └── rules/
├── src/
└── package.json
```

**Process CWD**: `/Users/you/projects/my-app/src`  
**Detected Workspace**: `/Users/you/projects/my-app`  
**Rules Path**: `/Users/you/projects/my-app/.windsurf/rules/`

### Example 2: Git Repository (No IDE Folder)

```
/Users/you/projects/my-app/
├── .git/               ← Detected as workspace root
├── src/
└── package.json
```

**Process CWD**: `/Users/you/projects/my-app/src`  
**Detected Workspace**: `/Users/you/projects/my-app`  
**Creates**: `/Users/you/projects/my-app/.windsurf/` (or .cursor/, .vscode/)

### Example 3: Multi-IDE Repository

```
/Users/you/projects/my-app/
├── .git/
├── .vscode/            ← VS Code marker
├── .cursor/            ← Cursor marker
├── .windsurf/          ← Windsurf marker
└── src/
```

**Windsurf User**: Detects `/Users/you/projects/my-app` via `.windsurf/`  
**Cursor User**: Detects `/Users/you/projects/my-app` via `.cursor/`  
**VS Code User**: Detects `/Users/you/projects/my-app` via `.vscode/`

## Logging

The server logs workspace detection:

```
INFO - Found workspace root at /Users/you/projects/my-app (marker: .windsurf)
INFO - Using workspace from WORKSPACE_DIR: /custom/path
INFO - Using fallback workspace: /Users/you/current/dir
```

## Benefits

1. **Automatic Detection**: No manual configuration needed
2. **IDE-Aware**: Prioritizes the IDE you're using
3. **Git-Compatible**: Works with git repositories
4. **Fallback Safe**: Always finds a valid workspace
5. **Override Available**: Can still set WORKSPACE_DIR manually
6. **Per-Request**: Detects fresh for each operation

## Implementation Details

### Search Depth
- Maximum 10 levels up from starting directory
- Prevents infinite loops and excessive searching

### Caching
- Detection happens per-request (no global cache)
- Ensures accuracy if workspace changes

### Thread Safety
- No global state for workspace
- Each request gets independent detection

## Troubleshooting

### Issue: Wrong workspace detected

**Solution**: Set WORKSPACE_DIR environment variable explicitly

```json
"env": {
  "WORKSPACE_DIR": "/correct/path"
}
```

### Issue: No workspace detected

**Check:**
1. Is there a `.windsurf/`, `.cursor/`, `.vscode/`, or `.git/` directory?
2. Is the server started from within your project?
3. Check server logs for detection messages

**Workaround**: Set WORKSPACE_DIR manually

### Issue: IDE-specific folder not found

**Behavior**: Server will create the IDE folder at detected workspace root

Example: If using Windsurf and only `.git/` exists, server creates `.windsurf/rules/`

## Migration from Static WORKSPACE_DIR

### Before
```python
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", os.getcwd()))
# Used everywhere
```

### After
```python
WORKSPACE_DIR = None  # Deprecated static value
# Each function calls get_workspace_dir()
workspace = get_workspace_dir(current_ide)
```

### Compatibility
- Old `WORKSPACE_DIR` env var still works
- Takes priority over detection
- No breaking changes for existing setups

## Future Enhancements

Potential improvements:
- Cache detection per IDE session
- Support for monorepo detection
- Custom marker file support (.workspace-root)
- Language-specific markers (pyproject.toml, package.json)
