# Team Config MCP - V2 Usage Examples

## Quick Start

### 1. List Available IDE Configurations

```python
sync(action="list_ides")
```

**Result:**
```json
{
  "success": true,
  "profile": "default",
  "available_ides": [
    {"id": 1, "name": "windsurf", "display_name": "Windsurf"},
    {"id": 2, "name": "vscode", "display_name": "VS Code"},
    {"id": 3, "name": "cursor", "display_name": "Cursor"}
  ]
}
```

### 2. Sync Rules to Windsurf

```python
sync(
    action="full",
    workspace_path="/Users/username/my-project",
    ide_choice=1  # Windsurf
)
```

**Creates:**
```
/Users/username/my-project/
└── .windsurf/
    ├── coding-standards.team-config.default.md
    ├── security-rules.team-config.default.md
    └── workflow-guide.team-config.default.md
```

### 3. Add Your Own Custom Rules

```bash
cd /Users/username/my-project/.windsurf
echo "# My Custom Rule" > my-custom-rule.md
```

**Result:**
```
.windsurf/
├── coding-standards.team-config.default.md  # Team-managed
├── security-rules.team-config.default.md    # Team-managed
├── workflow-guide.team-config.default.md    # Team-managed
└── my-custom-rule.md                         # YOUR FILE (preserved)
```

### 4. Switch to Production Profile

```python
profile(
    action="activate",
    profile_name="production",
    workspace_path="/Users/username/my-project"
)
```

**What Happens:**
```
✓ Removes: coding-standards.team-config.default.md
✓ Removes: security-rules.team-config.default.md
✓ Removes: workflow-guide.team-config.default.md
✓ KEEPS: my-custom-rule.md  # YOUR FILE PRESERVED!
```

### 5. Sync Production Rules

```python
sync(
    action="full",
    workspace_path="/Users/username/my-project",
    ide_choice=1  # Windsurf
)
```

**Creates:**
```
.windsurf/
├── prod-security.team-config.production.md   # New team files
├── prod-compliance.team-config.production.md
├── prod-workflow.team-config.production.md
└── my-custom-rule.md                          # YOUR FILE STILL HERE!
```

## Complete Workflow Example

### Scenario: Developer Using Windsurf

```python
# Step 1: Check current profile
profile(action="show")
# Shows: "default" profile is active

# Step 2: List available IDE configs
sync(action="list_ides")
# Shows: Windsurf (1), VS Code (2), Cursor (3)

# Step 3: Sync default profile to Windsurf
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=1
)
# Creates: .windsurf/*.team-config.default.md

# Step 4: Create custom rules
# Manually create: .windsurf/my-team-conventions.md

# Step 5: Switch to production profile
profile(
    action="activate",
    profile_name="production",
    workspace_path="/Users/dev/my-app"
)
# Removes: *.team-config.default.md
# Keeps: my-team-conventions.md

# Step 6: Sync production rules
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=1
)
# Creates: .windsurf/*.team-config.production.md
# Still keeps: my-team-conventions.md
```

## Multi-IDE Support

### Sync to Multiple IDEs

```python
# Sync to Windsurf
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=1
)

# Sync to VS Code
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=2
)

# Sync to Cursor
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=3
)
```

**Result:**
```
/Users/dev/my-app/
├── .windsurf/
│   ├── rule1.team-config.default.md
│   └── rule2.team-config.default.md
├── .vscode/
│   └── rules/
│       ├── rule1.team-config.default.md
│       └── rule2.team-config.default.md
└── .cursor/
    └── rules/
        ├── rule1.team-config.default.md
        └── rule2.team-config.default.md
```

## Profile Management

### List All Profiles

```python
profile(action="list")
```

**Result:**
```json
{
  "success": true,
  "profiles": {
    "default": {
      "active": true,
      "description": "General development profile"
    },
    "production": {
      "active": false,
      "description": "Production with strict controls"
    }
  }
}
```

### Activate Profile (Without Cleanup)

```python
# Just activate, don't cleanup old files
profile(
    action="activate",
    profile_name="production"
)
```

**Result:**
- Profile activated in config
- Old team files remain (can coexist temporarily)
- Next sync will add production files

### Activate Profile (With Cleanup)

```python
# Activate and cleanup old team files
profile(
    action="activate",
    profile_name="production",
    workspace_path="/Users/dev/my-app"
)
```

**Result:**
- Profile activated in config
- Old team files removed: `*.team-config.default.*`
- User files preserved: `*.md` (without suffix)

## File Naming Convention

