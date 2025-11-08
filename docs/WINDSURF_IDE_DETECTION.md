# Windsurf IDE Detection Troubleshooting

## Issue

When using the Team Config MCP server in Windsurf, it may create `.vscode` directories instead of `.windsurf` directories if the IDE is not properly detected.

## Root Cause

The MCP server detects the current IDE by checking environment variables set by the IDE. If Windsurf's environment variables are not present, it may fall back to detecting VS Code instead.

## How IDE Detection Works

The MCP server checks environment variables in this order:

1. **Windsurf** (highest priority):
   - `CODEIUM_PID` - Windsurf uses Codeium infrastructure
   - `WINDSURF_PID` - Windsurf-specific process ID
   - `TERM_PROGRAM` contains "windsurf"

2. **Cursor**:
   - `CURSOR_PID` - Cursor process ID
   - `CURSOR_USER_DATA_DIR` - Cursor data directory

3. **VS Code** (lowest priority):
   - `VSCODE_PID` - VS Code process ID
   - `VSCODE_CWD` - VS Code current working directory
   - `VSCODE_IPC_HOOK` - VS Code IPC hook

## Solution 1: Verify Environment Variables

Run the test script to see what environment variables are present:

```bash
cd /path/to/remote_context_mcp
python test_ide_detection.py
```

Expected output for Windsurf:
```
Environment Variables:
--------------------------------------------------------------------------------
  CODEIUM_PID               = 12345
  TERM_PROGRAM              = windsurf
  ...

Detected IDE:
--------------------------------------------------------------------------------
  ✓ WINDSURF (via CODEIUM_PID/WINDSURF_PID)
```

## Solution 2: Manually Set IDE

If environment variables are not detected, you can manually set the IDE using the MCP tool:

```
ide(action='set', ide_name='windsurf')
```

This will force the MCP server to use Windsurf-specific directories (`.windsurf/`) regardless of environment variables.

## Solution 3: Check MCP Server Logs

The MCP server logs show IDE detection at startup. Check the logs in your MCP server output:

```
======================================================================
IDE DETECTION
======================================================================
Current working directory: /path/to/your/project
✓ Detected IDE: WINDSURF
  Rules will sync to: .windsurf/ directories
======================================================================
```

If you see:
- `✓ Detected IDE: VSCODE` - VS Code was detected instead of Windsurf
- `⚠️ Could not detect IDE` - No IDE was detected

Then you need to manually set the IDE using Solution 2.

## Solution 4: Restart Windsurf

Sometimes environment variables are not set until Windsurf is fully restarted:

1. Close Windsurf completely
2. Open Windsurf
3. Open your project
4. Check IDE detection again

## Verification

After setting the IDE, verify it's working by:

1. **Check current IDE**:
   ```
   ide(action='info')
   ```
   
   Should return:
   ```json
   {
     "current_ide": "windsurf",
     "detected_ide": "windsurf"
   }
   ```

2. **Run a sync**:
   ```
   sync(action='full', workspace_path='/absolute/path/to/project')
   ```
   
   Check that `.windsurf/` directory is created in your project root.

3. **Check the logs** for:
   ```
   ✓ Detected IDE: WINDSURF
   Rules will sync to: .windsurf/ directories
   ```

## Permanent Fix

To ensure Windsurf is always detected, add this to your team config's MCP server configuration:

```json
{
  "team-config": {
    "command": "uvx",
    "args": [
      "--from",
      "git+https://github.com/coley-angel/remote_context_mcp",
      "--reinstall-package",
      "mcp-team-config",
      "mcp-team-config"
    ],
    "env": {
      "GITHUB_TOKEN": "${GITHUB_TOKEN}",
      "TEAM_CONFIG_REPO": "https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles",
      "TEAM_CONFIG_BRANCH": "main",
      "TEAM_CONFIG_FILE": "team_config.yaml",
      "FORCE_IDE": "windsurf"
    }
  }
}
```

Then update the code to check for `FORCE_IDE` environment variable first.

## Common Issues

### Issue: `.vscode` directories are created instead of `.windsurf`

**Cause**: VS Code was detected instead of Windsurf

**Fix**: 
1. Run `ide(action='set', ide_name='windsurf')`
2. Run `sync(action='full', workspace_path='/path/to/project')` again
3. The correct `.windsurf/` directory will be created

### Issue: Both `.vscode` and `.windsurf` directories exist

**Cause**: IDE was changed mid-sync or multiple syncs with different IDE detection

**Fix**:
1. Decide which IDE you want to use (probably Windsurf)
2. Run `ide(action='set', ide_name='windsurf')`
3. Delete the `.vscode` directory if not needed
4. Run `sync(action='full', workspace_path='/path/to/project')` to populate `.windsurf/`

### Issue: Rules not showing up in Windsurf

**Cause**: Rules are in the wrong directory

**Fix**:
1. Check that rules are in `.windsurf/` not `.vscode/`
2. If in wrong directory, move them:
   ```bash
   mv .vscode/rules .windsurf/
   ```
3. Or re-sync with correct IDE set:
   ```
   ide(action='set', ide_name='windsurf')
   sync(action='full', workspace_path='/path/to/project')
   ```

## Debug Checklist

- [ ] Run `test_ide_detection.py` to check environment variables
- [ ] Check MCP server logs for IDE detection message
- [ ] Verify `CODEIUM_PID` or `WINDSURF_PID` is set in environment
- [ ] Run `ide(action='info')` to see current IDE
- [ ] Manually set IDE with `ide(action='set', ide_name='windsurf')` if needed
- [ ] Run sync with explicit workspace path
- [ ] Verify `.windsurf/` directory is created
- [ ] Check that rules appear in Windsurf

## Need More Help?

Run the diagnostic tool to get a complete picture:

```
diagnose_config()
```

This will show:
- Environment variables
- Current config status
- GitHub connection test
- Recommendations

Share the output for further troubleshooting.
