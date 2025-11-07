# Team Configuration MCP Server

A Model Context Protocol (MCP) server for managing team-wide configuration including rules, instructions, workflows, prompts, and MCP servers across multiple IDEs (VS Code, Cursor, Windsurf).

## Features

- **📋 Profile-Based Configuration**: Manage multiple configuration profiles for different teams/contexts
- **🔄 Multi-IDE Support**: Sync configurations across VS Code, Cursor, and Windsurf
- **📝 Rules Management**: Manage IDE rules with frontmatter validation (trigger, glob patterns)
- **🔒 Security Validation**: Built-in security scanning for secrets, PII, and dangerous patterns
- **🌐 Remote Content**: Fetch content from GitHub repositories and URLs
- **🛠️ MCP Server Management**: Configure and manage MCP servers per profile
- **🧹 Auto Cleanup**: Removes rules when profiles are deactivated

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/coley-angel/remote_context_mcp.git
   cd remote_context_mcp
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up environment variables:
   ```bash
   export GITHUB_TOKEN="your_github_token"  # For private repos
   ```

## Configuration

Create a `team_config.yaml` file:

```yaml
version: 1.0.0
team_name: MyTeam
profiles:
  default:
    active: true
    description: Default team profile
    
    # Content sources
    instructions: []
    rules:
      - repo: owner/repo
        branch: main
        paths: ["rules/*.md"]
        token_env_var: GITHUB_TOKEN
    workflows: []
    prompts: []
    
    # MCP servers to install
    mcp_servers:
      - name: github
        command: npx
        args: ["-y", "@modelcontextprotocol/server-github"]
        enabled: true
    
    # Security settings
    security:
      enabled: true
      level: basic  # none, basic, strict, paranoid
      scan_for_secrets: true
      scan_for_pii: true
```

## MCP Tools

The server exposes **6 consolidated tools** with action-based interfaces:

### Profile Management: `profile()`

Unified tool for all profile operations:
- **`profile(action="list")`** - List all configuration profiles
- **`profile(action="activate", profile_name="...")`** - Switch active profile (auto-cleans previous)
- **`profile(action="show")`** - View current configuration
- **`profile(action="cleanup", profile_name="...")`** - Manually cleanup rules for a profile

### Synchronization: `sync()`

Sync configurations from remote repositories:
- **`sync(action="full")`** - Full sync of profile content to IDEs
- **`sync(action="check")`** - Check for updates without syncing
- **`sync(action="reload")`** - Reload configuration from source

### IDE Management: `ide()`

Detect and configure IDE settings:
- **`ide(action="info")`** - Get current IDE information
- **`ide(action="list")`** - List all installed IDEs
- **`ide(action="set", ide_name="...")`** - Manually set IDE (vscode, cursor, windsurf)

### MCP Server Management: `mcp_servers()`

Configure MCP servers per profile:
- **`mcp_servers(action="list")`** - List configured MCP servers
- **`mcp_servers(action="update")`** - Update MCP server configs (respects manual configs)

### Utility Tools

- **`validate_content_security(content, content_type, filename)`** - Scan content for security issues
- **`clear_cache(cache_type="all")`** - Clear cached repositories and content

### MCP Server Management

The system intelligently manages MCP servers with **strict protection guarantees**:

**Protection Rules:**
- ✅ **NEVER removes** servers without `_managed_by: team-config` marker
- ✅ **NEVER modifies** servers without `_managed_by: team-config` marker  
- ✅ **NEVER touches** manually configured servers
- ✅ **Always preserves** your custom MCP servers

**Server Types:**
- **Managed Servers**: Have `_managed_by: team-config` marker → Fully managed by team-config
- **Manual Servers**: No marker → Completely protected from team-config
- **Override**: To let team-config manage an existing server, add `"_managed_by": "team-config"` to it

**Example**: If your MCP config has:
```json
{
  "mcpServers": {
    "my-custom-server": {
      "command": "node",
      "args": ["./my-server.js"]
      // No _managed_by marker - will NOT be touched by team-config
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "_managed_by": "team-config"  // Will be managed by team-config
    }
  }
}
```

