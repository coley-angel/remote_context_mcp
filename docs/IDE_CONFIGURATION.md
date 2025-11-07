# IDE Configuration Guide

## Overview

The MCP server now supports **data-driven IDE configuration**, allowing you to define custom IDEs or override default paths directly in your `team_config.yaml` file. This eliminates the need to modify Python code when adding support for new IDEs.

## Default IDE Support

The server comes with built-in support for three popular IDEs:

- **VS Code**
- **Cursor**
- **Windsurf**

These IDEs work out of the box with sensible defaults for macOS, Windows, and Linux.

## Architecture

### Key Components

1. **`schemas.py`**
   - `IDEConfig`: Main IDE configuration dataclass
   - `IDEPathConfig`: Platform-specific path configuration
   - `get_default_ide_configs()`: Returns default IDE templates

2. **`ide_adapter.py`**
   - Compatibility layer between config and IDE manager
   - Loads IDE configs from team config
   - Provides name-to-enum mappings for backward compatibility

3. **`ide_manager.py`**
   - Manages IDE operations (read/write settings, sync rules, etc.)
   - Uses config-based IDE definitions
   - Falls back to defaults if config doesn't define IDEs

## Defining Custom IDEs

### Basic Structure

```yaml
ide_configs:
  my_ide:
    name: "my_ide"                    # Unique identifier
    display_name: "My Custom IDE"     # Human-readable name
    instructions_key: "myide.instructionsFilesLocations"  # Settings key
    supports_mcp: true                # Whether IDE supports MCP servers
    
    # Platform-specific paths
    darwin_paths:                     # macOS
      settings_path: "~/.myide/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
    
    win32_paths:                      # Windows
      settings_path: "~/AppData/Roaming/MyIDE/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
    
    linux_paths:                      # Linux
      settings_path: "~/.config/myide/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
```

### Path Configuration Fields

- **`settings_path`**: Location of IDE settings file (JSON)
- **`mcp_config_path`**: Location of MCP server configuration
- **`rules_path`**: Directory where rule files should be placed

Paths support:
- `~` for home directory expansion
- Relative paths (for workspace-level configs)
- Absolute paths

### Platform-Specific Paths

Define paths for each platform you need to support:

- **`darwin_paths`**: macOS
- **`win32_paths`**: Windows
- **`linux_paths`**: Linux

If a platform isn't defined, the server won't sync to that platform.

## Overriding Default IDEs

You can override default IDE configurations:

```yaml
ide_configs:
  # Override Windsurf to use different paths
  windsurf:
    name: "windsurf"
    display_name: "Windsurf (Custom)"
    instructions_key: "windsurf.instructionsFilesLocations"
    supports_mcp: true
    darwin_paths:
      settings_path: "~/custom/path/windsurf/settings.json"
      mcp_config_path: "~/custom/path/windsurf/mcp.json"
      rules_path: "~/custom/path/windsurf/rules"
```

The config values will merge with defaults, with your config taking precedence.

## Example: Adding Zed Editor Support

```yaml
ide_configs:
  zed:
    name: "zed"
    display_name: "Zed Editor"
    instructions_key: "zed.ai.instructionsPath"
    supports_mcp: true
    
    darwin_paths:
      settings_path: "~/.config/zed/settings.json"
      mcp_config_path: ".zed/mcp.json"
      rules_path: ".zed/rules"
    
    linux_paths:
      settings_path: "~/.config/zed/settings.json"
      mcp_config_path: ".zed/mcp.json"
      rules_path: ".zed/rules"

supported_ides:
  - "vscode"
  - "cursor"
  - "windsurf"
  - "zed"  # Add to supported list
```

## Workspace vs Global Paths

### Global Configuration
Used by IDEs that store rules at the user/system level:

```yaml
darwin_paths:
  rules_path: "~/.myide/rules"  # Global location
```

### Workspace Configuration
Used by IDEs that store rules at the project level:

```yaml
darwin_paths:
  rules_path: ".myide/rules"  # Relative to workspace
```

## Supported IDEs List

Update the `supported_ides` list to control which IDEs are actively managed:

```yaml
supported_ides:
  - "vscode"
  - "cursor"
  - "windsurf"
  - "my_custom_ide"
```

Only IDEs in this list will be synced to when they're detected as installed.

## Detection and Installation

The server:
1. Checks which IDEs are installed by looking for their settings directories
2. Only syncs to IDEs that are both **supported** and **installed**
3. Prompts the user to specify IDE if detection fails

## Backward Compatibility

The system maintains backward compatibility:
- If no `ide_configs` defined, defaults are used
- Existing code using `IDEType` enum still works
- `ide_adapter.py` provides translation layer between names and enum

## Benefits

✅ **No Code Changes**: Add IDE support via config  
✅ **Team Flexibility**: Different teams can use different IDEs  
✅ **Path Customization**: Override paths for non-standard installations  
✅ **Platform Support**: Define paths for each OS separately  
✅ **Easy Maintenance**: Update paths without redeploying  

## Troubleshooting

### IDE Not Detected

Check that the settings path exists:
```bash
ls -la ~/.myide/settings.json  # macOS/Linux
dir %USERPROFILE%\AppData\Roaming\MyIDE\settings.json  # Windows
```

### Rules Not Syncing

1. Verify the `rules_path` in your config
2. Check that frontmatter exists in rule files
3. Ensure IDE is in `supported_ides` list
4. Use `get_current_ide_info` MCP tool to verify paths

### Custom IDE Not Working

1. Ensure `name` field matches key in `ide_configs`
2. Define paths for your platform (`darwin`, `win32`, or `linux`)
3. Add IDE name to `supported_ides` list
4. Set IDE explicitly with `set_ide` MCP tool

## Migration from Hardcoded Paths

Old approach (hardcoded in Python):
```python
IDE_CONFIGS = {
    IDEType.MYIDE: IDEConfig(...)
}
```

New approach (in config):
```yaml
ide_configs:
  myide:
    name: "myide"
    ...
```

The adapter layer ensures existing code continues to work while new functionality is config-driven.
