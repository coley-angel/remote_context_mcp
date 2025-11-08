# Cursor MDC (Markdown with Configuration) Format Guide

## Overview

Cursor AI uses **MDC (Markdown with Configuration)** format for rules - Markdown files with YAML frontmatter that control how and when rules are applied. The Team Config MCP server fully supports this format and allows you to set default frontmatter values in your team configuration.

## MDC Format Structure

```markdown
---
trigger: always_on
glob: *.py
description: Python coding standards
priority: high
tags: [python, pep8, style]
author: Platform Team
version: 1.0.0
---

# Rule Content Here

Your rule content in Markdown...
```

## Frontmatter Fields

### `trigger` (string, **required**)
Controls when the rule is active:
- **`always_on`** - Rule is always active in all contexts (default)
- **`manual`** - Rule must be manually enabled by the user
- **`on_demand`** - Rule activates only when explicitly mentioned

**Example:**
```yaml
trigger: always_on
```

### `glob` (string, optional)
File pattern to match. Rules only apply to files matching this pattern.

**Supported patterns:**
- `*.py` - All Python files
- `*.{js,ts}` - JavaScript and TypeScript files
- `src/**/*.tsx` - TSX files in src directory
- `test_*.py` - Python test files
- `**/*.md` - All Markdown files in any directory

**Example:**
```yaml
glob: *.{js,ts,jsx,tsx}
```

### `description` (string, optional)
Human-readable description of what the rule does.

**Example:**
```yaml
description: Python PEP8 style guide with project conventions
```

### `priority` (string, optional)
Indicates importance of the rule:
- `critical` - Must always be followed
- `high` - Strongly recommended
- `medium` - Should be followed when applicable
- `low` - Nice to have

**Example:**
```yaml
priority: high
```

### `tags` (array, optional)
Categories or keywords for organizing rules.

**Example:**
```yaml
tags: [python, testing, pytest]
```

### `author` (string, optional)
Who created or maintains this rule.

**Example:**
```yaml
author: Platform Team
```

### `version` (string, optional)
Version of the rule (useful for tracking changes).

**Example:**
```yaml
version: 1.2.0
```

## Configurable Default Frontmatter

The Team Config MCP server allows you to set default frontmatter values in your `team_config.yaml`. This ensures all synced rules have consistent metadata.

### Configuration in `team_config.yaml`

```yaml
profiles:
  default:
    active: true
    description: "Development profile"
    
    # Default frontmatter for all rules
    frontmatter_defaults:
      trigger: always_on
      glob: null  # No default glob pattern
      description: null
      priority: high
      tags: [development, team-standards]
      author: Platform Team
      version: 1.0.0
    
    rules:
      - repo: your-org/coding-standards
        paths: ["rules/*.md"]
```

### How It Works

1. **Rules fetched from GitHub** without frontmatter get default values added
2. **Rules with existing frontmatter** are left unchanged
3. **Invalid frontmatter** is replaced with defaults
4. **Frontmatter format** follows MDC spec (YAML format)

### Example: Rule Without Frontmatter

**Original (from GitHub):**
```markdown
# Python Style Guide

Always use snake_case for variables...
```

**After Sync (with defaults applied):**
```markdown
---
trigger: always_on
priority: high
tags: [development, team-standards]
author: Platform Team
version: 1.0.0
---

# Python Style Guide

Always use snake_case for variables...
```

## Complete Examples

### Example 1: Python Style Guide

```markdown
---
trigger: always_on
glob: *.py
description: Python PEP8 style guide
priority: critical
tags: [python, pep8, style]
author: Backend Team
version: 2.0.0
---

# Python Style Guide

## Naming Conventions

### Functions and Variables
- Use `snake_case` for functions and variables
- Use descriptive names: `calculate_total_price()` not `calc()`

### Classes
- Use `PascalCase` for class names
- Example: `UserProfileManager`, `DatabaseConnection`

## Type Hints
Always use type hints:

```python
def process_data(user_id: int, data: dict[str, Any]) -> UserProfile:
    """Process user data and return profile."""
    pass
```
```

### Example 2: React Component Standards

```markdown
---
trigger: always_on
glob: *.{tsx,jsx}
description: React and TypeScript component standards
priority: high
tags: [react, typescript, frontend]
author: Frontend Team
version: 1.5.0
---

# React Component Standards

## Functional Components

Use functional components with TypeScript interfaces:

```typescript
interface UserCardProps {
  userId: string;
  name: string;
  onEdit?: (userId: string) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ 
  userId, 
  name, 
  onEdit 
}) => {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      {onEdit && <button onClick={() => onEdit(userId)}>Edit</button>}
    </div>
  );
};
```
```