The team-config system will update/remove `github` but will never touch `my-custom-server`.

## Rules with Frontmatter

All rule files must include frontmatter:

```markdown
---
trigger: always_on  # or: manual, on_demand
glob: *.py          # optional: file pattern
description: Python style guide  # optional
---

# Rule Content Here
```

The server automatically validates and adds frontmatter if missing (defaults to `always_on`).

## IDE-Specific Behavior

### Default IDE Paths

**Windsurf**
- Rules: `~/.windsurf/` (global)
- MCP Config: `~/.codeium/windsurf/mcp_config.json`
- Settings: `~/.windsurf/settings.json` (macOS)

**VS Code**
- Rules: `.vscode/rules/` (workspace)
- MCP Config: `.vscode/mcp.json`
- Settings: `~/Library/Application Support/Code/User/settings.json` (macOS)

**Cursor**
- Rules: `.cursor/rules/` (workspace)
- MCP Config: `.cursor/mcp.json`
- Settings: `~/Library/Application Support/Cursor/User/settings.json` (macOS)

### Custom IDE Configuration

You can define custom IDEs or override default paths in `team_config.yaml`:

```yaml
ide_configs:
  # Define a custom IDE
  my_ide:
    name: "my_ide"
    display_name: "My Custom IDE"
    instructions_key: "myide.instructionsFilesLocations"
    supports_mcp: true
    darwin_paths:
      settings_path: "~/.myide/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
    win32_paths:
      settings_path: "~/AppData/Roaming/MyIDE/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
    linux_paths:
      settings_path: "~/.config/myide/settings.json"
      mcp_config_path: ".myide/mcp.json"
      rules_path: ".myide/rules"
```

This allows the server to support **any IDE** by defining where files should be placed.

## Security Features

The security validator scans content for:

- **Secrets**: API keys, tokens, passwords, private keys
- **PII**: Emails, SSNs, phone numbers, credit cards
- **Dangerous Code**: eval(), exec(), shell=True
- **Custom Patterns**: Forbidden/required patterns
- **File Size**: Configurable limits

Security levels:
- `none` - No validation
- `basic` - Blocks critical issues (secrets)
- `strict` - Blocks critical + high severity
- `paranoid` - Blocks all issues

## Development

### Project Structure

```
remote_context_mcp/
├── main.py                 # MCP server entry point
├── ide_manager.py          # IDE configuration management
├── frontmatter_utils.py    # Rule frontmatter handling
├── security_validator.py   # Security scanning
├── config_loader.py        # Configuration loading
├── schemas.py              # Data models
├── tests/                  # Test files
│   ├── test_frontmatter.py
│   ├── test_mcp_tools.py
│   └── test_server.py
└── docs/                   # Documentation
    ├── MIGRATION.md
    ├── IDE_DETECTION.md
    └── TRACKING_SYSTEM.md
```

### Running Tests

```bash
# Test frontmatter utilities
python tests/test_frontmatter.py

# Test MCP tools
python tests/test_mcp_tools.py

# Test server components
python tests/test_server.py
```

### Adding IDE Support

The server automatically detects installed IDEs. If your IDE isn't detected:

1. The server will prompt you to specify which IDE you're using
2. Or manually set via `set_ide` MCP tool
3. Only the IDE you're using will have configurations installed

## Workflow Example

1. **Create configuration profile**:
   ```yaml
   profiles:
     dev:
       active: true
       rules:
         - repo: myorg/coding-standards
           paths: ["rules/*.md"]
   ```

2. **Sync to your IDE**:
   ```
   Use MCP tool: sync(action="full", profile_name="dev")
   ```

3. **Switch profiles** (auto-cleans old rules):
   ```
   Use MCP tool: profile(action="activate", profile_name="production", auto_sync=True)
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure they pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

---

**Documentation**:
- [Migration Guide](docs/MIGRATION.md)
- [IDE Detection](docs/IDE_DETECTION.md)
- [Tracking System](docs/TRACKING_SYSTEM.md)
- [MCP Server Management](docs/MANAGED_SERVERS.md)
