# V2 Architecture - Simplified, Data-Driven, IDE-Agnostic

## Overview

Version 2 of the Team Config MCP represents a complete architectural simplification:

- **No global paths** - Everything is workspace-relative
- **Data-driven** - All configuration in YAML, not code
- **IDE-agnostic** - MCP doesn't detect IDE, user chooses
- **User choice** - Select which IDE config to load (1=Windsurf, 2=VS Code, 3=Cursor)

## Key Changes from V1

### V1 (Old Approach)
- ❌ Complex IDE detection logic
- ❌ Mixed global and local paths
- ❌ Hard-coded IDE configurations
- ❌ Automatic IDE selection
- ❌ Global fallback directories

### V2 (New Approach)
- ✅ User selects IDE config
- ✅ All paths workspace-relative
- ✅ IDE configs defined in YAML
- ✅ Simple, predictable behavior
- ✅ No global directories

## Configuration Structure

### Profile with IDE Configs

```yaml
profiles:
  default:
    active: true
    description: "Development profile"
    
    # Content sources
    rules:
      - repo: "your-org/coding-standards"
        branch: "main"
        paths: ["rules/*.md"]
    
    # IDE-specific configurations
    ide_configs:
      
      windsurf:
        name: "windsurf"
        display_name: "Windsurf"
        enabled: true
        
        # All paths relative to workspace root
        paths:
          rules: ".windsurf/"
          workflows: ".windsurf/"
          prompts: ".windsurf/"
          instructions: ".windsurf/"
          mcp_config: null  # No local MCP for Windsurf
        
        # Frontmatter defaults for this IDE
        frontmatter_defaults:
          trigger: always_on
          priority: high
          tags: [windsurf, team]
          author: Team
      
      vscode:
        name: "vscode"
        display_name: "VS Code"
        enabled: true
        
        paths:
          rules: ".vscode/rules"
          workflows: ".vscode/workflows"
          prompts: ".vscode/prompts"
          instructions: ".vscode/instructions"
          mcp_config: ".vscode/mcp.json"
        
        frontmatter_defaults:
          trigger: always_on
          priority: high
          tags: [vscode, team]
      
      cursor:
        name: "cursor"
        display_name: "Cursor"
        enabled: true
        
        paths:
          rules: ".cursor/rules"
          workflows: ".cursor/workflows"
          prompts: ".cursor/prompts"
          instructions: ".cursor/instructions"
          mcp_config: ".cursor/mcp.json"
        
        frontmatter_defaults:
          trigger: always_on
          priority: high
          tags: [cursor, team]
```

## Usage

### List Available IDE Configs

```python
sync(action="list_ides", workspace_path="/path/to/project")
```

Returns:
```json
{
  "available_ides": [
    {
      "id": 1,
      "name": "windsurf",
      "display_name": "Windsurf",
      "enabled": true,
      "paths": {
        "rules": ".windsurf/",
        "workflows": ".windsurf/"
      }
    },
    {
      "id": 2,
      "name": "vscode",
      "display_name": "VS Code",
      "enabled": true
    },
    {
      "id": 3,
      "name": "cursor",
      "display_name": "Cursor",
      "enabled": true
    }
  ]
}
```

### Sync with Specific IDE Config

```python
# Option 1: Use IDE number
sync(
    action="full",
    workspace_path="/absolute/path/to/project",
    ide_choice=1  # 1=Windsurf, 2=VS Code, 3=Cursor
)

# Option 2: Use IDE name
sync(
    action="full",
    workspace_path="/absolute/path/to/project",
    ide_name="windsurf"
)
```

### Result

Files are synced to paths defined in the IDE config:

**For Windsurf (choice 1):**
```
/project-root/.windsurf/
  ├── rule1.md
  ├── rule2.md
  ├── workflow1.md
  └── workflow2.md
```

**For VS Code (choice 2):**
```
/project-root/.vscode/
  ├── rules/
  │   ├── rule1.md
  │   └── rule2.md
  └── workflows/
      ├── workflow1.md
      └── workflow2.md
```

**For Cursor (choice 3):**
```
/project-root/.cursor/
  ├── rules/
  │   ├── rule1.md
  │   └── rule2.md
  └── workflows/
      ├── workflow1.md
      └── workflow2.md
```

