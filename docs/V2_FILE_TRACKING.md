# V2 File Tracking System

## Overview

Team Config MCP manages files synced from remote sources. When switching profiles, we need to:
- ✅ Remove team-managed files from the old profile
- ✅ Preserve user-created files
- ✅ Track which profile created which files

## Solution: Metadata Files

### File Naming Convention

**Team-managed files** are tracked in a metadata file per IDE directory:
```
.windsurf/.team-config-manifest.json
.cursor/rules/.team-config-manifest.json
.vscode/rules/.team-config-manifest.json
```

### Manifest Format

```json
{
  "profile": "default",
  "ide": "windsurf",
  "synced_at": "2025-11-07T19:40:00Z",
  "files": {
    "rules": [
      {
        "path": "rule1.md",
        "source": "https://github.com/org/repo/blob/main/rules/rule1.md",
        "hash": "abc123...",
        "synced_at": "2025-11-07T19:40:00Z"
      }
    ],
    "workflows": [
      {
        "path": "workflow1.md",
        "source": "https://github.com/org/repo/blob/main/workflows/workflow1.md",
        "hash": "def456...",
        "synced_at": "2025-11-07T19:40:00Z"
      }
    ]
  }
}
```

### Alternative: File Suffix (Simpler)

**Append profile name to team-managed files:**
```
.windsurf/
  ├── rule1.team-config.default.md      # Team-managed (default profile)
  ├── rule2.team-config.default.md      # Team-managed
  ├── my-custom-rule.md                  # User-created (preserved)
  └── workflow1.team-config.default.md   # Team-managed

.cursor/rules/
  ├── rule1.team-config.production.md   # Team-managed (production profile)
  ├── my-rule.md                         # User-created (preserved)
```

**Pattern**: `{original-name}.team-config.{profile}.md`

### Cleanup Logic

When switching from profile A to profile B:
1. List all files in IDE directory
2. Find files matching `*.team-config.{profile-a}.*`
3. Delete only those files
4. Sync new files with `*.team-config.{profile-b}.*` suffix

## Implementation

### 1. Update sync_with_ide_config()

```python
async def sync_with_ide_config(...):
    # ... existing code ...
    
    # Save files with team-config suffix
    for file_path, content in files.items():
        original_name = Path(file_path).stem
        extension = Path(file_path).suffix
        
        # Add team-config suffix
        managed_name = f"{original_name}.team-config.{profile.name}{extension}"
        target_file = rules_dir / managed_name
        
        target_file.write_text(content_with_frontmatter)
```

### 2. Add cleanup_profile_files()

```python
def cleanup_profile_files(
    workspace_dir: Path,
    profile_name: str,
    ide_config: IDEProfile
) -> List[str]:
    """
    Remove team-managed files for a specific profile.
    
    Args:
        workspace_dir: Workspace root
        profile_name: Profile to clean up
        ide_config: IDE configuration with paths
    
    Returns:
        List of deleted file paths
    """
    deleted = []
    pattern = f"*.team-config.{profile_name}.*"
    
    # Check each content directory
    for content_type in ['rules', 'workflows', 'prompts', 'instructions']:
        content_dir = workspace_dir / getattr(ide_config.paths, content_type)
        if not content_dir.exists():
            continue
        
        # Find and delete team-managed files
        for file in content_dir.glob(pattern):
            try:
                file.unlink()
                deleted.append(str(file.relative_to(workspace_dir)))
                logger.info(f"✓ Removed team file: {file.relative_to(workspace_dir)}")
            except Exception as e:
                logger.warning(f"Failed to remove {file}: {e}")
    
    return deleted
```

### 3. Update profile activate action

```python
async def set_active_profile(profile_name: str, auto_sync: bool = True) -> str:
    # ... existing code ...
    
    # Find previously active profile
    previously_active = next((p.name for p in config.profiles.values() if p.active), None)
    
    # Deactivate all profiles
    for p in config.profiles.values():
        p.active = False
    
    # Activate new profile
    profile.active = True
    
    # Cleanup old profile files if switching
    if previously_active and previously_active != profile_name:
        logger.info(f"Cleaning up files from profile '{previously_active}'")
        
        # Get old profile's IDE configs
        old_profile = config.profiles.get(previously_active)
        if old_profile:
            cleanup_results = {}
            for ide_name, ide_config in old_profile.ide_configs.items():
                deleted = cleanup_profile_files(
                    workspace_dir,
                    previously_active,
                    ide_config
                )
                if deleted:
                    cleanup_results[ide_name] = deleted
            
            logger.info(f"Cleaned up {sum(len(v) for v in cleanup_results.values())} files")
    
    # ... rest of code ...
```

## Benefits

### Using Suffix Approach

**Pros:**
- ✅ Simple to implement
- ✅ Files are self-documenting (name shows origin)
- ✅ No separate manifest file needed
- ✅ Easy to identify team vs user files
- ✅ Works with git (clear file names)
- ✅ Can have multiple profiles' files coexist temporarily

**Cons:**
- ⚠️ Longer file names
- ⚠️ User sees `.team-config.{profile}` in names

### Using Manifest File Approach

**Pros:**
- ✅ Clean file names (no suffix)
- ✅ Can store additional metadata
- ✅ More flexibility

**Cons:**
- ⚠️ More complex implementation
- ⚠️ Manifest can get out of sync
- ⚠️ Harder to debug

## Recommendation

**Use Suffix Approach** for simplicity and clarity:
- `*.team-config.{profile}.md` for team-managed files
- Regular names for user files
- Simple glob pattern for cleanup
- Self-documenting

## Migration

### For Existing Users

Old files (without suffix) are treated as user files:
1. First sync adds suffix to new files
2. Old files without suffix remain (user files)
3. User can manually rename or delete old files

### Configuration Option

Add to profile config:
```yaml
profiles:
  default:
    # File management options
    file_suffix: ".team-config.{profile}"  # Default
    # Or disable: file_suffix: ""
```

## Example Workflow

```python
# 1. User on "default" profile
sync(action='full', workspace_path='/project', ide_choice=1)
# Creates: rule1.team-config.default.md

# 2. User creates custom rule
# Creates: my-custom-rule.md (manually)

# 3. Switch to "production" profile
profile(action='activate', profile_name='production')
# Removes: rule1.team-config.default.md
# Keeps: my-custom-rule.md

# 4. Sync production profile
sync(action='full', workspace_path='/project', ide_choice=1)
# Creates: rule1.team-config.production.md
# Still keeps: my-custom-rule.md
```

## Implementation Priority

1. ✅ Add suffix to synced files
2. ✅ Add cleanup_profile_files() function
3. ✅ Update profile activate to call cleanup
4. ✅ Add tests
5. ⏸️ Add configuration option (later)
6. ⏸️ Add manifest approach (if needed)
