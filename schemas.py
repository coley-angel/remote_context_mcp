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
class FrontmatterConfig:
    """Default frontmatter configuration for rules"""
    trigger: str = "always_on"  # always_on, manual, on_demand
    glob: Optional[str] = None  # File pattern (e.g., *.py, *.{js,ts})
    description: Optional[str] = None
    priority: Optional[str] = None  # critical, high, medium, low
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    version: Optional[str] = None


@dataclass
class IDEPaths:
    """IDE-specific relative paths (all relative to workspace root)"""
    rules: str = ".ide/rules"
    workflows: str = ".ide/workflows"
    prompts: str = ".ide/prompts"
    instructions: str = ".ide/instructions"
    mcp_config: Optional[str] = None  # Some IDEs don't support local MCP configs


@dataclass
class IDEProfile:
    """IDE-specific configuration within a profile"""
    name: str  # "windsurf", "vscode", "cursor"
    display_name: str  # "Windsurf", "VS Code", "Cursor"
    paths: IDEPaths = field(default_factory=IDEPaths)
    frontmatter_defaults: FrontmatterConfig = field(default_factory=FrontmatterConfig)
    enabled: bool = True
    

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
    """Configuration for an MCP server - supports multiple formats"""
    name: str
    command: Optional[str] = None  # Optional for HTTP-based servers
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    cwd: Optional[str] = None
    enabled: bool = True
    auto_restart: bool = True
    description: Optional[str] = None
    
    # IDE-native fields (Windsurf/VSCode/Cursor format)
    type: Optional[str] = None  # "http", "sse", etc.
    url: Optional[str] = None  # For HTTP/SSE servers
    headers: Optional[Dict[str, str]] = None  # For auth headers
    inputs: Optional[List[Dict[str, Any]]] = None  # For user prompts
    disabled: Optional[bool] = None  # IDE uses 'disabled' instead of 'enabled'
    autoApprove: Optional[List[str]] = None  # Tools to auto-approve


@dataclass
class IDEPathConfig:
    """Platform-specific paths for an IDE"""
    settings_path: str
    mcp_config_path: Optional[str] = None
    rules_path: Optional[str] = None
    
    def resolve_for_platform(self, platform: str) -> 'IDEPathConfig':
        """
        Resolve path templates for specific platform
        
        Args:
            platform: Platform name (darwin, win32, linux)
        
        Returns:
            IDEPathConfig with resolved paths
        """
        # Path templates can use {platform} placeholder
        settings = self.settings_path.format(platform=platform)
        mcp = self.mcp_config_path.format(platform=platform) if self.mcp_config_path else None
        rules = self.rules_path.format(platform=platform) if self.rules_path else None
        
        return IDEPathConfig(
            settings_path=settings,
            mcp_config_path=mcp,
            rules_path=rules
        )


