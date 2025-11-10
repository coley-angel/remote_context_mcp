# Per-Content-Type Frontmatter Configuration

## Overview

Team Config MCP now supports separate frontmatter defaults for each content type (rules, workflows, prompts, and instructions). This allows you to configure different behaviors for different types of files.

## Use Cases

Different content types often need different frontmatter configurations:

- **Rules**: `trigger: always_on`, `priority: critical` - Always active, highest priority
- **Workflows**: `trigger: manual`, `priority: high` - Manually triggered process guides
- **Prompts**: `trigger: on_demand`, `priority: medium` - Available when needed
- **Instructions**: `trigger: always_on`, `priority: high` - Always active guidance

## Configuration

### Basic Structure

In your IDE profile configuration, you can now specify frontmatter defaults for each content type:

```yaml
ide_configs:
  windsurf:
    name: "windsurf"
    display_name: "Windsurf"
    paths:
      rules: ".windsurf/"
      workflows: ".windsurf/"
      prompts: ".windsurf/"
      instructions: ".windsurf/"
    
    # Per-content-type frontmatter defaults
    frontmatter_defaults_rules:
      trigger: always_on
      priority: critical
      tags: [windsurf, team-standards, rules]
      author: Platform Team
      description: "Team coding rules"
    
    frontmatter_defaults_workflows:
      trigger: manual
      priority: high
      tags: [windsurf, team-standards, workflows]
      author: Platform Team
      description: "Team workflows"
    
    frontmatter_defaults_prompts:
      trigger: on_demand
      priority: medium
      tags: [windsurf, team-standards, prompts]
      author: Platform Team
      description: "AI prompts"
    
    frontmatter_defaults_instructions:
      trigger: always_on
      priority: high
      tags: [windsurf, team-standards, instructions]
      author: Platform Team
      description: "Team instructions"
    
    # Legacy fallback (optional)
    frontmatter_defaults:
      trigger: always_on
      priority: high
      tags: [windsurf, team-standards]
      author: Platform Team
```

### Frontmatter Fields

Each frontmatter configuration supports these fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `trigger` | string | When to activate (required) | `always_on`, `manual`, `on_demand` |
| `priority` | string | Priority level | `critical`, `high`, `medium`, `low` |
| `tags` | array | Categorization tags | `[windsurf, team, rules]` |
| `author` | string | Content author | `Platform Team` |
| `description` | string | Brief description | `Team coding rules` |
| `glob` | string | File pattern filter | `*.py`, `*.{js,ts}` |
| `version` | string | Version number | `1.0.0` |

### Fallback Behavior

The system uses a fallback hierarchy:

1. **Content-type-specific config**: `frontmatter_defaults_rules`, `frontmatter_defaults_workflows`, etc.
2. **Legacy general config**: `frontmatter_defaults` (if content-type-specific not defined)
3. **System default**: Built-in defaults if nothing is configured

## How It Works

### During Sync

When syncing content, the system:

1. Determines the content type (rule, workflow, prompt, instruction)
2. Looks up the appropriate frontmatter config using `ide_config.get_frontmatter_for_type(content_type)`
3. Falls back to general config if content-type-specific config not found
4. Adds or validates frontmatter in the synced file

### File Path Management

Files are saved with proper paths as configured:

```yaml
paths:
  rules: ".windsurf/rules"           # Rules go here
  workflows: ".windsurf/workflows"   # Workflows go here
  prompts: ".windsurf/prompts"       # Prompts go here
  instructions: ".windsurf/instructions"  # Instructions go here
```

Files are also tagged with profile suffix for tracking:
- `rule-name.team-config.{profile}.md`
- `workflow-name.team-config.{profile}.md`

## Examples

### Example 1: Strict Rules, Flexible Prompts

```yaml
frontmatter_defaults_rules:
  trigger: always_on
  priority: critical
  description: "Must-follow coding standards"
  
frontmatter_defaults_prompts:
  trigger: on_demand
  priority: low
  description: "Optional AI suggestions"
```

