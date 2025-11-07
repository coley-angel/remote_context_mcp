# Multi-Repository Support

## Overview

The team-config MCP server now supports working with multiple team configuration repositories on a single machine. Each repository gets its own isolated state, cache, and content directories.

## Directory Structure

When you configure a `central_repo_url` in your team_config.yaml, the MCP server automatically creates a repository-specific directory structure:

```
~/.mcp-team-config/
├── default/                    # Default config (no central_repo_url)
│   ├── cache/
│   ├── content/
│   └── backups/
├── CiscoOpsStack_Ops_Stack_Dev_Profiles/  # Repo-specific directory
│   ├── cache/
│   ├── content/
│   └── backups/
├── AnotherOrg_AnotherRepo/     # Another repo
│   ├── cache/
│   ├── content/
│   └── backups/
└── state/                      # Shared state for IDE workspace tracking
```

## How It Works

### Repository Directory Naming

The directory name is derived from the `central_repo_url`:

- **GitHub/GitLab/Bitbucket URLs**: `{org}_{repo}`
  - `https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles` → `CiscoOpsStack_Ops_Stack_Dev_Profiles`
  - `https://gitlab.com/myorg/myrepo` → `myorg_myrepo`

- **Other URLs**: `repo_{hash}`
  - Uses MD5 hash of the URL for unique identification

- **No URL (null)**: `default`
  - Used when `central_repo_url` is not configured

### Automatic Switching

When you change the `central_repo_url` in your configuration:

1. The MCP server reloads the config
2. Calculates the new repository directory name
3. Switches to use that directory for cache/content/backups
4. All subsequent operations use the new directory

### State Directory

The `state/` directory remains shared across all repositories because it tracks:
- IDE workspace associations
- Managed file tracking per IDE/workspace
- Cross-repository IDE state

This allows the same IDE installation to work with multiple team configs.

## Configuration

### Environment Variables

- **`TEAM_CONFIG_REPO`**: Remote Git repository URL for team configuration
  - Example: `https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles`
  - Supports: GitHub, GitLab, Bitbucket
  - If set, the server fetches `team_config.yaml` directly from the repository

- **`TEAM_CONFIG_FILE`**: Configuration filename in the repository
  - Default: `team_config.yaml`
  - Example: `team_config.yaml`, `config.yaml`

- **`TEAM_CONFIG_BRANCH`**: Git branch to fetch configuration from
  - Default: `main`
  - Example: `main`, `master`, `develop`

- **`GITHUB_TOKEN`**: GitHub Personal Access Token for private repositories
  - Required for private repositories
  - Example: `github_pat_...`

- **`MCP_BASE_DIR_ROOT`**: Override the base directory location
  - Default: `~/.mcp-team-config`
  - Example: `MCP_BASE_DIR_ROOT=/opt/team-configs`

### Example MCP Config

#### Remote Configuration (Recommended)

```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/remote_context_mcp",
        "python",
        "main.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "TEAM_CONFIG_REPO": "https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles",
        "TEAM_CONFIG_FILE": "team_config.yaml",
        "TEAM_CONFIG_BRANCH": "main"
      }
    }
  }
}
```

#### Local Configuration

```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/remote_context_mcp",
        "python",
        "main.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "MCP_BASE_DIR_ROOT": "~/.mcp-team-config"
      }
    }
  }
}
```

## Use Cases

### Working with Multiple Teams

```yaml
# Team A config
version: 1.0.0
team_name: Team A
central_repo_url: https://github.com/teamA/dev-config
# Uses ~/.mcp-team-config/teamA_dev-config/
```

```yaml
# Team B config  
version: 1.0.0
team_name: Team B
central_repo_url: https://github.com/teamB/engineering-standards
# Uses ~/.mcp-team-config/teamB_engineering-standards/
```

### Development vs Production

```yaml
# Development config
version: 1.0.0
team_name: Dev Team
central_repo_url: https://github.com/company/dev-config
# Uses ~/.mcp-team-config/company_dev-config/
```

```yaml
# Production config
version: 1.0.0
team_name: Prod Team  
central_repo_url: https://github.com/company/prod-config
# Uses ~/.mcp-team-config/company_prod-config/
```

## Benefits

1. **Isolation**: Each repository's cache and content don't interfere with others
2. **Parallel Usage**: Work with multiple team configurations simultaneously
3. **Clean Switching**: Change repositories without cache conflicts
4. **Preserved State**: Previous repository data remains available
5. **Shared IDE State**: IDE workspace tracking works across all configs

## Migration

Existing installations will continue using the default directory. After upgrading:

1. Restart the MCP server (restart your IDE)
2. The server will create `~/.mcp-team-config/default/` 
3. Sync your config to populate the new directory
4. Old data in `~/.mcp-team-config/` can be safely removed after verification

## Troubleshooting

### Check Current Directory

The MCP server logs the active directory on startup:
```
INFO - Using repo-specific directory: /Users/you/.mcp-team-config/CiscoOpsStack_Ops_Stack_Dev_Profiles
```

### Force Directory Cleanup

Remove a specific repository's cache:
```bash
rm -rf ~/.mcp-team-config/CiscoOpsStack_Ops_Stack_Dev_Profiles/cache
```

### Reset to Default

Remove the central_repo_url from your config:
```yaml
central_repo_url: null
```

The server will use `~/.mcp-team-config/default/`