## Benefits

### 1. Simplicity
- No complex IDE detection code
- No platform-specific logic
- User makes explicit choice

### 2. Predictability
- Always know where files go
- No surprises from auto-detection
- Clear error messages

### 3. Flexibility
- Easy to add new IDE support
- Just add to YAML config
- No code changes needed

### 4. Maintainability
- Configuration-driven
- Easy to understand
- Less code to maintain

### 5. Workspace-Only
- No global pollution
- Project-specific rules
- Version control friendly

## Default IDE Configurations

If no IDE configs are specified in the profile, sensible defaults are applied:

### Windsurf
```yaml
paths:
  rules: ".windsurf/"
  workflows: ".windsurf/"
  prompts: ".windsurf/"
  instructions: ".windsurf/"
  mcp_config: null
frontmatter_defaults:
  trigger: always_on
  priority: high
  tags: [windsurf, team]
```

### VS Code
```yaml
paths:
  rules: ".vscode/rules"
  workflows: ".vscode/workflows"
  prompts: ".vscode/prompts"
  instructions: ".vscode/instructions"
  mcp_config: ".vscode/mcp.json"
frontmatter_defaults:
  trigger: always_on
  priority: high
  tags: [vscode, team]
```

### Cursor
```yaml
paths:
  rules: ".cursor/rules"
  workflows: ".cursor/workflows"
  prompts: ".cursor/prompts"
  instructions: ".cursor/instructions"
  mcp_config: ".cursor/mcp.json"
frontmatter_defaults:
  trigger: always_on
  priority: high
  tags: [cursor, team]
```

## Migration from V1

### Step 1: Update Your Config

Add `ide_configs` section to your profiles:

```yaml
profiles:
  default:
    # ... existing config ...
    
    # Add this:
    ide_configs:
      windsurf:
        name: "windsurf"
        display_name: "Windsurf"
        enabled: true
        paths:
          rules: ".windsurf/"
          workflows: ".windsurf/"
        frontmatter_defaults:
          trigger: always_on
          tags: [windsurf, team]
```

### Step 2: Update Your Sync Calls

```python
# Old V1 way (auto-detection)
sync(action="full", workspace_path="/path/to/project")

# New V2 way (explicit choice)
sync(
    action="full",
    workspace_path="/path/to/project",
    ide_choice=1  # Choose Windsurf
)
```

### Step 3: Remove Old Files (Optional)

If you were using global directories:
```bash
rm -rf ~/windsurf-instructions
rm -rf ~/cursor-instructions
rm -rf ~/vscode-instructions
```

## FAQ

### Q: Why remove IDE auto-detection?
**A:** It was complex, error-prone, and often wrong. Explicit user choice is simpler and more reliable.

### Q: What if I want to sync to multiple IDEs?
**A:** Run sync multiple times with different `ide_choice` values:
```python
sync(action="full", workspace_path="/path", ide_choice=1)  # Windsurf
sync(action="full", workspace_path="/path", ide_choice=2)  # VS Code
sync(action="full", workspace_path="/path", ide_choice=3)  # Cursor
```

### Q: Can I customize paths per profile?
**A:** Yes! Define different IDE configs in each profile.

### Q: What happened to global directories?
**A:** Removed. Everything is now workspace-local for consistency.

### Q: Can I still use scope='global'?
**A:** No. V2 only supports workspace-relative paths.

## Example Workflow

```python
# 1. List available IDEs
result = sync(action="list_ides", workspace_path="/my-project")
print(result)  # Shows: 1=Windsurf, 2=VS Code, 3=Cursor

# 2. Choose your IDE (e.g., Windsurf)
sync(
    action="full",
    workspace_path="/my-project",
    ide_choice=1
)

# 3. Files are synced to .windsurf/ directory
# /my-project/.windsurf/rule1.md
# /my-project/.windsurf/rule2.md
```

## Summary

- **Simpler**: No detection logic, user chooses
- **Clearer**: Explicit paths in config
- **Predictable**: Always workspace-relative
- **Flexible**: Easy to customize per IDE/profile
- **Maintainable**: Data-driven, not code-driven