### Example 2: IDE-Specific Configurations

```yaml
# Windsurf - Everything always on
windsurf:
  frontmatter_defaults_rules:
    trigger: always_on
  frontmatter_defaults_workflows:
    trigger: always_on

# VS Code - More selective
vscode:
  frontmatter_defaults_rules:
    trigger: always_on
  frontmatter_defaults_workflows:
    trigger: manual  # Manual activation in VS Code
```

### Example 3: Development vs Production

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
          priority: critical  # Higher priority in production
```

## Migration from Legacy Config

Old configurations using single `frontmatter_defaults` continue to work:

```yaml
# Old way (still works)
frontmatter_defaults:
  trigger: always_on
  priority: high

# New way (more flexible)
frontmatter_defaults_rules:
  trigger: always_on
  priority: critical
frontmatter_defaults_workflows:
  trigger: manual
  priority: high
```

The system automatically falls back to the legacy config if content-type-specific configs aren't defined.

## Best Practices

### 1. Match Content Type to Trigger

| Content Type | Recommended Trigger | Reason |
|--------------|---------------------|--------|
| Rules | `always_on` | Coding standards should always apply |
| Workflows | `manual` | Process guides used when needed |
| Prompts | `on_demand` | AI suggestions on-demand |
| Instructions | `always_on` | General guidance always available |

### 2. Use Priority Appropriately

- **critical**: Security rules, production standards
- **high**: General coding standards, team conventions
- **medium**: Style guides, suggestions
- **low**: Optional tips, experimental features

### 3. Tag Consistently

Use hierarchical tags:
```yaml
tags: [ide-name, team-name, content-type, environment]
# Example: [windsurf, platform-team, rules, production]
```

### 4. Keep Descriptions Brief

```yaml
# Good
description: "Team coding rules"

# Too verbose
description: "These are the coding rules that the team has agreed upon and should be followed by all developers when writing code"
```

## Schema Reference

The `IDEProfile` schema includes:

```python
@dataclass
class IDEProfile:
    name: str
    display_name: str
    paths: IDEPaths
    
    # Per-content-type configs
    frontmatter_defaults_rules: Optional[FrontmatterConfig] = None
    frontmatter_defaults_workflows: Optional[FrontmatterConfig] = None
    frontmatter_defaults_prompts: Optional[FrontmatterConfig] = None
    frontmatter_defaults_instructions: Optional[FrontmatterConfig] = None
    
    # Legacy fallback
    frontmatter_defaults: FrontmatterConfig = field(default_factory=FrontmatterConfig)
    enabled: bool = True
    
    def get_frontmatter_for_type(self, content_type: ContentType) -> FrontmatterConfig:
        """Get frontmatter config for specific content type with fallback"""
        # Returns content-type-specific config or falls back to general config
```

## Troubleshooting

### Frontmatter Not Applied

Check these in order:

1. **Is the content type configured?**
   ```yaml
   frontmatter_defaults_rules:  # ✅ Configured
   frontmatter_defaults_workflows:  # ❌ Missing - will use fallback
   ```

2. **Does the file already have valid frontmatter?**
   - Existing valid frontmatter is preserved
   - Only missing/invalid frontmatter is added

3. **Is the profile active?**
   - Check `profile(action='list')` to see active profile

### Wrong Frontmatter Applied

- Verify you're using the right content type field name:
  - `frontmatter_defaults_rules` (not `frontmatter_defaults_rule`)
  - `frontmatter_defaults_workflows` (not `frontmatter_default_workflows`)

### Files in Wrong Directory

Check your `paths` configuration:
```yaml
paths:
  rules: ".windsurf/rules"  # Make sure this matches your IDE structure
  workflows: ".windsurf/workflows"
```

## See Also

- [V2 Architecture](./V2_ARCHITECTURE.md)
- [V2 File Tracking](./V2_FILE_TRACKING.md)
- [V2 Quick Start](./V2_QUICK_START.md)
