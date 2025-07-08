# Instructions MCP Server 📚

A Model Context Protocol (MCP) server that fetches and manages remote instruction files for GitHub Copilot from centralized team locations. This server focuses solely on instruction management using a profile-based system for team collaboration.

## 🌟 Features

- **📁 Profile-Based Management**: Multiple instruction profiles for different teams/contexts (e.g., "default", "dev", "corporate")
- **🏢 Centralized Storage**: Instructions stored in `~/vscode-instructions` by default for team sharing
- **⚙️ User Settings Integration**: Automatically updates VS Code user settings instead of workspace settings
- **🌐 GitHub Integration**: Built-in support for fetching files from GitHub repositories with wildcard patterns
- **🔄 Easy Sync**: Simple commands to fetch and sync instruction files from remote locations

## 🌟 Features

- ** Profile-Based Management**: Multiple instruction profiles for different teams/contexts (e.g., "default", "dev", "corporate")
- **� Centralized Storage**: Instructions stored in `~/vscode-instructions` by default for team sharing
- **⚙️ User Settings Integration**: Automatically updates VS Code user settings instead of workspace settings
- **🌐 GitHub Integration**: Built-in support for fetching files from GitHub repositories with wildcard patterns
- **� Easy Sync**: Simple commands to fetch and sync instruction files from remote locations

## �️ AI Security for Organizations

This MCP server provides powerful capabilities for organizations to enhance their AI security posture while enabling safe, controlled AI-assisted development. Here's how it helps address key organizational concerns:

### 🔐 Centralized Context Control

**Challenge**: Developers using AI assistants may inadvertently expose sensitive information or follow inconsistent practices across the organization.

**Solution**: The profile-based system allows organizations to:
- **Standardize AI Interactions**: Define organization-wide context profiles that ensure consistent, secure AI behavior across all projects
- **Role-Based Context**: Create different profiles for different teams (dev, security, production) with appropriate context boundaries
- **Version Control**: Context configurations are stored in `context_config.yaml`, enabling audit trails and approval workflows

```yaml
project_types:
  python:
    corporate:
      active: true
      always_fetch:
        instructions:
          - "https://internal.company.com/secure-coding-guidelines.md"
          - "https://internal.company.com/data-classification-rules.md"
        prompts:
          - "https://internal.company.com/approved-prompts.md"
```

### 🚫 Sensitive Data Protection

**Challenge**: Preventing AI assistants from accessing or recommending patterns that could expose secrets, credentials, or proprietary information.

**Solution**: 
- **Curated Instructions**: Organizations can provide AI-specific guidelines that explicitly define what should never be suggested or exposed
- **Prompt Isolation**: Sensitive prompts are stored in `.github/*/prompts/` and excluded from version control via `.gitignore`
- **Context Boundaries**: Each profile defines strict boundaries for what context the AI can access

### 🏢 Compliance & Governance

**Challenge**: Meeting regulatory requirements (SOC2, GDPR, HIPAA) while enabling AI-assisted development.

**Solution**:
- **Audit Trails**: All context fetching and profile changes are logged
- **Approval Workflows**: Configuration changes can go through standard git review processes
- **Environment Separation**: Different profiles for development, staging, and production environments
- **Documentation**: Automatic generation of AI context documentation for compliance reviews

```yaml
project_types:
  healthcare:
    hipaa-compliant:
      active: true
      always_fetch:
        instructions:
          - "https://compliance.company.com/hipaa-ai-guidelines.md"
          - "https://compliance.company.com/data-handling-rules.md"
      conditional:
        has_patient_data:
          instructions:
            - "https://compliance.company.com/phi-protection-rules.md"
```

### 🎯 Secure Development Practices

**Challenge**: Ensuring AI assistants promote secure coding practices rather than introducing vulnerabilities.

**Solution**:
- **Security-First Context**: Organizations can provide security-focused instructions that guide AI toward secure patterns
- **Framework-Specific Rules**: Automatically load security guidelines based on detected frameworks (Django security for Python, React security for JavaScript)
- **Vulnerability Prevention**: Context that explicitly warns against common security antipatterns

### 🔄 Supply Chain Security

**Challenge**: Managing the security of external context sources and preventing malicious context injection.

**Solution**:
- **Controlled Sources**: Organizations control exactly which URLs and repositories provide context
- **Internal Context Hosting**: Support for private GitHub repositories and internal documentation systems
- **Content Validation**: Downloaded context can be reviewed before activation
- **Fallback Mechanisms**: Graceful degradation when external sources are unavailable

### 📊 Usage Analytics & Monitoring

**Challenge**: Understanding how AI tools are being used across the organization and identifying potential security risks.

**Solution**:
- **Profile Usage Tracking**: Monitor which profiles are active across different teams and projects
- **Context Source Monitoring**: Track which external sources are being accessed
- **Configuration Drift Detection**: Identify when local configurations diverge from organizational standards

