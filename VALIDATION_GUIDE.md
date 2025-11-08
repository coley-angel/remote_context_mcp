# Team Config Validation Guide

## Quick Start

Validate your `team_config.yaml` file:

```bash
uv run python validate_config.py /path/to/team_config.yaml
```

## What It Checks

### V1 Configs
- ✅ Required fields (team_name, profiles)
- ✅ Profile structure
- ✅ Content source format
- ✅ Active profile status
- ⚠️ Suggests V2 upgrade

### V2 Configs
- ✅ All V1 checks PLUS:
- ✅ IDE configurations
- ✅ Path configurations (workspace-relative)
- ✅ Frontmatter defaults
- ✅ Version compliance

## Validation Levels

| Icon | Level | Description |
|------|-------|-------------|
| ❌ | ERROR | Must fix - config is invalid |
| ⚠️ | WARNING | Should fix - may cause issues |
| ℹ️ | INFO | Suggestions for improvement |

## Example Output

### Valid V2 Config
```
======================================================================
VALIDATING: /path/to/team_config_v2.yaml
======================================================================

📋 Detected version: 2.0.0 (V2)

🔍 Validating V2 format...

======================================================================
VALIDATION RESULTS
======================================================================

✅ No issues found! Config is valid.
```

### V1 Config with Warnings
```
======================================================================
VALIDATING: /path/to/team_config.yaml
======================================================================

📋 Detected version: 1.0.0 (V1)

🔍 Validating V1 format...

======================================================================
VALIDATION RESULTS
======================================================================

⚠️  WARNINGS (1):
----------------------------------------------------------------------
⚠️ [WARNING] version: Using V1 config format
   Current: 1.0.0
   Fix: Upgrade to version: '2.0.0' for new features

ℹ️  INFO (3):
----------------------------------------------------------------------
ℹ️ [INFO] profiles.default: Missing ide_configs (V2 feature)
   Fix: Add ide_configs with windsurf, vscode, cursor configurations

ℹ️ [INFO] profiles.testing: Missing ide_configs (V2 feature)
   Fix: Add ide_configs with windsurf, vscode, cursor configurations

ℹ️ [INFO] upgrade: Consider upgrading to V2 format
   Fix: V2 adds IDE-specific configs, better file tracking, and simplified architecture

======================================================================
SUMMARY:
  Errors:   0
  Warnings: 1
  Info:     3
  Status:   ⚠️  VALID (with warnings)
======================================================================
```

### Invalid Config
```
======================================================================
VALIDATING: /path/to/bad_config.yaml
======================================================================

📋 Detected version: 2.0.0 (V2)

🔍 Validating V2 format...

======================================================================
VALIDATION RESULTS
======================================================================

❌ ERRORS (2):
----------------------------------------------------------------------
❌ [ERROR] team_name: Required field missing
   Fix: Add 'team_name:' to config

❌ [ERROR] profiles.default.ide_configs.windsurf.paths.rules: Path must be relative, not absolute
   Current: /absolute/path/to/rules
   Fix: Use relative path like '.ide/rules'

======================================================================
SUMMARY:
  Errors:   2
  Warnings: 0
  Info:     0
  Status:   ❌ INVALID
======================================================================
```

## Common Validation Issues

### Missing Required Fields

**Error:**
```
❌ [ERROR] team_name: Required field missing
   Fix: Add 'team_name:' to config
```

**Fix:**
```yaml
team_name: Your Team Name
```

### Absolute Paths (V2)

**Error:**
```
❌ [ERROR] profiles.default.ide_configs.windsurf.paths.rules: Path must be relative, not absolute
   Current: /absolute/path
   Fix: Use relative path like '.ide/rules'
```

**Fix:**
```yaml
ide_configs:
  windsurf:
    paths:
      rules: .windsurf/  # Relative to workspace root
```

### Missing IDE Configs (V2)

**Warning:**
```
⚠️ [WARNING] profiles.default.ide_configs: Missing IDE configs (V2 feature)
   Fix: Add ide_configs with windsurf, vscode, cursor
```

**Fix:**
```yaml
profiles:
  default:
    ide_configs:
      windsurf:
        name: windsurf
        display_name: Windsurf
        paths:
          rules: .windsurf/
          workflows: .windsurf/
        frontmatter_defaults:
          trigger: always_on
          tags: [team]
```

### Invalid Repo Format

**Warning:**
```
⚠️ [WARNING] profiles.default.rules[0].repo: Repo should be in 'org/repo' format
   Current: https://github.com/org/repo
   Fix: Use format: 'CiscoOpsStack/MyRepo'
```

**Fix:**
```yaml
rules:
  - repo: CiscoOpsStack/MyRepo  # Not: https://github.com/...
    paths: ["rules/*.md"]
```

### Invalid Trigger Values

