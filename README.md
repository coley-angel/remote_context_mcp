# Remote Context MCP Server 🏴‍☠️

A Model Context Protocol (MCP) server that intelligently fetches and manages remote context files for GitHub Copilot. This server automatically detects project types and frameworks, then fetches relevant instructions, prompts, and chat modes using a flexible profile-based system.

## 🌟 Features

- **🔍 Automatic Project Detection**: Detects Python, JavaScript, TypeScript, Rust, Go, and other project types
- **⚙️ Framework-Aware Context**: Identifies frameworks like React, Django, Flask, FastAPI, Next.js, Express, etc.
- **📁 Profile-Based Management**: Multiple context profiles per project type (e.g., "default", "dev", "production")
- **🎯 Smart Directory Organization**: Saves files to `.github/{profile}/instructions`, `.github/{profile}/chatmodes`, `.github/{profile}/prompts`
- **🔧 VS Code Integration**: Automatically updates VS Code settings with all available profiles as options
- **🌐 GitHub Integration**: Built-in support for fetching files from GitHub repositories with wildcard patterns
- **📊 Git Repository Analysis**: Extracts git metadata for additional context

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd mcp_get_remote_context
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Set up environment variables (optional):
   ```bash
   export GITHUB_TOKEN="your_github_token"  # For GitHub API access and private repos
   export CONTEXT_CONFIG_FILE="context_config.yaml"  # Config file location
   ```

## 💻 Usage

### Configure VS Code

Add the MCP server to your VS Code settings by creating or updating `.vscode/mcp.json`:

```json
{
  "servers": {
    "remote-context": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "GITHUB_TOKEN": "${input:githubToken}",
        "CONTEXT_CONFIG_FILE": "${input:configFile}",
        "CONTEXT_WORKDIR": "${input:workDir}"
      }
    }
  },
  "inputs": [
    {
      "id": "githubToken",
      "description": "GitHub Personal Access Token",
      "type": "promptString",
      "password": true
    },
    {
      "id": "configFile",
      "description": "Context configuration file path",
      "type": "promptString",
      "default": "context_config.yaml"
    },
    {
      "id": "workDir",
      "description": "Working directory",
      "type": "promptString",
      "default": "${workspaceFolder}"
    }
  ]
}
```

### Available MCP Tools

#### 🎯 Core Tools

1. **`fetch_and_setup_copilot_files`** - Main tool to fetch context files
   - Auto-detects project type and active profile
   - Downloads context files to profile-specific directories
   - Updates VS Code settings with all available profiles

2. **`get_workspace_context`** - Analyze current workspace
   - Detects project types and frameworks
   - Provides suggestions for context fetching

3. **`list_context_config`** - View current configuration
   - Shows all project types and their profiles
   - Displays URLs for each context type

#### 🏷️ Profile Management

4. **`set_active_profile`** - Switch active profile for a project type
   ```json
   {
     "project_type": "python",
     "profile_name": "default"
   }
   ```

5. **`get_available_profiles`** - List all profiles for a project type
   ```json
   {
     "project_type": "python"
   }
   ```

#### 🔧 Configuration Management

6. **`add_context_url`** - Add new URLs to active profile
   ```json
   {
     "project_type": "python",
     "url": "https://example.com/docs",
     "condition": "has_fastapi"
   }
   ```

7. **`remove_context_url`** - Remove URLs from active profile

## ⚙️ Configuration System

### Profile Structure

The configuration uses a hierarchical profile system:

```yaml
project_types:
  python:
    default:           # Profile name
      active: true     # Currently active profile
      always_fetch:
        instructions:
          - "https://python-docs.com/guidelines.md"
        chatmodes:
          - "https://python-docs.com/chat-modes.json"
        prompts:
          - "https://python-docs.com/prompts.md"
      conditional:
        has_django:
          instructions:
            - repo: "django/django-copilot"
              branch: "main"
              paths: ["instructions/*.md"]
    
    dev:               # Alternative profile
      active: false
      always_fetch:
        # Different URLs for development context
```

### Project Type Detection

Automatic detection based on file presence:

- **Python**: `requirements.txt`, `setup.py`, `pyproject.toml`, `__init__.py`
- **JavaScript**: `package.json`
- **TypeScript**: `package.json` + `tsconfig.json` or `.ts` files
- **Rust**: `Cargo.toml`
- **Go**: `go.mod` or `.go` files

### Framework Detection

Smart framework detection analyzes:

- **package.json** dependencies (React, Next.js, Express, TypeScript)
- **requirements.txt** content (Django, Flask, FastAPI)
- **pyproject.toml** dependencies
- Configuration files (`tsconfig.json`, `Cargo.toml`, etc.)

## 📂 Directory Structure

Context files are organized by profile:

```
.github/
├── default/              # Default profile
│   ├── instructions/     # Instruction files
│   ├── chatmodes/        # Chat mode configurations  
│   └── prompts/          # Prompt files
├── dev/                  # Development profile
│   ├── instructions/
│   ├── chatmodes/
│   └── prompts/
└── production/           # Production profile
    ├── instructions/
    ├── chatmodes/
    └── prompts/
```

## 🎯 Workflow Examples

### Basic Usage

1. **Fetch context for current project:**
   ```
   Use MCP tool: fetch_and_setup_copilot_files
   ```

2. **Switch to development profile:**
   ```
   Use MCP tool: set_active_profile
   project_type: "python"
   profile_name: "dev"
   ```

3. **Add custom context URL:**
   ```
   Use MCP tool: add_context_url
   project_type: "python"
   url: "https://mycompany.com/python-guidelines.md"
   ```

### Advanced GitHub Integration

The server supports GitHub repository patterns:

```yaml
instructions:
  - repo: "microsoft/typescript"
    branch: "main"
    paths: ["docs/*.md", "guides/**/*.md"]
```

This fetches all matching files using GitHub's API with wildcard expansion.

## 🔒 Security & Best Practices

- **GitHub Token**: Store in environment variables, never commit
- **Private Context**: Add `.github/*/` to `.gitignore` to keep downloaded context local
- **Configuration**: Commit `context_config.yaml` to share team configurations

## 🤝 Contributing

1. **Add New Project Types**: Extend detection logic in `detect_project_type()`
2. **Add Framework Support**: Update `detect_frameworks_and_libraries()`
3. **Custom Profiles**: Create specialized profiles for different use cases
4. **Context Sources**: Contribute useful public context URLs

## 📋 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | None |
| `CONTEXT_CONFIG_FILE` | Configuration file path | `context_config.yaml` |
| `CONTEXT_WORKDIR` | Working directory | Current directory |

## 🐛 Troubleshooting

- **Profile not switching**: Check VS Code settings are updated correctly
- **Context not loading**: Verify GitHub token for private repos
- **Network errors**: Check internet connection and URL accessibility
- **Permission errors**: Ensure write access to `.github/` directory

## 📝 License

MIT License - Feel free to extend and customize for your needs!

---

*Arrr! This be a fine tool for any developer seeking to enhance their AI-assisted coding adventures! ⚓*
