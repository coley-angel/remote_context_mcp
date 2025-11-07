# Quick Start: Using Team Config MCP in Windsurf

## ✅ What Just Got Added

Your MCP server now **automatically detects which IDE you're using** and saves files to the correct location!

## 🎯 IDE-Specific Directories

| IDE | Files Save To |
|-----|---------------|
| **Windsurf** | `~/windsurf-instructions/{profile}/` |
| **VS Code** | `~/vscode-instructions/{profile}/` |
| **Cursor** | `~/cursor-instructions/{profile}/` |

## 🚀 Try It Now in Windsurf Cascade

### 1. Check Your Current IDE
```
get_current_ide_info()
```

You should see:
```json
{
  "current_ide": "windsurf",
  "detected_ide": "windsurf",
  "instructions_dir": "/Users/coangel/windsurf-instructions/default"
}
```

### 2. List All Installed IDEs
```
list_installed_ides()
```

Shows which IDEs are detected and where files will go for each.

### 3. Sync Your Configuration
```
sync_team_config()
```

This will:
- ✅ Auto-detect you're using Windsurf
- ✅ Download your team's configurations
- ✅ Save to `~/windsurf-instructions/default/`
- ✅ Update Windsurf settings automatically

### 4. Override IDE Detection (Optional)
```
# If you want to use a different IDE's directory:
set_ide(ide_name="vscode")

# Then sync again:
sync_team_config()
```

## 📋 New MCP Tools

### `get_current_ide_info()`
Shows which IDE is detected and where files will be saved.

### `list_installed_ides()`
Lists all detected IDEs with their directories and settings paths.

### `set_ide(ide_name)`
Manually set which IDE to use. Options: "vscode", "cursor", "windsurf"

### `sync_team_config()`
Now automatically uses the correct IDE directory!

## 🎨 How It Works

1. **Auto-Detection**
   - Checks environment variables (VSCODE_PID, CURSOR_PID, etc.)
   - Checks which IDE settings directories exist
   - Falls back to VS Code if can't determine

2. **Smart Saving**
   - Uses IDE-specific directory for your current IDE
   - Creates subdirectories: instructions/, rules/, workflows/, prompts/
   - Updates IDE settings to reference the new location

3. **Multi-IDE Support**
   - Can manage multiple IDEs on same machine
   - Each gets its own directory
   - Switch between them with `set_ide()`

## 🧪 Test Results

✅ **All 6 tests passed:**
- Configuration System ✅
- Security Validation ✅
- IDE Manager ✅
- **IDE Detection ✅** (NEW!)
- Repository Manager ✅
- Config Loader ✅

**Auto-detected:** VS Code (currently running tests)
**Supports:** VS Code, Windsurf (detected on your system)
**Directory Structure:** Working correctly for all IDEs

## 🔥 Example Workflow

```bash
# In Windsurf Cascade:

# 1. Check what's detected
get_current_ide_info()
# → Shows: "current_ide": "windsurf"

# 2. Sync your team config
sync_team_config()
# → Downloads to ~/windsurf-instructions/default/

# 3. Verify it worked
list_installed_ides()
# → Shows Windsurf as current with files saved

# 4. Check a different IDE's location
set_ide(ide_name="vscode")
get_current_ide_info()
# → Shows: "current_ide": "vscode"
# → Shows: ~/vscode-instructions/default/
```

## 💡 Pro Tips

1. **Let it auto-detect** - It detected VS Code and Windsurf correctly!
2. **No configuration needed** - Just run `sync_team_config()`
3. **Verify with `get_current_ide_info()`** - Shows exactly what will happen
4. **Switch anytime** - Use `set_ide()` to change between IDEs

## 📚 More Info

- Full documentation: `IDE_DETECTION.md`
- Complete guide: `README_NEW.md`
- Test the server: `uv run python test_server.py`

---

**You're all set! The server now intelligently handles each IDE's requirements.** 🎉