**Warning:**
```
⚠️ [WARNING] profiles.default.ide_configs.windsurf.frontmatter_defaults.trigger: Unknown trigger value: auto
   Current: auto
   Fix: Use one of: always_on, manual, on_demand
```

**Fix:**
```yaml
frontmatter_defaults:
  trigger: always_on  # Valid: always_on, manual, on_demand
```

### Multiple Active Profiles

**Warning:**
```
⚠️ [WARNING] profiles: Multiple active profiles (2)
   Fix: Only one profile should be active
```

**Fix:**
```yaml
profiles:
  default:
    active: true   # ✓ Active
  production:
    active: false  # ✓ Inactive
```

## Validation Checklist

Before deploying your config:

- [ ] `uv run python validate_config.py config.yaml` returns no errors
- [ ] All required fields present
- [ ] At least one profile defined
- [ ] Exactly one active profile
- [ ] All paths are workspace-relative (V2)
- [ ] IDE configs present for each IDE you use (V2)
- [ ] Frontmatter defaults are valid (V2)

## V1 to V2 Migration

### 1. Validate Current Config

```bash
uv run python validate_config.py team_config.yaml
```

Look for warnings about missing V2 features.

### 2. Update Version

```yaml
version: 2.0.0  # Was: 1.0.0
```

### 3. Add IDE Configs

```yaml
profiles:
  default:
    # ... existing content ...
    
    # Add this:
    ide_configs:
      windsurf:
        name: windsurf
        display_name: Windsurf
        paths:
          rules: .windsurf/
          workflows: .windsurf/
          prompts: .windsurf/
          instructions: .windsurf/
        frontmatter_defaults:
          trigger: always_on
          tags: [windsurf, team]
      
      vscode:
        name: vscode
        display_name: VS Code
        paths:
          rules: .vscode/rules
          workflows: .vscode/workflows
          prompts: .vscode/prompts
          instructions: .vscode/instructions
          mcp_config: .vscode/mcp.json
        frontmatter_defaults:
          trigger: always_on
          tags: [vscode, team]
      
      cursor:
        name: cursor
        display_name: Cursor
        paths:
          rules: .cursor/rules
          workflows: .cursor/workflows
          prompts: .cursor/prompts
          instructions: .cursor/instructions
          mcp_config: .cursor/mcp.json
        frontmatter_defaults:
          trigger: always_on
          tags: [cursor, team]
```

### 4. Validate V2 Config

```bash
uv run python validate_config.py team_config_v2.yaml
```

Should return: `✅ No issues found! Config is valid.`

## Integration with CI/CD

### GitHub Actions

```yaml
name: Validate Config

on:
  push:
    paths:
      - 'team_config.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Validate Config
        run: |
          cd path/to/mcp
          uv run python validate_config.py ../../team_config.yaml
```

### Pre-commit Hook

```bash
#!/bin/sh
# .git/hooks/pre-commit

if git diff --cached --name-only | grep -q "team_config.yaml"; then
    echo "Validating team_config.yaml..."
    cd path/to/mcp
    uv run python validate_config.py ../../team_config.yaml
    if [ $? -ne 0 ]; then
        echo "❌ Config validation failed!"
        exit 1
    fi
    echo "✅ Config validation passed!"
fi
```

## Advanced Usage

### Validate Multiple Configs

```bash
for config in configs/*.yaml; do
    echo "Validating $config..."
    uv run python validate_config.py "$config"
done
```

### Exit Code

- `0` - Valid config (may have warnings/info)
- `1` - Invalid config (has errors)

Use in scripts:
```bash
if uv run python validate_config.py config.yaml; then
    echo "✅ Valid"
else
    echo "❌ Invalid"
    exit 1
fi
```

## Troubleshooting

### ModuleNotFoundError: yaml

**Error:**
```
ModuleNotFoundError: No module named 'yaml'
```

**Fix:**
```bash
# Use uv run (preferred)
uv run python validate_config.py config.yaml

# Or install PyYAML
pip install pyyaml
```

### File Not Found

**Error:**
```
❌ [ERROR] file: File not found: /path/to/config.yaml
```

**Fix:**
- Check file path is correct
- Use absolute path or relative from current directory
- Ensure file has `.yaml` extension

### Invalid YAML Syntax

**Error:**
```
❌ [ERROR] yaml: Invalid YAML syntax: ...
```

**Fix:**
- Check YAML indentation (use spaces, not tabs)
- Ensure colons have spaces after them: `key: value`
- Quote strings with special characters: `url: "http://example.com"`
- Use YAML validator online: https://www.yamllint.com/

## Summary

The validator helps you:
1. ✅ Catch errors before deployment
2. ✅ Ensure config follows V2 best practices
3. ✅ Get specific fix suggestions
4. ✅ Migrate from V1 to V2 safely
5. ✅ Integrate validation into CI/CD

**Always validate before committing config changes!**
