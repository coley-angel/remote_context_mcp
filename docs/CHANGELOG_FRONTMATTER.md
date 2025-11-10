# Changelog: Per-Content-Type Frontmatter Configuration

## Summary

Added support for separate frontmatter defaults for each content type (rules, workflows, prompts, instructions) with proper file path handling.

## Changes Made

### 1. Schema Updates (`schemas.py`)

#### IDEProfile Class
- Added per-content-type frontmatter fields:
  - `frontmatter_defaults_rules: Optional[FrontmatterConfig]`
  - `frontmatter_defaults_workflows: Optional[FrontmatterConfig]`
  - `frontmatter_defaults_prompts: Optional[FrontmatterConfig]`
  - `frontmatter_defaults_instructions: Optional[FrontmatterConfig]`
- Added `get_frontmatter_for_type(content_type: ContentType)` method
  - Returns content-type-specific config if available
  - Falls back to general `frontmatter_defaults` if not specified
- Maintained backward compatibility with legacy `frontmatter_defaults` field

#### Default IDE Profiles (`get_default_ide_profiles()`)
Updated default profiles for windsurf, cursor, and vscode with:
- **Rules**: `trigger: always_on`, `priority: critical`
- **Workflows**: `trigger: manual`, `priority: high`
- **Prompts**: `trigger: on_demand`, `priority: medium`
- **Instructions**: `trigger: always_on`, `priority: high`

### 2. Sync Logic Updates (`main.py`)

#### `sync_with_ide_config()` function
Updated all content type syncing sections:

**Rules** (lines 1801-1807):
```python
frontmatter_config = ide_config.get_frontmatter_for_type(ContentType.RULE)
content_with_frontmatter = addFrontmatterToContent(content, frontmatter_config)
```

**Workflows** (lines 1830-1836):
```python
frontmatter_config = ide_config.get_frontmatter_for_type(ContentType.WORKFLOW)
content_with_frontmatter = addFrontmatterToContent(content, frontmatter_config)
```

**Prompts** (lines 1859-1865):
```python
frontmatter_config = ide_config.get_frontmatter_for_type(ContentType.PROMPT)
content_with_frontmatter = addFrontmatterToContent(content, frontmatter_config)
```

**Instructions** (lines 1888-1894):
```python
frontmatter_config = ide_config.get_frontmatter_for_type(ContentType.INSTRUCTION)
content_with_frontmatter = addFrontmatterToContent(content, frontmatter_config)
```

#### File Path Management
All content types now:
1. Use the correct directory from `ide_config.paths` (rules, workflows, prompts, instructions)
2. Apply content-type-specific frontmatter
3. Add team-config suffix: `{filename}.team-config.{profile}.md`

### 3. Configuration Example (`team_config_v2_example.yaml`)

Updated all IDE configs (windsurf, vscode, cursor) with per-content-type examples:

```yaml
frontmatter_defaults_rules:
  trigger: always_on
  priority: critical
  tags: [ide-name, team-standards, rules]
  description: "Team coding rules"

frontmatter_defaults_workflows:
  trigger: manual
  priority: high
  tags: [ide-name, team-standards, workflows]
  description: "Team workflows"

frontmatter_defaults_prompts:
  trigger: on_demand
  priority: medium
  tags: [ide-name, team-standards, prompts]
  description: "AI prompts"

frontmatter_defaults_instructions:
  trigger: always_on
  priority: high
  tags: [ide-name, team-standards, instructions]
  description: "Team instructions"

# Legacy fallback maintained for backward compatibility
frontmatter_defaults:
  trigger: always_on
  priority: high
  tags: [ide-name, team-standards]
```

### 4. Documentation (`docs/FRONTMATTER_CONFIG.md`)

Created comprehensive documentation covering:
- Overview and use cases
- Configuration structure
- Frontmatter fields reference
- Fallback behavior
- File path management
- Examples for common scenarios
- Migration guide from legacy config
- Best practices
- Troubleshooting guide

## Benefits

### 1. Flexibility
Different content types can have different behaviors:
- Rules: Always active, critical priority
- Workflows: Manual trigger, on-demand usage
- Prompts: Available when needed
- Instructions: Always available guidance

### 2. Proper File Organization
Each content type goes to its configured directory:
```
.windsurf/
  rules/      ← Rules go here
  workflows/  ← Workflows go here
  prompts/    ← Prompts go here
  instructions/ ← Instructions go here
```

### 3. Backward Compatibility
- Legacy `frontmatter_defaults` still works
- Automatic fallback to general config
- No breaking changes for existing users

### 4. Profile-Based Management
Files include profile suffix for easy tracking:
- `rule-name.team-config.default.md`
- `rule-name.team-config.production.md`

## Usage Examples

### Basic Configuration

```yaml
ide_configs:
  windsurf:
    paths:
      rules: ".windsurf/rules"
      workflows: ".windsurf/workflows"
    
    frontmatter_defaults_rules:
      trigger: always_on
      priority: critical
    
    frontmatter_defaults_workflows:
      trigger: manual
      priority: high
```

### Per-Profile Configuration

```yaml
profiles:
  development:
    ide_configs:
      windsurf:
        frontmatter_defaults_rules:
          trigger: always_on
          priority: high
  
  production:
    ide_configs:
      windsurf:
        frontmatter_defaults_rules:
          trigger: always_on
          priority: critical
```

## Testing Recommendations

1. **Test per-content-type configs**
   ```python
   sync(action='full', workspace_path='/project', ide_choice=1)
   ```
   Verify each content type has appropriate frontmatter

2. **Test fallback behavior**
   - Remove content-type-specific config
   - Verify fallback to general `frontmatter_defaults`

3. **Test file paths**
   - Verify files go to correct directories
   - Check team-config suffix is applied

4. **Test profile switching**
   - Switch profiles
   - Verify old profile files are cleaned up
   - Verify new profile files use correct frontmatter

## Migration Path

### For Existing Users

No action required! Existing configs continue to work:

```yaml
# Old config (still works)
frontmatter_defaults:
  trigger: always_on
  priority: high
```

### To Enable New Features

Add content-type-specific configs:

```yaml
# New config (more flexible)
frontmatter_defaults_rules:
  trigger: always_on
  priority: critical

frontmatter_defaults_workflows:
  trigger: manual
  priority: high

# Keep legacy as fallback
frontmatter_defaults:
  trigger: always_on
  priority: high
```

## Related Files

- `schemas.py` - Data models and configuration structures
- `main.py` - Sync logic and MCP tool implementations
- `frontmatter_utils.py` - Frontmatter parsing and generation
- `team_config_v2_example.yaml` - Example configuration
- `docs/FRONTMATTER_CONFIG.md` - User documentation

## Future Enhancements

Potential improvements:
1. UI tool for generating frontmatter configs
2. Validation rules for frontmatter combinations
3. Template-based frontmatter (e.g., "strict", "flexible")
4. Per-file frontmatter overrides
5. Frontmatter inheritance from parent configs
