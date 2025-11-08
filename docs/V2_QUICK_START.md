# V2 Quick Start Guide

## Overview

Version 2 is **simplified, data-driven, and IDE-agnostic**:
- ✅ No IDE auto-detection
- ✅ User chooses IDE explicitly (1, 2, 3)
- ✅ All paths workspace-relative
- ✅ Configuration-driven (not code)
- ✅ No global directories

## Quick Start

### 1. List Available IDEs

First, see which IDE configurations are available in your profile:

```python
sync(action="list_ides")
```

**Response:**
```json
{
  "success": true,
  "profile": "default",
  "available_ides": [
    {
      "id": 1,
      "name": "windsurf",
      "display_name": "Windsurf",
      "paths": {
        "rules": ".windsurf/",
        "workflows": ".windsurf/"
      }
    },
    {
      "id": 2,
      "name": "vscode",
      "display_name": "VS Code",
      "paths": {
        "rules": ".vscode/rules",
        "workflows": ".vscode/workflows"
      }
    },
    {
      "id": 3,
      "name": "cursor",
      "display_name": "Cursor",
      "paths": {
        "rules": ".cursor/rules",
        "workflows": ".cursor/workflows"
      }
    }
  ]
}
```

### 2. Sync with Your IDE

Choose your IDE and sync:

```python
# Option 1: Use IDE number
sync(
    action="full",
    workspace_path="/absolute/path/to/your/project",
    ide_choice=1  # 1=Windsurf
)

# Option 2: Use IDE name
sync(
    action="full",
    workspace_path="/absolute/path/to/your/project",
    ide_name="windsurf"
)
```

### 3. Check Results

Files are synced to workspace-relative paths:

**For Windsurf (choice 1):**
```
/your-project/
├── .windsurf/
│   ├── rule1.md
│   ├── rule2.md
│   ├── workflow1.md
│   └── workflow2.md
```

**For VS Code (choice 2):**
```
/your-project/
├── .vscode/
│   ├── rules/
│   │   ├── rule1.md
│   │   └── rule2.md
│   └── workflows/
│       ├── workflow1.md
│       └── workflow2.md
```

**For Cursor (choice 3):**
```
/your-project/
├── .cursor/
│   ├── rules/
│   │   ├── rule1.md
│   │   └── rule2.md
│   └── workflows/
│       ├── workflow1.md
│       └── workflow2.md
```

## Configuration

### team_config_v2_example.yaml

```yaml
version: "2.0.0"
team_name: "Engineering Team"

profiles:
  default:
    active: true
    
    # Content sources
    rules:
      - repo: "your-org/coding-standards"
        branch: "main"
        paths: ["rules/*.md"]
    
    # IDE configs
    ide_configs:
      windsurf:
        name: "windsurf"
        display_name: "Windsurf"
        enabled: true
        
        paths:
          rules: ".windsurf/"
          workflows: ".windsurf/"
          prompts: ".windsurf/"
          instructions: ".windsurf/"
        
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

## Common Workflows

### Sync Rules to Multiple IDEs

```python
# Sync to Windsurf
sync(action="full", workspace_path="/my-project", ide_choice=1)

# Sync to VS Code
sync(action="full", workspace_path="/my-project", ide_choice=2)

# Sync to Cursor
sync(action="full", workspace_path="/my-project", ide_choice=3)
```

### Check for Updates

```python
sync(action="check")
```

### Reload Configuration

```python
sync(action="reload")
```

## Key Differences from V1

| Feature | V1 | V2 |
|---------|----|----|
| IDE Detection | Automatic (often wrong) | User chooses explicitly |
| Paths | Global + Local | Workspace-relative only |
| Configuration | Hardcoded in Python | Defined in YAML |
| Scope Parameter | `auto`, `workspace`, `global`, `both` | Removed (always workspace) |
| IDE Selection | Auto-detected | `ide_choice` or `ide_name` |
| Frontmatter | Global default | Per-IDE configurable |

## Error Handling

### No IDE Specified

```python
sync(action="full", workspace_path="/path")
```

**Error:**
```json
{
  "error": "IDE selection required",
  "available_ides": [
    "1=windsurf (Windsurf)",
    "2=vscode (VS Code)",
    "3=cursor (Cursor)"
  ],
  "hint": "Specify ide_choice (number) or ide_name (string)"
}
```

### Invalid IDE Choice

```python
sync(action="full", workspace_path="/path", ide_choice=99)
```

**Error:**
```json
{
  "error": "Invalid IDE choice: 99",
  "valid_range": "1-3",
  "hint": "Use sync(action='list_ides') to see available IDE configs"
}
```

### Missing Workspace Path

```python
sync(action="full", ide_choice=1)
```

**Error:**
```json
{
  "error": "workspace_path is required",
  "hint": "Provide absolute path to project root",
  "example": "sync(action='full', workspace_path='/Users/username/my-project', ide_choice=1)"
}
```

## Customization

### Add Custom IDE

Edit your `team_config.yaml`:

```yaml
profiles:
  default:
    ide_configs:
      # ... existing configs ...
      
      zed:
        name: "zed"
        display_name: "Zed Editor"
        enabled: true
        paths:
          rules: ".zed/rules"
          workflows: ".zed/workflows"
        frontmatter_defaults:
          trigger: always_on
          tags: [zed, team]
```

Then sync:
```python
sync(action="full", workspace_path="/path", ide_name="zed")
```

### Customize Paths Per Profile

```yaml
profiles:
  development:
    ide_configs:
      windsurf:
        paths:
          rules: ".windsurf/dev-rules/"  # Custom path
          workflows: ".windsurf/dev-workflows/"
  
  production:
    ide_configs:
      windsurf:
        paths:
          rules: ".windsurf/prod-rules/"  # Different path
          workflows: ".windsurf/prod-workflows/"
```

### Customize Frontmatter Per IDE

```yaml
profiles:
  default:
    ide_configs:
      windsurf:
        frontmatter_defaults:
          trigger: always_on
          priority: critical
          tags: [windsurf, production, mandatory]
          author: Security Team
          version: 2.0.0
      
      vscode:
        frontmatter_defaults:
          trigger: manual
          priority: low
          tags: [vscode, optional]
```

## Migration from V1

1. **Update your config** - Add `ide_configs` section
2. **Update sync calls** - Add `ide_choice` or `ide_name`
3. **Remove scope parameter** - No longer needed
4. **Test** - Run `sync(action="list_ides")` to verify

## Summary

- **Simpler**: No detection logic, explicit choice
- **Predictable**: Always know where files go
- **Flexible**: Easy to customize paths per IDE
- **Workspace-only**: No global directories
- **Data-driven**: Configuration over code

## Next Steps

1. Update your `team_config.yaml` with V2 structure
2. Run `sync(action="list_ides")` to see options
3. Choose your IDE and sync
4. Verify files in workspace directories