@dataclass
class IDEConfig:
    """IDE-specific configuration"""
    name: str  # IDE identifier (e.g., "vscode", "cursor", "windsurf")
    display_name: str  # Display name (e.g., "VS Code")
    instructions_key: str  # Key in settings for instructions
    supports_mcp: bool = True
    
    # Platform-specific paths
    darwin_paths: Optional[IDEPathConfig] = None  # macOS
    win32_paths: Optional[IDEPathConfig] = None  # Windows
    linux_paths: Optional[IDEPathConfig] = None  # Linux
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_paths_for_platform(self, platform: str) -> Optional[IDEPathConfig]:
        """
        Get path configuration for specific platform
        
        Args:
            platform: Platform name (darwin, win32, linux)
        
        Returns:
            IDEPathConfig for the platform or None
        """
        platform_map = {
            'darwin': self.darwin_paths,
            'win32': self.win32_paths,
            'linux': self.linux_paths
        }
        
        paths = platform_map.get(platform)
        if paths:
            return paths.resolve_for_platform(platform)
        
        return None


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
    
    # IDE-specific configurations (key: ide name like "windsurf", "vscode", "cursor")
    ide_configs: Dict[str, IDEProfile] = field(default_factory=dict)
    
    # Legacy support - will be removed
    ide_overrides: Dict[IDEType, Dict[str, Any]] = field(default_factory=dict)
    frontmatter_defaults: FrontmatterConfig = field(default_factory=FrontmatterConfig)
    
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
    
    # IDE definitions (can override defaults)
    ide_configs: Dict[str, IDEConfig] = field(default_factory=dict)
    
    # Global settings
    global_security: SecurityConfig = field(default_factory=SecurityConfig)
    supported_ides: List[str] = field(default_factory=lambda: [
        "vscode", "cursor", "windsurf"
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


# Default IDE Profile Templates
def get_default_ide_profiles() -> Dict[str, IDEProfile]:
    """
    Get default IDE profile configurations with sensible defaults
    
    Returns:
        Dictionary of IDE profiles keyed by IDE name
    """
    return {
        "windsurf": IDEProfile(
            name="windsurf",
            display_name="Windsurf",
            paths=IDEPaths(
                rules=".windsurf/",
                workflows=".windsurf/",
                prompts=".windsurf/",
                instructions=".windsurf/",
                mcp_config=None  # Windsurf uses global MCP config only
            ),
            frontmatter_defaults=FrontmatterConfig(
                trigger="always_on",
                priority="high",
                tags=["windsurf", "team"],
                author="Team"
            ),
            enabled=True
        ),
        "cursor": IDEProfile(
            name="cursor",
            display_name="Cursor",
            paths=IDEPaths(
                rules=".cursor/rules",
                workflows=".cursor/workflows",
                prompts=".cursor/prompts",
                instructions=".cursor/instructions",
                mcp_config=".cursor/mcp.json"
            ),
            frontmatter_defaults=FrontmatterConfig(
                trigger="always_on",
                priority="high",
                tags=["cursor", "team"],
                author="Team"
            ),
            enabled=True
        ),
        "vscode": IDEProfile(
            name="vscode",
            display_name="VS Code",
            paths=IDEPaths(
                rules=".vscode/rules",
                workflows=".vscode/workflows",
                prompts=".vscode/prompts",
                instructions=".vscode/instructions",
                mcp_config=".vscode/mcp.json"
            ),
            frontmatter_defaults=FrontmatterConfig(
                trigger="always_on",
                priority="high",
                tags=["vscode", "team"],
                author="Team"
            ),
            enabled=True
        )
    }


# Default IDE Configuration Templates (LEGACY - will be removed)
def get_default_ide_configs() -> Dict[str, IDEConfig]:
    """
    Get default IDE configurations for common IDEs
    
    Returns:
        Dictionary of IDE configurations keyed by IDE name
    """
    return {
        "vscode": IDEConfig(
            name="vscode",
            display_name="VS Code",
            instructions_key="chat.instructionsFilesLocations",
            supports_mcp=True,
            darwin_paths=IDEPathConfig(
                settings_path="~/Library/Application Support/Code/User/settings.json",
                mcp_config_path=".vscode/mcp.json",
                rules_path=".vscode/rules"
            ),
            win32_paths=IDEPathConfig(
                settings_path="~/AppData/Roaming/Code/User/settings.json",
                mcp_config_path=".vscode/mcp.json",
                rules_path=".vscode/rules"
            ),
            linux_paths=IDEPathConfig(
                settings_path="~/.config/Code/User/settings.json",
                mcp_config_path=".vscode/mcp.json",
                rules_path=".vscode/rules"
            )
        ),
        "cursor": IDEConfig(
            name="cursor",
            display_name="Cursor",
            instructions_key="cursor.instructionsFilesLocations",
            supports_mcp=True,
            darwin_paths=IDEPathConfig(
                settings_path="~/Library/Application Support/Cursor/User/settings.json",
                mcp_config_path=".cursor/mcp.json",
                rules_path=".cursor/rules"
            ),
            win32_paths=IDEPathConfig(
                settings_path="~/AppData/Roaming/Cursor/User/settings.json",
                mcp_config_path=".cursor/mcp.json",
                rules_path=".cursor/rules"
            ),
            linux_paths=IDEPathConfig(
                settings_path="~/.config/Cursor/User/settings.json",
                mcp_config_path=".cursor/mcp.json",
                rules_path=".cursor/rules"
            )
        ),
        "windsurf": IDEConfig(
            name="windsurf",
            display_name="Windsurf",
            instructions_key="windsurf.instructionsFilesLocations",
            supports_mcp=True,
            darwin_paths=IDEPathConfig(
                settings_path="~/.windsurf/settings.json",
                mcp_config_path="~/.codeium/windsurf/mcp_config.json",
                rules_path=".windsurf/"
            ),
            win32_paths=IDEPathConfig(
                settings_path="~/AppData/Roaming/Windsurf/User/settings.json",
                mcp_config_path="~/.codeium/windsurf/mcp_config.json",
                rules_path=".windsurf/"
            ),
            linux_paths=IDEPathConfig(
                settings_path="~/.config/windsurf/settings.json",
                mcp_config_path="~/.codeium/windsurf/mcp_config.json",
                rules_path=".windsurf/"
            )
        )
    }
