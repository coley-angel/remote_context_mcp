# Remote Configuration Setup Guide

## Quick Start

Configure the MCP server to fetch `team_config.yaml` directly from your GitHub repository.

## Step 1: Add Environment Variables to MCP Config

Edit your `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/coangel/Documents/Development/CiscoOpsStack/remote_context_mcp",
        "python",
        "main.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_pat_token",
        "TEAM_CONFIG_REPO": "https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles",
        "TEAM_CONFIG_FILE": "team_config.yaml",
        "TEAM_CONFIG_BRANCH": "main"
      },
      "disabled": false
    }
  }
}
```

## Step 2: Restart Your IDE

- **Windsurf**: Restart the application
- **VS Code/Cursor**: Reload window (Cmd+Shift+P → "Reload Window")

## Step 3: Verify Configuration

After restart, the server will:
1. Read the environment variables
2. Construct the GitHub raw URL: `https://raw.githubusercontent.com/CiscoOpsStack/Ops_Stack_Dev_Profiles/main/team_config.yaml`
3. Fetch the configuration from GitHub
4. Create repository-specific directories: `~/.mcp-team-config/CiscoOpsStack_Ops_Stack_Dev_Profiles/`

Check the logs (in IDE console/stderr) for:
```
INFO - Loading config from GitHub: https://raw.githubusercontent.com/...
INFO - Using repo-specific directory: /Users/you/.mcp-team-config/CiscoOpsStack_Ops_Stack_Dev_Profiles
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TEAM_CONFIG_REPO` | No | - | Git repository URL (GitHub, GitLab, Bitbucket) |
| `TEAM_CONFIG_FILE` | No | `team_config.yaml` | Configuration filename in repo |
| `TEAM_CONFIG_BRANCH` | No | `main` | Git branch to fetch from |
| `GITHUB_TOKEN` | Yes* | - | Personal access token for authentication |

*Required for private repositories

## Supported Git Platforms

### GitHub
```
Input:  https://github.com/CiscoOpsStack/Ops_Stack_Dev_Profiles
Output: https://raw.githubusercontent.com/CiscoOpsStack/Ops_Stack_Dev_Profiles/main/team_config.yaml
```

### GitLab
```
Input:  https://gitlab.com/myorg/myrepo
Output: https://gitlab.com/myorg/myrepo/-/raw/main/team_config.yaml
```

### Bitbucket
```
Input:  https://bitbucket.org/myorg/myrepo
Output: https://bitbucket.org/myorg/myrepo/raw/main/team_config.yaml
```

## Benefits

1. **Centralized Configuration**: Single source of truth in your repository
2. **No Local Files**: No need to maintain local `team_config.yaml`
3. **Version Control**: All config changes tracked in Git
4. **Team Sync**: Everyone automatically gets updates
5. **Multi-Repo Support**: Switch repositories by changing environment variables

## Troubleshooting

### Configuration Not Loading

1. **Check URL**: Verify the repository exists and is accessible
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
     "https://raw.githubusercontent.com/CiscoOpsStack/Ops_Stack_Dev_Profiles/main/team_config.yaml"
   ```

2. **Check Token**: Ensure your GitHub token has `repo` scope for private repositories

3. **Check Logs**: Look for error messages in IDE console:
   - Windsurf: View → Output → Select "Windsurf MCP"
   - VS Code: View → Output → Select "MCP Server"

### Server Uses Wrong Configuration

1. Ensure `TEAM_CONFIG_REPO` environment variable is set in `mcp_config.json`
2. Restart the IDE (not just reload window)
3. Check the logs for "Loading config from GitHub" message

### Cache Issues

Clear the repository-specific cache:
```bash
rm -rf ~/.mcp-team-config/CiscoOpsStack_Ops_Stack_Dev_Profiles/cache
```

Then reload the configuration:
- Use MCP tool: `reload_config`
- Or restart the IDE

## Example Workflow

### Initial Setup
1. Create `team_config.yaml` in your repository
2. Push to GitHub
3. Add environment variables to MCP config
4. Restart IDE
5. Server fetches and uses remote config

### Making Changes
1. Edit `team_config.yaml` in your repository
2. Commit and push to GitHub
3. Team members' IDEs auto-sync (if `auto_update: true`)
4. Or manually sync with MCP tool: `sync_team_config`

### Switching Repositories
1. Update `TEAM_CONFIG_REPO` environment variable
2. Restart IDE
3. Server creates new repo-specific directory
4. Fetches configuration from new repository

## Security Notes

- **Never commit tokens to Git**: Use environment variables
- **Token Rotation**: Update `GITHUB_TOKEN` when rotating tokens
- **Private Repos**: Ensure token has `repo` scope
- **Public Repos**: Token still recommended to avoid rate limits
