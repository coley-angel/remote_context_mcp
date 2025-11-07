# Team Configuration MCP Server 🚀

A comprehensive Model Context Protocol (MCP) server for managing team AI configurations across multiple IDEs (Windsurf, Cursor, VS Code). Centralize your team's rules, workflows, instructions, and prompts with built-in security validation and Git-based syncing.

## ✨ Key Features

### 🎯 Multi-IDE Support
- **Windsurf**: Full support for Cascade workflows
- **Cursor**: Native integration with AI features
- **VS Code**: GitHub Copilot and chat instructions
- Automatic detection and configuration syncing

### 📦 Content Management
- **Instructions**: AI guidance and coding guidelines
- **Rules**: Team coding standards and best practices
- **Workflows**: Development process definitions
- **Prompts**: Reusable AI prompt templates

### 🔒 Security & Compliance
- **Secret Scanning**: Detect API keys, tokens, passwords
- **PII Detection**: Find emails, SSNs, phone numbers
- **Pattern Matching**: Custom forbidden/required patterns
- **Security Levels**: None, Basic, Strict, Paranoid
- **Audit Trails**: Track all configuration changes

### 🌐 Git-Based Syncing
- **Central Repository**: Pull from team config repos
- **Auto-Update**: Periodic checks for changes
- **Branch Support**: Different configs per environment
- **Private Repos**: Token-based authentication

### ⚙️ Dynamic MCP Management
- **Server Configuration**: Manage MCP servers per profile
- **Hot Reload**: Update configs without restart
- **Environment-Specific**: Different servers per profile

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/remote_context_mcp
   cd remote_context_mcp
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your tokens
   ```

### Configuration

Create a `team_config.yaml` file (see `team_config_example.yaml` for full example):

```yaml
version: "1.0.0"
team_name: "Engineering Team"

# Global security settings
global_security:
  enabled: true
  level: "basic"  # none, basic, strict, paranoid
  scan_for_secrets: true
  scan_for_pii: true

# Profiles for different environments
profiles:
  default:
    active: true
    description: "Default development profile"
    
    # Instructions for AI
    instructions:
      - url: "https://raw.githubusercontent.com/your-org/guidelines/main/instructions.md"
      - repo: "your-org/dev-guidelines"
        branch: "main"
        paths: ["instructions/*.md"]
    
    # Coding rules
    rules:
      - url: "https://raw.githubusercontent.com/your-org/guidelines/main/rules.md"
    
    # Workflows
    workflows:
      - repo: "your-org/workflows"
        branch: "main"
        paths: ["workflows/*.md"]
    
    # MCP servers
    mcp_servers:
      - name: "github"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-github"]
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
        enabled: true
    
    # Security overrides
    security:
      enabled: true
      level: "basic"
```

### IDE Configuration

#### Windsurf

Add to `.windsurf/mcp.json`:
```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": ["run", "python", "/path/to/main.py"],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "TEAM_CONFIG_FILE": "/path/to/team_config.yaml"
      }
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "team-config": {
      "command": "uv",
      "args": ["run", "python", "/path/to/main.py"],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "TEAM_CONFIG_FILE": "/path/to/team_config.yaml"
      }
    }
  }
}
```

#### VS Code

Add to `.vscode/mcp.json`:
```json
{
  "servers": {
    "team-config": {
      "command": "uv",
      "args": ["run", "python", "/path/to/main.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "GITHUB_TOKEN": "${input:githubToken}",
        "TEAM_CONFIG_FILE": "team_config.yaml"
      }
    }
  }
}
```

## 📚 MCP Tools

### Core Tools

#### `sync_team_config`
Sync all team configuration content for a profile.

```python
# Usage in AI chat
sync_team_config(profile_name="default", force_update=False, sync_to_ides=True)
```

**Parameters:**
- `profile_name` (optional): Profile to sync (uses active if None)
- `force_update` (optional): Force pull from remote
- `sync_to_ides` (optional): Sync to all detected IDEs

**Returns:** JSON with sync results, security issues, and IDE sync status

#### `list_profiles`
List all available configuration profiles.

```python
list_profiles()
```

**Returns:** JSON with all profiles, content sources, MCP servers, and security settings

#### `set_active_profile`
Activate a specific configuration profile.

```python
set_active_profile(profile_name="corporate", auto_sync=True)
```

**Parameters:**
- `profile_name`: Name of profile to activate
- `auto_sync` (optional): Automatically sync after activation

**Returns:** JSON with activation status and optional sync results

### Update Management

#### `check_for_updates`
Check if central repositories have updates without pulling.

```python
check_for_updates()
```

**Returns:** JSON with update status for each profile's central repo

#### `reload_config`
Reload configuration from source.

```python
reload_config()
```

**Returns:** JSON with reload status

### Security Tools

#### `validate_content_security`
Validate content for security issues.

```python
validate_content_security(
    content="your content here",
    content_type="instruction",
    filename="test.md"
)
```

**Parameters:**
- `content`: Content to validate
- `content_type`: Type (instruction, rule, workflow, prompt, general)
- `filename`: Name of file being validated

**Returns:** JSON with validation results and violations

### MCP Server Management

#### `update_mcp_servers`
Update MCP server configurations for active profile.

```python
update_mcp_servers(profile_name="default", reload=True)
```

**Parameters:**
- `profile_name` (optional): Profile to use
- `reload` (optional): Reload IDE after updating

**Returns:** JSON with update results for all IDEs

#### `list_installed_ides`
Detect which IDEs are installed.

```python
list_installed_ides()
```

**Returns:** JSON with installed IDEs and their settings paths

### Utility Tools

#### `get_config`
Get the complete team configuration.

```python
get_config()
```

**Returns:** JSON with full configuration

#### `clear_cache`
Clear cached data.

```python
clear_cache(cache_type="all")  # Options: all, repos, content
```

**Returns:** JSON indicating what was cleared

## 🔧 Configuration Reference

### Profile Structure

```yaml
profiles:
  profile-name:
    active: true/false
    description: "Profile description"
    
    # Content sources
    instructions: [...]  # List of RemoteSource
    rules: [...]
    workflows: [...]
    prompts: [...]
    
    # MCP servers
    mcp_servers:
      - name: "server-name"
        command: "command"
        args: ["arg1", "arg2"]
        env:
          KEY: "value"
        enabled: true
    
    # Security settings
    security:
      enabled: true
      level: "basic"  # none, basic, strict, paranoid
      forbidden_patterns: ["pattern1", "pattern2"]
      required_patterns: ["pattern1"]
      scan_for_secrets: true
      scan_for_pii: true
      allowed_domains: ["github.com", "internal.company.com"]
    
    # Central repository
    central_repo:
      repo: "your-org/team-config"
      branch: "main"
      paths: ["profiles/default/**/*"]
      auto_pull: true
      pull_interval_minutes: 30
    
    tags: ["tag1", "tag2"]