### Example 3: Test Standards (On-Demand)

```markdown
---
trigger: on_demand
glob: test_*.py
description: Python testing standards
priority: critical
tags: [python, testing, pytest]
author: QA Team
version: 1.0.0
---

# Testing Standards

## Test Structure

Use Arrange-Act-Assert pattern:

```python
def test_user_creation():
    # Arrange
    user_data = {"name": "John"}
    
    # Act
    user = User.create(user_data)
    
    # Assert
    assert user.name == "John"
```
```

## Profile-Specific Defaults

You can set different frontmatter defaults for different profiles:

```yaml
profiles:
  # Development profile - lenient
  development:
    active: false
    frontmatter_defaults:
      trigger: always_on
      priority: medium
      tags: [dev, experimental]
      author: Dev Team
  
  # Production profile - strict
  production:
    active: true
    frontmatter_defaults:
      trigger: always_on
      priority: critical
      tags: [production, mandatory]
      author: Platform Team
      version: 2.0.0
  
  # Security profile - paranoid settings
  security:
    active: false
    frontmatter_defaults:
      trigger: always_on
      glob: "**/*.{py,js,ts}"
      priority: critical
      tags: [security, compliance, audit]
      author: Security Team
      version: 1.0.0
```

## Best Practices

### 1. Use Specific Glob Patterns

**Good:**
```yaml
glob: *.py              # Python only
glob: *.{ts,tsx}        # TypeScript/TSX only
glob: src/**/*.js       # JS in src directory
```

**Avoid:**
```yaml
glob: "*"               # Too broad
```

### 2. Set Appropriate Triggers

- **`always_on`** for core standards everyone must follow
- **`manual`** for experimental or optional guidelines
- **`on_demand`** for context-specific rules (e.g., testing, migrations)

### 3. Use Meaningful Tags

```yaml
tags: [python, backend, api, rest]  # Good - specific and searchable
tags: [code]                         # Bad - too generic
```

### 4. Version Your Rules

```yaml
version: 1.0.0  # Initial version
version: 1.1.0  # Minor updates
version: 2.0.0  # Breaking changes
```

### 5. Document With Priority

```yaml
priority: critical  # Security, compliance, must-follow
priority: high      # Strong recommendations
priority: medium    # Best practices
priority: low       # Stylistic preferences
```

## Validation

The MCP server validates frontmatter when syncing rules:

### Valid Frontmatter
```markdown
---
trigger: always_on
glob: *.py
---
# Rule content
```

### Invalid Frontmatter (Will Be Replaced)
```markdown
---
trigger: invalid_value
---
# Rule content
```

### Missing Frontmatter (Will Be Added)
```markdown
# Rule content with no frontmatter
```

## IDE Integration

### Cursor
Rules are synced to:
- **Workspace**: `{project}/.cursor/rules/`
- **Global**: `~/.cursor/rules/`

### VS Code
Rules are synced to:
- **Workspace**: `{project}/.vscode/rules/`
- **Global**: `~/.vscode/rules/`

### Windsurf
Rules are synced to:
- **Workspace**: `{project}/.windsurf/`
- **Global**: `~/.windsurf/`

## Migration from Old Format

If you have rules without frontmatter:

1. **Update your config** with frontmatter_defaults
2. **Run sync** - MCP will add frontmatter automatically
3. **Review** the generated frontmatter
4. **Push back to GitHub** if needed

**Before:**
```markdown
# My Rule
Content here...
```

**After (auto-added):**
```markdown
---
trigger: always_on
priority: high
tags: [team-standards]
author: Platform Team
version: 1.0.0
---

# My Rule
Content here...
```

## Troubleshooting

### Rules Not Being Applied

1. **Check frontmatter syntax** - Must be valid YAML
2. **Verify trigger value** - Must be `always_on`, `manual`, or `on_demand`
3. **Check glob pattern** - Must match your file extensions
4. **Review IDE logs** - Look for parsing errors

### Frontmatter Not Being Added

1. **Check profile config** - Ensure `frontmatter_defaults` is set
2. **Run diagnose_config()** - Verify config is loaded
3. **Check sync logs** - Look for frontmatter processing messages

### Custom Fields Not Showing

The MCP server supports these standard fields. Custom fields in the config are ignored but custom fields in existing rules are preserved.

##summary

- **MDC Format** = Markdown + YAML frontmatter
- **Cursor compatible** - Uses standard Cursor format
- **Configurable defaults** - Set in `team_config.yaml`
- **Auto-applied** - Missing frontmatter is added automatically
- **Validated** - Invalid frontmatter is replaced
- **Profile-specific** - Different defaults per profile

This ensures all team rules have consistent, valid metadata that works across all supported IDEs!
