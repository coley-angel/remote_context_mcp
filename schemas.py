"""
Configuration Schemas and Data Models

Defines the structure for:
- Rules: Team coding standards and guidelines
- Workflows: Development process definitions
- MCP Servers: Dynamic MCP server configurations
- IDE Settings: Cross-IDE configuration management
"""
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum


class IDEType(str, Enum):
    """Supported IDE types"""
    VSCODE = "vscode"
    CURSOR = "cursor"
    WINDSURF = "windsurf"


class ContentType(str, Enum):
    """Types of content that can be managed"""
    INSTRUCTION = "instruction"
    RULE = "rule"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    MCP_CONFIG = "mcp_config"


class SecurityLevel(str, Enum):
    """Security validation levels"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class RemoteSource:
    """Configuration for a remote content source"""
    url: Optional[str] = None
    repo: Optional[str] = None  # Format: "owner/repo"
    branch: str = "main"
    paths: List[str] = field(default_factory=lambda: ["*.md"])
    token_env_var: Optional[str] = None  # Environment variable containing auth token
    auto_pull: bool = True  # Automatically pull updates
    pull_interval_minutes: int = 30  # How often to check for updates


@dataclass
class SecurityConfig:
    """Security validation configuration"""
    enabled: bool = True
    level: SecurityLevel = SecurityLevel.BASIC
    forbidden_patterns: List[str] = field(default_factory=list)
    required_patterns: List[str] = field(default_factory=list)
    max_file_size_kb: int = 1024  # Maximum file size in KB
    allowed_domains: List[str] = field(default_factory=list)
    scan_for_secrets: bool = True
    scan_for_pii: bool = True
    

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    cwd: Optional[str] = None
    enabled: bool = True
    auto_restart: bool = True
    description: Optional[str] = None


@dataclass
class IDEConfig:
    """IDE-specific configuration"""
    ide_type: IDEType
    settings_path: str
    instructions_key: str  # Key in settings for instructions
    mcp_config_path: Optional[str] = None  # Path to MCP config file
    rules_path: Optional[str] = None  # Path to rules directory
    supports_mcp: bool = True
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Rule:
    """A coding rule or guideline"""
    id: str
    name: str
    description: str
    content: str
    category: str  # e.g., "security", "style", "architecture"
    severity: Literal["error", "warning", "info"] = "warning"
    enabled: bool = True
    applies_to: List[str] = field(default_factory=list)  # File patterns


@dataclass
class Workflow:
    """A development workflow definition"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    triggers: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class Profile:
    """A configuration profile for a team or environment"""
    name: str
    active: bool = False
    description: Optional[str] = None
    
    # Content sources
    instructions: List[RemoteSource] = field(default_factory=list)
    rules: List[RemoteSource] = field(default_factory=list)
    workflows: List[RemoteSource] = field(default_factory=list)
    prompts: List[RemoteSource] = field(default_factory=list)
    
    # MCP server configurations
    mcp_servers: List[MCPServerConfig] = field(default_factory=list)
    
    # IDE settings
    ide_overrides: Dict[IDEType, Dict[str, Any]] = field(default_factory=dict)
    
    # Security settings
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Central repository configuration
    central_repo: Optional[RemoteSource] = None
    
    # Tags for organization
    tags: List[str] = field(default_factory=list)


@dataclass
class TeamConfig:
    """Root configuration for team settings"""
    version: str = "1.0.0"
    team_name: str = "default"
    profiles: Dict[str, Profile] = field(default_factory=dict)
    
    # Global settings
    global_security: SecurityConfig = field(default_factory=SecurityConfig)
    supported_ides: List[IDEType] = field(default_factory=lambda: [
        IDEType.VSCODE, IDEType.CURSOR, IDEType.WINDSURF
    ])
    
    # Central repository for team configs
    central_repo_url: Optional[str] = None
    central_repo_branch: str = "main"
    
    # Update settings
    auto_update: bool = True
    update_check_interval_minutes: int = 30
    
    # Metadata
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None


# IDE Configuration Mappings
IDE_CONFIGS = {
    IDEType.VSCODE: IDEConfig(
        ide_type=IDEType.VSCODE,
        settings_path="~/Library/Application Support/Code/User/settings.json",
        instructions_key="chat.instructionsFilesLocations",
        mcp_config_path=".vscode/mcp.json",
        rules_path=".vscode/rules",
    ),
    IDEType.CURSOR: IDEConfig(
        ide_type=IDEType.CURSOR,
        settings_path="~/Library/Application Support/Cursor/User/settings.json",
        instructions_key="cursor.instructionsFilesLocations",
        mcp_config_path=".cursor/mcp.json",
        rules_path=".cursor/rules",
    ),
    IDEType.WINDSURF: IDEConfig(
        ide_type=IDEType.WINDSURF,
        settings_path="~/.windsurf/settings.json",
        instructions_key="windsurf.instructionsFilesLocations",
        mcp_config_path="~/.codeium/windsurf/mcp_config.json",
        rules_path=".windsurf/rules",  # New location, replaces .windsurfrules
    ),
}


def get_ide_config(ide_type: IDEType, platform: str = "darwin") -> IDEConfig:
    """
    Get IDE configuration adjusted for the current platform
    
    Args:
        ide_type: The IDE type
        platform: Platform name (darwin, win32, linux)
    
    Returns:
        IDEConfig with platform-specific paths
    """
    config = IDE_CONFIGS.get(ide_type)
    if not config:
        raise ValueError(f"Unknown IDE type: {ide_type}")
    
    # Adjust paths for platform
    if platform == "win32":
        if ide_type == IDEType.VSCODE:
            config.settings_path = "~/AppData/Roaming/Code/User/settings.json"
        elif ide_type == IDEType.CURSOR:
            config.settings_path = "~/AppData/Roaming/Cursor/User/settings.json"
        elif ide_type == IDEType.WINDSURF:
            config.settings_path = "~/AppData/Roaming/Windsurf/User/settings.json"
    elif platform == "linux":
        if ide_type == IDEType.VSCODE:
            config.settings_path = "~/.config/Code/User/settings.json"
        elif ide_type == IDEType.CURSOR:
            config.settings_path = "~/.config/Cursor/User/settings.json"
        elif ide_type == IDEType.WINDSURF:
            config.settings_path = "~/.config/windsurf/settings.json"
    
    return config
