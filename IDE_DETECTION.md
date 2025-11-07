# IDE Detection and Configuration

The Team Configuration MCP Server now automatically detects which IDE you're using and saves files to the appropriate location.

## 🎯 How It Works

### Automatic Detection

The server tries to detect your IDE using:
1. **Environment variables** (VSCODE_PID, CURSOR_PID, CODEIUM_PID)
2. **Settings directories** (checks which IDE's settings exist)
3. **Fallback** to VS Code if detection fails

### IDE-Specific Directories

Files are saved to IDE-specific locations:

| IDE | Instructions Directory |
|-----|----------------------|
| **VS Code** | `~/vscode-instructions/{profile}/` |
| **Cursor** | `~/cursor-instructions/{profile}/` |
| **Windsurf** | `~/windsurf-instructions/{profile}/` |

## 📋 MCP Tools for IDE Management

### 1. Check Current IDE

```
get_current_ide_info()
```

**Returns:**
```json
{
  "success": true,
  "current_ide": "windsurf",
  "detected_ide": "windsurf",
  "auto_detected": true,
  "settings_path": "/Users/you/.windsurf/settings.json",
  "instructions_dir": "/Users/you/windsurf-instructions/default",
  "instructions_dirs": {
    "vscode": "/Users/you/vscode-instructions/default",
    "cursor": "/Users/you/cursor-instructions/default",
    "windsurf": "/Users/you/windsurf-instructions/default"
  }
}
```

### 2. List All IDEs

```
list_installed_ides()
```

**Returns:**
```json
{
  "success": true,
  "current_ide": "windsurf",
  "detected_ide": "windsurf",
  "installed_ides": ["vscode", "windsurf"],
  "ide_details": {
    "vscode": {
      "installed": true,
      "is_current": false,
      "is_detected": false,
      "settings_path": "/Users/you/Library/Application Support/Code/User/settings.json",
      "settings_exists": true,
      "instructions_dir": "/Users/you/vscode-instructions/default"
    },
    "windsurf": {
      "installed": true,
      "is_current": true,
      "is_detected": true,
      "settings_path": "/Users/you/.windsurf/settings.json",
      "settings_exists": true,
      "instructions_dir": "/Users/you/windsurf-instructions/default"
    }
  }
}
```

### 3. Set IDE Explicitly

If auto-detection doesn't work or you want to override:

```
set_ide(ide_name="windsurf")
```

**Options:** `vscode`, `cursor`, `windsurf`, `cascade` (alias for windsurf)

**Returns:**
```json
{
  "success": true,
  "message": "IDE set to windsurf",
  "current_ide": "windsurf",
  "instructions_dir": "/Users/you/windsurf-instructions/default"
}
```

## 🚀 Usage Examples

### Example 1: Check Which IDE You're Using

```
# In Windsurf Cascade or other IDE chat:
get_current_ide_info()
```

This will tell you:
- Which IDE was detected
- Where files will be saved
- Settings paths for configuration

### Example 2: Override IDE Detection

```
# If you're using VS Code but want Windsurf-style directories:
set_ide(ide_name="vscode")

# Now sync will save to ~/vscode-instructions/
sync_team_config()
```

### Example 3: Full Workflow

```
# 1. Check current setup
get_current_ide_info()

# 2. Optionally set IDE explicitly
set_ide(ide_name="windsurf")

# 3. Sync your team configuration
sync_team_config()

# 4. Verify where files were saved
list_installed_ides()
```

## 🔧 Configuration Behavior

### When You Run `sync_team_config()`

1. **Detects IDE** (or uses your explicitly set IDE)
2. **Creates IDE-specific directory** (e.g., `~/windsurf-instructions/default/`)
3. **Downloads content** (instructions, rules, workflows, prompts)
4. **Updates IDE settings** to point to the new directory
5. **Syncs to all installed IDEs** (if `sync_to_ides=true`)

### Directory Structure

```
~/vscode-instructions/
├── default/
│   ├── instructions/
│   │   ├── instruction_0.md
│   │   └── instruction_1.md
│   ├── rules/
│   │   └── rule_0.md
│   └── workflows/
│       └── workflow_0.md
└── corporate/
    └── ...

~/cursor-instructions/
└── default/
    └── ...

~/windsurf-instructions/
└── default/
    └── ...
```

## 📝 Settings Updates

The server automatically updates your IDE settings to reference the correct directories.

### VS Code
Updates: `~/Library/Application Support/Code/User/settings.json`
```json
{
  "chat.instructionsFilesLocations": {
    "/Users/you/vscode-instructions/default": true
  }
}
```

### Cursor
Updates: `~/Library/Application Support/Cursor/User/settings.json`
```json
{
  "cursor.instructionsFilesLocations": {
    "/Users/you/cursor-instructions/default": true
  }
}
```

### Windsurf
Updates: `~/.windsurf/settings.json`
```json
{
  "windsurf.instructionsFilesLocations": {
    "/Users/you/windsurf-instructions/default": true
  }
}
```

## 🐛 Troubleshooting

### IDE Not Detected

```
# Check what's detected:
get_current_ide_info()

# Manually set it:
set_ide(ide_name="windsurf")
```

### Files Going to Wrong Directory

```
# Verify current IDE:
get_current_ide_info()

# Change it:
set_ide(ide_name="cursor")

# Then sync again:
sync_team_config()
```

### Multiple IDEs on Same Machine

The server can manage all IDEs simultaneously:
- Each IDE gets its own directory
- Settings are updated independently
- You can switch between IDEs with `set_ide()`

## 💡 Pro Tips

1. **Let it auto-detect**: The detection usually works correctly
2. **Use `get_current_ide_info()` first**: See what the server detected
3. **Override when needed**: Use `set_ide()` for specific workflows
4. **Check after sync**: Use `list_installed_ides()` to see where files went

---

**Questions?** The IDE detection happens automatically when you run `sync_team_config()` - no configuration needed!