### Team-Managed Files
```
{original-name}.team-config.{profile}.{extension}

Examples:
- coding-standards.team-config.default.md
- security-rules.team-config.production.md
- workflow-guide.team-config.staging.md
```

### User Files
```
{name}.{extension}

Examples:
- my-custom-rule.md
- team-conventions.md
- local-config.md
```

## Advanced Usage

### Sync Specific Profile

```python
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_choice=1,
    profile_name="staging"  # Use specific profile
)
```

### Use IDE Name Instead of Number

```python
sync(
    action="full",
    workspace_path="/Users/dev/my-app",
    ide_name="windsurf"  # Use name instead of number
)
```

### Check for Updates

```python
sync(action="check")
```

### Reload Configuration

```python
sync(action="reload")
```

## Common Scenarios

### Scenario 1: New Project Setup

```python
# 1. Sync default profile
sync(
    action="full",
    workspace_path="/Users/dev/new-project",
    ide_choice=1
)

# Result: Team rules loaded to .windsurf/
```

### Scenario 2: Switch Between Environments

```python
# Development -> Staging
profile(
    action="activate",
    profile_name="staging",
    workspace_path="/Users/dev/project"
)

sync(
    action="full",
    workspace_path="/Users/dev/project",
    ide_choice=1
)

# Result: Dev rules removed, staging rules loaded, user files kept
```

### Scenario 3: Multiple Team Members

**Team Member A (Windsurf):**
```python
sync(action="full", workspace_path="/shared/project", ide_choice=1)
```

**Team Member B (VS Code):**
```python
sync(action="full", workspace_path="/shared/project", ide_choice=2)
```

**Team Member C (Cursor):**
```python
sync(action="full", workspace_path="/shared/project", ide_choice=3)
```

**Result:** All team members get same rules, in their preferred IDE format

### Scenario 4: Clean Slate

```bash
# Remove ALL team files manually
cd /Users/dev/project/.windsurf
rm *.team-config.*.md

# Sync fresh
sync(action="full", workspace_path="/Users/dev/project", ide_choice=1)
```

## Error Handling

### Missing Workspace Path

```python
sync(action="full", ide_choice=1)
# Error: "workspace_path is required"
```

### Missing IDE Selection

```python
sync(action="full", workspace_path="/path")
# Error: "IDE selection required"
# Shows available options: 1=Windsurf, 2=VS Code, 3=Cursor
```

### Invalid Profile

```python
profile(action="activate", profile_name="nonexistent")
# Error: "Profile 'nonexistent' not found"
# Shows available profiles
```

## Tips & Best Practices

### ✅ DO

1. **Always provide workspace_path** for consistent results
2. **Use descriptive custom file names** (no suffix)
3. **Commit team files to git** if desired (`.team-config` files)
4. **Keep user files separate** (no `.team-config` suffix)
5. **Use profile switching** to manage environments

### ❌ DON'T

1. **Don't manually rename team files** (breaks tracking)
2. **Don't edit team files** (will be overwritten on sync)
3. **Don't rely on auto-sync** (V2 requires explicit IDE choice)
4. **Don't mix profile files** (use profile switching instead)

## Troubleshooting

### Team Files Not Removed on Profile Switch

**Check:**
```python
# Did you provide workspace_path?
profile(
    action="activate",
    profile_name="new-profile",
    workspace_path="/path/to/project"  # REQUIRED for cleanup
)
```

### Can't Find My Custom Files

**Check file names:**
```bash
# Your files should NOT have .team-config suffix
ls -la .windsurf/

# Good:
my-rule.md  # Yours
their-rule.team-config.default.md  # Team

# Bad (will be deleted on profile switch):
my-rule.team-config.myprofile.md
```

### Multiple Versions of Same File

```bash
# This happens if you switch profiles without cleanup
ls .windsurf/
rule.team-config.default.md
rule.team-config.production.md
rule.team-config.staging.md

# Fix: Activate profile WITH workspace_path to cleanup
profile(action="activate", profile_name="default", workspace_path="/path")
```

## Summary

**Key Concepts:**
- **Team files**: `*.team-config.{profile}.*` - Managed by MCP
- **User files**: `*.md` (no suffix) - Preserved always
- **Profile switching**: Removes old team files, keeps user files
- **Multi-IDE**: Same rules, different locations

**Main Commands:**
- `sync(action="list_ides")` - See available IDEs
- `sync(..., ide_choice=N)` - Sync to IDE
- `profile(action="activate", ...)` - Switch profiles
