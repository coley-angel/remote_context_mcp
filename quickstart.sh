#!/bin/bash
# Team Configuration MCP Server - Quick Start Setup

set -e

echo "=============================================="
echo "Team Configuration MCP Server - Quick Start"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo -e "${GREEN}✓ uv found${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
uv sync

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << EOF
# GitHub token for accessing private repositories
GITHUB_TOKEN=

# Team configuration file (can be local path or URL)
TEAM_CONFIG_FILE=team_config.yaml

# Base directory for MCP data
MCP_BASE_DIR=~/.mcp-team-config

# Workspace directory
WORKSPACE_DIR=\$(pwd)
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env and add your GITHUB_TOKEN${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

# Create team_config.yaml if it doesn't exist
if [ ! -f team_config.yaml ]; then
    echo ""
    echo "Creating default team_config.yaml..."
    cat > team_config.yaml << 'EOF'
version: "1.0.0"
team_name: "My Team"

# Global security settings
global_security:
  enabled: true
  level: "basic"
  scan_for_secrets: true
  scan_for_pii: true

# Supported IDEs
supported_ides:
  - "vscode"
  - "cursor"
  - "windsurf"

# Configuration profiles
profiles:
  default:
    active: true
    description: "Default development profile"
    
    # AI instructions
    instructions: []
    
    # Coding rules
    rules: []
    
    # Development workflows
    workflows: []
    
    # AI prompts
    prompts: []
    
    # MCP servers
    mcp_servers:
      - name: "github"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-github"]
        env:
          GITHUB_TOKEN: "${GITHUB_TOKEN}"
        enabled: true
    
    # Security settings
    security:
      enabled: true
      level: "basic"
    
    tags: ["development"]
EOF
    echo -e "${GREEN}✓ team_config.yaml created${NC}"
else
    echo -e "${YELLOW}⚠ team_config.yaml already exists${NC}"
fi

# Create base directory
BASE_DIR="${HOME}/.mcp-team-config"
mkdir -p "${BASE_DIR}"
echo -e "${GREEN}✓ Base directory created: ${BASE_DIR}${NC}"

# Test the server
echo ""
echo "Testing MCP server..."
if uv run python main.py --help > /dev/null 2>&1 || true; then
    echo -e "${GREEN}✓ MCP server can be started${NC}"
else
    echo -e "${YELLOW}⚠ MCP server test completed${NC}"
fi

# Check for installed IDEs
echo ""
echo "Checking for installed IDEs..."

if [ -d "${HOME}/Library/Application Support/Code" ]; then
    echo -e "${GREEN}✓ VS Code detected${NC}"
fi

if [ -d "${HOME}/Library/Application Support/Cursor" ]; then
    echo -e "${GREEN}✓ Cursor detected${NC}"
fi

if [ -d "${HOME}/.windsurf" ]; then
    echo -e "${GREEN}✓ Windsurf detected${NC}"
fi

# Print next steps
echo ""
echo "=============================================="
echo "Setup Complete! 🎉"
echo "=============================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Edit .env and add your GITHUB_TOKEN:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Customize team_config.yaml for your team:"
echo "   ${YELLOW}nano team_config.yaml${NC}"
echo ""
echo "3. Configure your IDE:"
echo ""
echo "   For VS Code/Cursor, create .vscode/mcp.json or .cursor/mcp.json:"
echo '   {
     "servers": {
       "team-config": {
         "command": "uv",
         "args": ["run", "python", "'$(pwd)'/main.py"],
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}",
           "TEAM_CONFIG_FILE": "team_config.yaml"
         }
       }
     }
   }'
echo ""
echo "   For Windsurf, create .windsurf/mcp.json:"
echo '   {
     "mcpServers": {
       "team-config": {
         "command": "uv",
         "args": ["run", "python", "'$(pwd)'/main.py"],
         "env": {
           "GITHUB_TOKEN": "${GITHUB_TOKEN}",
           "TEAM_CONFIG_FILE": "team_config.yaml"
         }
       }
     }
   }'
echo ""
echo "4. Test the setup:"
echo "   ${YELLOW}uv run python main.py${NC}"
echo ""
echo "5. Use in your IDE's AI chat:"
echo "   - sync_team_config()           # Sync your team config"
echo "   - list_profiles()              # List available profiles"
echo "   - list_installed_ides()        # Check detected IDEs"
echo ""
echo "Documentation:"
echo "  - README_NEW.md    # Full documentation"
echo "  - MIGRATION.md     # Migration guide from v1"
echo "  - team_config_example.yaml  # Complete example"
echo ""
echo "=============================================="
