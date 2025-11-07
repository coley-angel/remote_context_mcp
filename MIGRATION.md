# Migration Guide: v1 to v2

This guide helps you migrate from the old Instructions MCP Server to the new Team Configuration MCP Server.

## What's Changed

### 🎯 New Features
- Multi-IDE support (Windsurf, Cursor, VS Code)
- Rules and workflows management
- Built-in security validation
- Git-based repository syncing
- Dynamic MCP server configuration
- Enhanced profile system

### 📝 Configuration File Changes

**Old Format (`context_config.yaml`):**
```yaml
profiles:
  default:
    active: true
    instructions:
      - "https://example.com/file.md"
```

**New Format (`team_config.yaml`):**
```yaml
version: "1.0.0"
team_name: "Your Team"

global_security:
  enabled: true
  level: "basic"

profiles:
  default:
    active: true
    description: "Default profile"
    instructions:
      - url: "https://example.com/file.md"
    rules: []
    workflows: []
    prompts: []
    mcp_servers: []
    security:
      enabled: true
      level: "basic"
```

## Migration Steps

### Step 1: Update Dependencies

```bash
uv sync
```

This will install the new dependencies including GitPython.

### Step 2: Convert Configuration

Use the conversion helper:

```python
# convert_config.py
import yaml
from pathlib import Path

def convert_old_to_new(old_config_path, new_config_path):
    """Convert old context_config.yaml to new team_config.yaml"""
    
    with open(old_config_path, 'r') as f:
        old_config = yaml.safe_load(f)
    
    new_config = {
        "version": "1.0.0",
        "team_name": "default",
        "global_security": {
            "enabled": True,
            "level": "basic",
            "scan_for_secrets": True,
            "scan_for_pii": True
        },
        "supported_ides": ["vscode", "cursor", "windsurf"],
        "profiles": {}
    }
    
    # Convert profiles
    for profile_name, profile_data in old_config.get("profiles", {}).items():
        instructions = []
        for item in profile_data.get("instructions", []):
            if isinstance(item, str):
                instructions.append({"url": item})
            else:
                instructions.append(item)
        
        new_config["profiles"][profile_name] = {
            "active": profile_data.get("active", False),
            "description": f"Migrated profile: {profile_name}",
            "instructions": instructions,
            "rules": [],
            "workflows": [],
            "prompts": [],
            "mcp_servers": [],
            "security": {
                "enabled": True,
                "level": "basic"
            }
        }
    
    with open(new_config_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Converted {old_config_path} to {new_config_path}")

# Usage
if __name__ == "__main__":
    convert_old_to_new("context_config.yaml", "team_config.yaml")
```

Run the conversion:
```bash
python convert_config.py
```

### Step 3: Update Environment Variables

**Old:**
```bash
CONTEXT_CONFIG_FILE=context_config.yaml
INSTRUCTIONS_DIR=~/vscode-instructions
```

**New:**
```bash
TEAM_CONFIG_FILE=team_config.yaml
MCP_BASE_DIR=~/.mcp-team-config
WORKSPACE_DIR=$(pwd)
```

### Step 4: Update MCP Configuration

**Old (VS Code `.vscode/mcp.json`):**
```json
{
  "servers": {
    "remote-context": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "env": {
        "CONTEXT_CONFIG_FILE": "context_config.yaml"
      }
    }
  }
}
```

**New:**
```json
{
  "servers": {
    "team-config": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "env": {
        "TEAM_CONFIG_FILE": "team_config.yaml",
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Step 5: Update Tool Calls

**Old Tool Names:**
- `fetch_and_sync_instructions` → `sync_team_config`
- `get_available_profiles` → `list_profiles`
- `set_active_profile` → `set_active_profile` (same)
- `list_context_config` → `get_config`

**Example Changes:**

```python
# Old
fetch_and_sync_instructions(profile_name="default")

# New
sync_team_config(profile_name="default")
```

## New Capabilities

### Security Validation

Add security settings to your profiles:

```yaml
profiles:
  default:
    security:
      enabled: true
      level: "basic"  # or "strict", "paranoid"
      forbidden_patterns:
        - "hardcoded.*password"
      scan_for_secrets: true
      scan_for_pii: true
```

### Rules and Workflows

Add rules and workflows to your profiles:

```yaml
profiles:
  default:
    rules:
      - url: "https://company.com/coding-rules.md"
    workflows:
      - url: "https://company.com/pr-workflow.md"
```

### MCP Server Management

Add MCP servers to your profiles:

```yaml
profiles:
  default:
    mcp_servers:
      - name: "github"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-github"]
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
        enabled: true
```

### Multi-IDE Support

The server now automatically syncs to all detected IDEs:
- Windsurf
- Cursor
- VS Code

No additional configuration needed!

## Testing Migration

1. **Test configuration loading:**
   ```bash
   uv run python main.py
   # Check logs for successful configuration loading
   ```

2. **Test profile sync:**
   ```python
   # In your IDE's AI chat
   sync_team_config(profile_name="default")
   ```

3. **Verify IDE sync:**
   ```python
   list_installed_ides()
   ```

4. **Check security validation:**
   ```python
   validate_content_security(
       content="test content",
       content_type="instruction"
   )
   ```

## Rollback Plan

If you need to rollback:

1. **Keep old configuration:**
   ```bash
   cp context_config.yaml context_config.yaml.backup
   ```

2. **Revert to v1:**
   ```bash
   git checkout v1.0.0
   uv sync
   ```

3. **Restore old config:**
   ```bash
   mv context_config.yaml.backup context_config.yaml
   ```

## Common Issues

### Issue: "Module not found" errors

**Solution:**
```bash
uv sync --force
```

### Issue: Configuration not loading

**Solution:**
- Check YAML syntax with: `python -c "import yaml; yaml.safe_load(open('team_config.yaml'))"`
- Verify file permissions
- Check `TEAM_CONFIG_FILE` environment variable

### Issue: IDE not syncing

**Solution:**
- Verify IDE is installed: `list_installed_ides()`
- Check IDE settings file exists
- Restart IDE after configuration changes

### Issue: Security validation blocking content

**Solution:**
- Review violations: `validate_content_security(content=...)`
- Adjust security level to "basic" or "none" temporarily
- Fix content issues or add exceptions

## Getting Help

- Review logs in `~/.mcp-team-config/logs/`
- Check the new README for detailed documentation
- Open an issue on GitHub with migration questions

## Checklist

- [ ] Dependencies updated (`uv sync`)
- [ ] Configuration converted to new format
- [ ] Environment variables updated
- [ ] MCP configuration updated in IDEs
- [ ] Tested profile sync
- [ ] Verified IDE detection
- [ ] Tested security validation
- [ ] Backup created of old configuration
- [ ] Team notified of changes

## What's Next?

After migrating, explore new features:

1. **Add security validation** to prevent secrets in configs
2. **Set up central repository** for team-wide config sync
3. **Configure rules and workflows** for your team
4. **Manage MCP servers** dynamically per profile
5. **Enable multi-IDE support** for team using different editors

---

Need help? Check the main README or open a GitHub issue.