```

### Remote Source Types

**Direct URL:**
```yaml
- url: "https://example.com/file.md"
```

**GitHub Repository:**
```yaml
- repo: "owner/repo-name"
  branch: "main"
  paths: ["path/*.md", "other/**/*.md"]
  token_env_var: "GITHUB_TOKEN"
  auto_pull: true
  pull_interval_minutes: 30
```

### Security Levels

- **None**: No security scanning
- **Basic**: Scan for secrets and PII, warn on violations
- **Strict**: Block on critical and high severity violations
- **Paranoid**: Block on any violations including medium severity

## 🏢 Team Workflows

### Scenario 1: Development Team

```yaml
profiles:
  dev-team:
    active: true
    instructions:
      - repo: "company/dev-instructions"
        branch: "main"
        paths: ["general/*.md"]
    rules:
      - repo: "company/coding-standards"
        branch: "main"
        paths: ["rules/*.md"]
    mcp_servers:
      - name: "github"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-github"]
        enabled: true
```

### Scenario 2: Corporate/Production

```yaml
profiles:
  corporate:
    active: false
    security:
      level: "strict"
      forbidden_patterns:
        - "eval\\("
        - "exec\\("
      allowed_domains:
        - "internal.company.com"
    instructions:
      - url: "https://internal.company.com/ai/corporate-guidelines.md"
    mcp_servers:
      - name: "filesystem"
        enabled: false  # Disabled for security
```

### Scenario 3: Security Team

```yaml
profiles:
  security-team:
    active: false
    security:
      level: "paranoid"
      scan_for_secrets: true
      scan_for_pii: true
      max_file_size_kb: 512
    instructions:
      - url: "https://internal.company.com/security/instructions.md"
    rules:
      - url: "https://internal.company.com/security/owasp-guidelines.md"
```

## 🔒 Security Best Practices

1. **Store tokens in environment variables**, never in config files
2. **Use security levels** appropriate for your environment
3. **Enable secret scanning** for all profiles
4. **Define forbidden patterns** for your organization
5. **Use allowed domains** to control content sources
6. **Regular audits** of configuration changes
7. **Private repositories** for sensitive configs

## 📊 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | None |
| `TEAM_CONFIG_FILE` | Path to team configuration | `team_config.yaml` |
| `MCP_BASE_DIR` | Base directory for MCP data | `~/.mcp-team-config` |
| `WORKSPACE_DIR` | Workspace directory | Current directory |

## 🐛 Troubleshooting

### Configuration not loading
- Check file path in `TEAM_CONFIG_FILE`
- Verify YAML syntax
- Check file permissions

### IDE not syncing
- Verify IDE is installed
- Check settings file paths
- Restart IDE after configuration changes

### Git repository errors
- Verify `GITHUB_TOKEN` is set
- Check repository access permissions
- For private repos, ensure token has repo scope

### Security violations
- Review violation details in sync results
- Adjust security level if needed
- Fix content issues or add exceptions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🔗 Related Projects

- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [MCP Servers](https://github.com/modelcontextprotocol/servers)

## 💡 Support

- Issues: [GitHub Issues](https://github.com/your-org/remote_context_mcp/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/remote_context_mcp/discussions)

---

**Made with ❤️ for better team collaboration across AI-powered IDEs**