### 🌐 Multi-Environment Management

**Challenge**: Maintaining different security postures across development, staging, and production environments.

**Solution**:
```yaml
project_types:
  python:
    development:
      active: false
      always_fetch:
        instructions:
          - "https://internal.company.com/dev-guidelines.md"
    
    staging:
      active: false
      always_fetch:
        instructions:
          - "https://internal.company.com/staging-security-rules.md"
    
    production:
      active: true
      always_fetch:
        instructions:
          - "https://internal.company.com/production-security-strict.md"
          - "https://internal.company.com/incident-response-guidelines.md"
```

### 🔧 Implementation Recommendations

**For Security Teams:**
1. **Start Small**: Begin with read-only monitoring to understand current AI usage patterns
2. **Gradual Rollout**: Implement profiles incrementally, starting with the most security-critical projects
3. **Regular Audits**: Schedule periodic reviews of context configurations and usage patterns
4. **Incident Response**: Develop procedures for quickly updating context in response to security incidents

**For Development Teams:**
1. **Embrace Profiles**: Use organization-provided profiles as the foundation, customize as needed
2. **Contribute Context**: Share useful, non-sensitive context sources with the organization
3. **Security Awareness**: Understand how your context choices affect the AI's security recommendations

**For Compliance Officers:**
1. **Documentation**: Maintain clear documentation of approved AI usage patterns
2. **Regular Reviews**: Include AI context configurations in compliance audits
3. **Policy Integration**: Align AI context policies with existing data governance frameworks

### 🎯 ROI for Organizations

- **Reduced Security Incidents**: Proactive guidance prevents AI-suggested vulnerabilities
- **Faster Onboarding**: New developers get consistent, secure AI guidance from day one
- **Compliance Efficiency**: Automated enforcement of security policies through AI context
- **Knowledge Scaling**: Distribute security expertise organization-wide through curated context

This system transforms AI assistants from potential security risks into powerful allies for maintaining secure, compliant development practices at scale.

## �🚀 Installation

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

1. **`fetch_and_sync_instructions`** - Main tool to fetch instruction files
   - Fetches instructions for a specific profile (or active profile)
   - Downloads files to centralized directory (`~/vscode-instructions/{profile}/`)
   - Updates VS Code user settings automatically

2. **`get_available_profiles`** - List all available profiles
   - Shows profile configurations and directories
   - Indicates which profile is currently active

3. **`set_active_profile`** - Switch active profile
   ```json
   {
     "profile_name": "corporate"
   }
   ```

4. **`list_context_config`** - View current configuration
   - Shows all profiles and their instruction URLs

## ⚙️ Configuration System

### Profile Structure

The configuration uses a simple profile-based system:

```yaml
profiles:
  default:
    active: true
    instructions:
      - "https://company.com/copilot/general-guidelines.md"
      - repo: "your-org/copilot-instructions"
        branch: "main"
        paths: ["general/*.md"]
  
  corporate:
    active: false
    instructions:
      - "https://company.com/copilot/corporate-guidelines.md"
      - "https://company.com/copilot/security-guidelines.md"
  
  dev:
    active: false
    instructions:
      - repo: "your-org/dev-instructions"
        branch: "main"
        paths: ["dev/*.md", "best-practices/*.md"]
```

### Directory Structure

Instructions are stored centrally in your home directory:

```
~/vscode-instructions/
├── default/              # Default profile
│   ├── guidelines.instructions.md
│   └── security.instructions.md
├── corporate/            # Corporate profile
│   └── corporate-guidelines.instructions.md
└── dev/                  # Development profile
    ├── dev-guidelines.instructions.md
    └── best-practices.instructions.md
```

## 🎯 Workflow Examples

### Basic Usage

1. **Sync instructions for active profile:**
   ```
   Use MCP tool: fetch_and_sync_instructions
   ```

2. **Switch to corporate profile:**
   ```
   Use MCP tool: set_active_profile
   profile_name: "corporate"
   ```

3. **List available profiles:**
   ```
   Use MCP tool: get_available_profiles
   ```

4. **View configuration:**
   ```
   Use MCP tool: list_context_config
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
| `INSTRUCTIONS_DIR` | Base directory for instructions | `~/vscode-instructions` |

## 🐛 Troubleshooting

- **Profile not switching**: Check that VS Code user settings are being updated correctly
- **Instructions not loading**: Verify GitHub token for private repos and URL accessibility
- **Network errors**: Check internet connection and URL accessibility
- **Permission errors**: Ensure write access to instructions directory (`~/vscode-instructions`)

## 📝 License

MIT License - Feel free to extend and customize for your team's needs!

---

*This tool helps teams maintain centralized, consistent AI instruction sets for better collaboration! 🚀*
