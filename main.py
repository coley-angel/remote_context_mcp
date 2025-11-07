#!/usr/bin/env uv run python
"""
Team Configuration MCP Server

Enhanced MCP server for managing team configurations across multiple IDEs:
- Windsurf, Cursor, VS Code support
- Rules, workflows, instructions, and prompts management
- Security validation for team content
- Git-based central repository syncing
- Dynamic MCP server configuration and reloading
"""
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import yaml
import httpx
import aiofiles
import fnmatch
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Import new modules
from schemas import IDEType, ContentType, TeamConfig, Profile
from config_loader import ConfigLoader
from security_validator import SecurityValidator, create_default_security_config
from repo_manager import create_repo_manager
from ide_manager import create_ide_manager

# Set up logging (use stderr to avoid interfering with MCP stdio protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("TeamConfigMCP")

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CONFIG_FILE = os.getenv("TEAM_CONFIG_FILE", "team_config.yaml")
WORKSPACE_DIR = Path(os.getenv("WORKSPACE_DIR", os.getcwd()))

# Make CONFIG_FILE absolute if it's a relative path
if not CONFIG_FILE.startswith(('http://', 'https://', '/')):
    CONFIG_FILE = str(Path(__file__).parent / CONFIG_FILE)

# Base directories
BASE_DIR = Path(os.getenv("MCP_BASE_DIR", "~/.mcp-team-config")).expanduser()
CACHE_DIR = BASE_DIR / "cache"
CONTENT_DIR = BASE_DIR / "content"
BACKUP_DIR = BASE_DIR / "backups"

# Create directories
for directory in [BASE_DIR, CACHE_DIR, CONTENT_DIR, BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize managers (will be created on first use)
_repo_manager = None
_ide_manager = None
_security_validator = None
_current_config: Optional[TeamConfig] = None
_current_ide: Optional[IDEType] = None  # Detected or user-specified IDE


def get_repo_manager():
    """Get or create repository manager"""
    global _repo_manager
    if _repo_manager is None:
        _repo_manager = create_repo_manager(CACHE_DIR / "repos")
    return _repo_manager


def get_ide_manager():
    """Get or create IDE manager"""
    global _ide_manager
    if _ide_manager is None:
        _ide_manager = create_ide_manager()
    return _ide_manager


def get_security_validator(config: Optional[TeamConfig] = None):
    """Get or create security validator"""
    global _security_validator
    if config and config.global_security:
        return SecurityValidator(config.global_security)
    if _security_validator is None:
        _security_validator = SecurityValidator(create_default_security_config())
    return _security_validator


def detect_current_ide() -> Optional[IDEType]:
    """
    Detect which IDE is currently running this MCP server.
    
    Returns:
        Detected IDE type or None if cannot determine
    """
    # Check environment variables that might indicate the IDE
    if os.getenv("VSCODE_PID") or os.getenv("VSCODE_CWD"):
        return IDEType.VSCODE
    
    if os.getenv("CURSOR_PID"):
        return IDEType.CURSOR
    
    # Check for Windsurf-specific indicators
    if os.getenv("WINDSURF_PID") or os.getenv("CODEIUM_PID"):
        return IDEType.WINDSURF
    
    # Fallback: check which IDE's settings directory exists
    ide_mgr = get_ide_manager()
    installed = ide_mgr.detect_installed_ides()
    
    # Return the first installed IDE as a guess
    if installed:
        return installed[0]
    
    return None


def get_current_ide() -> IDEType:
    """
    Get the current IDE (detected or user-specified).
    
    Returns:
        Current IDE type, defaults to VS Code if cannot determine
    """
    global _current_ide
    
    if _current_ide is None:
        _current_ide = detect_current_ide()
    
    # Default to VS Code if still None
    if _current_ide is None:
        _current_ide = IDEType.VSCODE
    
    return _current_ide


def set_current_ide(ide_type: IDEType):
    """
    Set the current IDE explicitly.
    
    Args:
        ide_type: IDE type to use
    """
    global _current_ide
    _current_ide = ide_type


def get_ide_content_dir(ide_type: IDEType, profile_name: str) -> Path:
    """
    Get the content directory for a specific IDE and profile.
    
    Args:
        ide_type: IDE type
        profile_name: Profile name
    
    Returns:
        Path to IDE-specific content directory
    """
    # IDE-specific base directories
    ide_dirs = {
        IDEType.VSCODE: Path.home() / "vscode-instructions",
        IDEType.CURSOR: Path.home() / "cursor-instructions",
        IDEType.WINDSURF: Path.home() / "windsurf-instructions",
    }
    
    base_dir = ide_dirs.get(ide_type, Path.home() / f"{ide_type.value}-instructions")
    return base_dir / profile_name


def load_team_config() -> TeamConfig:
    """Load team configuration from file or URL"""
    global _current_config
    
    config_source = CONFIG_FILE
    
    try:
        if config_source.startswith(('http://', 'https://')):
            # Remote config file
            headers = {}
            if GITHUB_TOKEN and "github.com" in config_source:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(config_source, headers=headers, timeout=5.0)
                response.raise_for_status()
                content = response.text
                config = ConfigLoader.load_from_string(content)
        else:
            # Local config file
            config_path = Path(config_source)
            if config_path.exists():
                config = ConfigLoader.load_from_file(config_path)
            else:
                # Create default config
                config = create_default_config()
                ConfigLoader.save_to_file(config, config_path)
                logger.info(f"Created default configuration at {config_path}")
        
        if config:
            _current_config = config
            return config
        else:
            return create_default_config()
            
    except Exception as e:
        logger.error(f"Failed to load config from {config_source}: {e}")
        return create_default_config()


def create_default_config() -> TeamConfig:
    """Create a default team configuration"""
    from schemas import Profile, SecurityConfig, SecurityLevel
    
    default_profile = Profile(
        name="default",
        active=True,
        description="Default profile",
        instructions=[],
        rules=[],
        workflows=[],
        prompts=[],
        mcp_servers=[],
        security=SecurityConfig(
            enabled=True,
            level=SecurityLevel.BASIC,
        ),
    )
    
    return TeamConfig(
        version="1.0.0",
        team_name="default",
        profiles={"default": default_profile},
        global_security=SecurityConfig(enabled=True, level=SecurityLevel.BASIC),
        supported_ides=[IDEType.VSCODE, IDEType.CURSOR, IDEType.WINDSURF],
    )


async def fetch_content_from_source(
    source,
    content_type: ContentType,
    profile_name: str
) -> List[Dict[str, Any]]:
    """
    Fetch content from a remote source
    
    Args:
        source: RemoteSource object
        content_type: Type of content being fetched
        profile_name: Profile name for organization
    
    Returns:
        List of fetched content with metadata
    """
    fetched_items = []
    repo_manager = get_repo_manager()
    
    try:
        if source.repo:
            # Git repository source
            token = os.getenv(source.token_env_var) if source.token_env_var else GITHUB_TOKEN
            repo_url = f"https://github.com/{source.repo}"
            
            repo = repo_manager.clone_or_update_repo(
                repo_url,
                source.branch,
                token
            )
            
            if repo:
                files = repo_manager.get_files_from_repo(repo, source.paths)
                
                for file_path in files:
                    content = file_path.read_text(encoding='utf-8')
                    
                    # Validate content security
                    validator = get_security_validator(_current_config)
                    is_valid, violations = validator.validate_content(
                        content,
                        str(file_path),
                        content_type.value
                    )
                    
                    fetched_items.append({
                        "source": str(file_path),
                        "content": content,
                        "size": len(content),
                        "security_valid": is_valid,
                        "security_violations": len(violations),
                        "repo": source.repo,
                        "branch": source.branch,
                    })
        
        elif source.url:
            # Direct URL source
            headers = {}
            if GITHUB_TOKEN and "github.com" in source.url:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            
            async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
                response = await client.get(source.url, headers=headers, timeout=30.0)
                response.raise_for_status()
                content = response.text
                
                # Validate content security
                validator = get_security_validator(_current_config)
                is_valid, violations = validator.validate_content(
                    content,
                    source.url,
                    content_type.value
                )
                
                fetched_items.append({
                    "source": source.url,
                    "content": content,
                    "size": len(content),
                    "security_valid": is_valid,
                    "security_violations": len(violations),
                })
    
    except Exception as e:
        logger.error(f"Failed to fetch content from source: {e}")
    
    return fetched_items


# ============================================================================
# MCP TOOLS - New comprehensive tools for team configuration management
# ============================================================================

@mcp.tool()
async def sync_team_config(
    profile_name: Optional[str] = None,
    force_update: bool = False,
    sync_to_ides: bool = True
) -> str:
    """
    Sync team configuration from central repository and update all IDEs.
    
    This is the main tool to fetch and apply team configurations including:
    - Instructions (AI guidance files)
    - Rules (coding standards)
    - Workflows (development processes)
    - Prompts (reusable AI prompts)
    - MCP server configurations
    
    Files are saved to IDE-specific directories:
    - VS Code: ~/vscode-instructions/{profile}/
    - Cursor: ~/cursor-instructions/{profile}/
    - Windsurf: ~/windsurf-instructions/{profile}/
    
    Args:
        profile_name: Profile to sync (uses active profile if None)
        force_update: Force pull from remote even if recently updated
        sync_to_ides: Sync to all detected IDEs (Windsurf, Cursor, VS Code)
    
    Returns:
        JSON response with sync results and any security issues
    """
    from mcp_tools import sync_profile_tool
    
    config = load_team_config()
    ide_manager = get_ide_manager()
    current_ide = get_current_ide()
    
    return await sync_profile_tool(
        profile_name,
        config,
        CONTENT_DIR,
        ide_manager,
        fetch_content_from_source,
        WORKSPACE_DIR if sync_to_ides else None,
        current_ide,
        get_ide_content_dir
    )


@mcp.tool()
async def cleanup_profile_rules(profile_name: Optional[str] = None) -> str:
    """
    Clean up rule files from IDEs for a specific profile.
    
    This removes all managed rule files that were synced by the profile.
    Useful when deactivating a profile without switching to another one.
    
    Args:
        profile_name: Profile name to cleanup (uses active profile if None)
    
    Returns:
        JSON response with cleanup results
    """
    try:
        config = load_team_config()
        ide_manager = get_ide_manager()
        
        # Find profile
        if profile_name is None:
            active_profiles = [p for p in config.profiles.values() if p.active]
            if not active_profiles:
                return json.dumps({
                    "success": False,
                    "error": "No active profile found"
                })
            profile_name = active_profiles[0].name
        else:
            if profile_name not in config.profiles:
                return json.dumps({
                    "success": False,
                    "error": f"Profile '{profile_name}' not found",
                    "available_profiles": list(config.profiles.keys())
                })
        
        # Cleanup rules from all IDEs
        cleanup_results = ide_manager.cleanup_all_ides(
            profile_name,
            WORKSPACE_DIR
        )
        
        return json.dumps({
            "success": True,
            "profile": profile_name,
            "cleanup_results": {ide.value: success for ide, success in cleanup_results.items()},
            "message": f"Cleaned up rules for profile '{profile_name}'"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error cleaning up profile rules: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def list_profiles() -> str:
    """
    List all available configuration profiles.
    
    Shows:
    - Profile names
    - Active status
    - Content sources (instructions, rules, workflows, prompts)
    - Security settings
    - MCP servers configured
    
    Returns:
        JSON response with all profiles and their configurations
    """
    try:
        config = load_team_config()
        
        profiles_info = {}
        for name, profile in config.profiles.items():
            profiles_info[name] = {
                "active": profile.active,
                "description": profile.description,
                "content_sources": {
                    "instructions": len(profile.instructions),
                    "rules": len(profile.rules),
                    "workflows": len(profile.workflows),
                    "prompts": len(profile.prompts)
                },
                "mcp_servers": [
                    {"name": s.name, "enabled": s.enabled, "description": s.description}
                    for s in profile.mcp_servers
                ],
                "security_level": profile.security.level.value,
                "tags": profile.tags
            }
        
        return json.dumps({
            "success": True,
            "team_name": config.team_name,
            "profiles": profiles_info,
            "content_directory": str(CONTENT_DIR)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def set_active_profile(profile_name: str, auto_sync: bool = True) -> str:
    """
    Set the active configuration profile.
    
    Args:
        profile_name: Name of profile to activate
        auto_sync: Automatically sync the profile after activation
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        config = load_team_config()
        ide_manager = get_ide_manager()
        
        if profile_name not in config.profiles:
            return json.dumps({
                "success": False,
                "error": f"Profile '{profile_name}' not found",
                "available_profiles": list(config.profiles.keys())
            })
        
        # Find currently active profile to cleanup
        previously_active = None
        for name, profile in config.profiles.items():
            if profile.active:
                previously_active = name
                break
        
        # Cleanup previously active profile rules
        cleanup_results = {}
        if previously_active and previously_active != profile_name:
            logger.info(f"Cleaning up rules from previous profile: {previously_active}")
            cleanup_results = ide_manager.cleanup_all_ides(
                previously_active,
                WORKSPACE_DIR
            )
        
        # Deactivate all profiles
        for profile in config.profiles.values():
            profile.active = False
        
        # Activate requested profile
        config.profiles[profile_name].active = True
        
        # Save config
        config_path = Path(CONFIG_FILE)
        if not CONFIG_FILE.startswith(('http://', 'https://')):
            ConfigLoader.save_to_file(config, config_path)
        
        response = {
            "success": True,
            "message": f"Profile '{profile_name}' activated",
            "profile": profile_name,
            "previous_profile": previously_active,
            "cleanup_results": {ide.value: success for ide, success in cleanup_results.items()} if cleanup_results else {}
        }
        
        # Auto-sync if requested
        if auto_sync:
            sync_result = await sync_team_config(profile_name)
            response["sync_result"] = json.loads(sync_result)
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def check_for_updates() -> str:
    """
    Check if central repository has updates without pulling them.
    
    Useful for monitoring changes before applying them.
    
    Returns:
        JSON response with update status for each profile's central repo
    """
    try:
        config = load_team_config()
        repo_manager = get_repo_manager()
        
        updates = {}
        
        for name, profile in config.profiles.items():
            if profile.central_repo and profile.central_repo.repo:
                repo_url = f"https://github.com/{profile.central_repo.repo}"
                token = os.getenv(profile.central_repo.token_env_var) if profile.central_repo.token_env_var else GITHUB_TOKEN
                
                has_updates, latest_commit = repo_manager.check_for_updates(
                    repo_url,
                    profile.central_repo.branch,
                    token
                )
                
                updates[name] = {
                    "has_updates": has_updates,
                    "latest_commit": latest_commit,
                    "repo": profile.central_repo.repo,
                    "branch": profile.central_repo.branch
                }
        
        return json.dumps({
            "success": True,
            "updates": updates,
            "checked_at": datetime.now().isoformat()
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def validate_content_security(
    content: str,
    content_type: str = "general",
    filename: str = "unknown"
) -> str:
    """
    Validate content for security issues before using it.
    
    Scans for:
    - Secrets (API keys, tokens, passwords)
    - PII (emails, SSNs, phone numbers)
    - Forbidden patterns
    - Dangerous code patterns
    
    Args:
        content: Content to validate
        content_type: Type of content (instruction, rule, workflow, prompt, general)
        filename: Name of file being validated
    
    Returns:
        JSON response with validation results and violations
    """
    try:
        config = load_team_config()
        validator = get_security_validator(config)
        
        is_valid, violations = validator.validate_content(content, filename, content_type)
        
        violations_data = [
            {
                "severity": v.severity,
                "category": v.category,
                "message": v.message,
                "line_number": v.line_number,
                "suggestion": v.suggestion
            }
            for v in violations
        ]
        
        return json.dumps({
            "success": True,
            "is_valid": is_valid,
            "violations_count": len(violations),
            "violations": violations_data,
            "security_level": config.global_security.level.value
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error validating content: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def update_mcp_servers(
    profile_name: Optional[str] = None,
    reload: bool = True
) -> str:
    """
    Update MCP server configurations for active profile.
    
    Applies MCP server settings from profile to workspace configuration.
    
    Args:
        profile_name: Profile to use (uses active if None)
        reload: Reload IDE after updating (requires IDE restart)
    
    Returns:
        JSON response with update results
    """
    try:
        config = load_team_config()
        ide_manager = get_ide_manager()
        
        # Find profile
        if profile_name is None:
            active_profiles = [p for p in config.profiles.values() if p.active]
            if not active_profiles:
                return json.dumps({"success": False, "error": "No active profile"})
            profile = active_profiles[0]
        else:
            if profile_name not in config.profiles:
                return json.dumps({"success": False, "error": f"Profile '{profile_name}' not found"})
            profile = config.profiles[profile_name]
        
        # Update MCP servers for all IDEs
        results = {}
        for ide_type in config.supported_ides:
            success = ide_manager.update_mcp_servers(
                ide_type,
                profile.mcp_servers,
                WORKSPACE_DIR,
                merge=True,  # Merge with existing servers, preserve manually configured ones
                profile_name=profile.name  # Track which profile manages these servers
            )
            results[ide_type.value] = success
        
        return json.dumps({
            "success": True,
            "profile": profile.name,
            "mcp_servers_configured": len(profile.mcp_servers),
            "ide_updates": results,
            "reload_required": reload
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error updating MCP servers: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def list_installed_ides() -> str:
    """
    Detect which IDEs are installed on this system.
    
    Checks for:
    - VS Code
    - Cursor
    - Windsurf
    
    Returns:
        JSON response with installed IDEs and their settings paths
    """
    try:
        ide_manager = get_ide_manager()
        installed = ide_manager.detect_installed_ides()
        
        # Get current IDE
        current_ide = get_current_ide()
        detected_ide = detect_current_ide()
        
        ide_info = {}
        for ide_type in installed:
            settings_path = ide_manager.get_settings_path(ide_type)
            mcp_path = ide_manager.get_mcp_config_path(ide_type, WORKSPACE_DIR)
            
            ide_info[ide_type.value] = {
                "installed": True,
                "is_current": ide_type == current_ide,
                "is_detected": ide_type == detected_ide,
                "settings_path": str(settings_path),
                "mcp_config_path": str(mcp_path) if mcp_path else None,
                "settings_exists": settings_path.exists(),
                "instructions_dir": str(get_ide_content_dir(ide_type, "default"))
            }
        
        return json.dumps({
            "success": True,
            "current_ide": current_ide.value,
            "detected_ide": detected_ide.value if detected_ide else "unknown",
            "installed_ides": [ide.value for ide in installed],
            "ide_details": ide_info
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error listing IDEs: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_current_ide_info() -> str:
    """
    Get information about the currently active IDE.
    
    This tool automatically detects which IDE is running the MCP server
    or uses the IDE that was explicitly set.
    
    Returns:
        JSON response with current IDE information
    """
    try:
        current_ide = get_current_ide()
        detected_ide = detect_current_ide()
        
        ide_manager = get_ide_manager()
        settings_path = ide_manager.get_settings_path(current_ide)
        
        return json.dumps({
            "success": True,
            "current_ide": current_ide.value,
            "detected_ide": detected_ide.value if detected_ide else "unknown",
            "auto_detected": detected_ide is not None,
            "settings_path": str(settings_path),
            "instructions_dir": str(get_ide_content_dir(current_ide, "default")),
            "instructions_dirs": {
                "vscode": str(get_ide_content_dir(IDEType.VSCODE, "default")),
                "cursor": str(get_ide_content_dir(IDEType.CURSOR, "default")),
                "windsurf": str(get_ide_content_dir(IDEType.WINDSURF, "default"))
            }
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting current IDE: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def set_ide(ide_name: str) -> str:
    """
    Explicitly set which IDE you're using.
    
    Use this if auto-detection doesn't work or you want to override it.
    
    Args:
        ide_name: IDE to use ("vscode", "cursor", or "windsurf")
    
    Returns:
        JSON response with updated IDE setting
    """
    try:
        # Convert string to IDEType
        ide_name_lower = ide_name.lower()
        ide_map = {
            "vscode": IDEType.VSCODE,
            "vs code": IDEType.VSCODE,
            "cursor": IDEType.CURSOR,
            "windsurf": IDEType.WINDSURF,
            "cascade": IDEType.WINDSURF
        }
        
        if ide_name_lower not in ide_map:
            return json.dumps({
                "success": False,
                "error": f"Unknown IDE: {ide_name}",
                "available_ides": list(set(ide_map.keys()))
            })
        
        ide_type = ide_map[ide_name_lower]
        set_current_ide(ide_type)
        
        return json.dumps({
            "success": True,
            "message": f"IDE set to {ide_type.value}",
            "current_ide": ide_type.value,
            "instructions_dir": str(get_ide_content_dir(ide_type, "default"))
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting IDE: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_config() -> str:
    """
    Get the complete team configuration.
    
    Returns:
        JSON response with full configuration
    """
    try:
        config = load_team_config()
        config_dict = ConfigLoader.config_to_dict(config)
        
        return json.dumps({
            "success": True,
            "config": config_dict
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def reload_config() -> str:
    """
    Reload configuration from source (file or URL).
    
    Useful when configuration has been updated externally.
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        global _current_config
        _current_config = None  # Force reload
        
        config = load_team_config()
        
        return json.dumps({
            "success": True,
            "message": "Configuration reloaded",
            "team_name": config.team_name,
            "profiles_count": len(config.profiles),
            "active_profile": next((p.name for p in config.profiles.values() if p.active), None)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def clear_cache(cache_type: str = "all") -> str:
    """
    Clear cached data.
    
    Args:
        cache_type: Type of cache to clear (all, repos, content)
    
    Returns:
        JSON response indicating what was cleared
    """
    try:
        cleared = []
        
        if cache_type in ["all", "repos"]:
            repo_manager = get_repo_manager()
            repo_manager.clear_cache()
            cleared.append("repositories")
        
        if cache_type in ["all", "content"]:
            import shutil
            if CONTENT_DIR.exists():
                shutil.rmtree(CONTENT_DIR)
                CONTENT_DIR.mkdir(parents=True, exist_ok=True)
            cleared.append("content")
        
        return json.dumps({
            "success": True,
            "cleared": cleared,
            "message": f"Cleared cache: {', '.join(cleared)}"
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return json.dumps({"success": False, "error": str(e)})


def main():
    """Main function to run the Team Configuration MCP server"""
    logger.info("=" * 70)
    logger.info("Starting Team Configuration MCP Server")
    logger.info("=" * 70)
    logger.info(f"Config file: {CONFIG_FILE}")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Content directory: {CONTENT_DIR}")
    logger.info(f"Workspace directory: {WORKSPACE_DIR}")
    
    # Try to load configuration (don't block on failure)
    try:
        # Use a shorter timeout for startup config check
        config = load_team_config()
        logger.info(f"Team: {config.team_name}")
        logger.info(f"Profiles: {len(config.profiles)}")
        active_profile = next((p.name for p in config.profiles.values() if p.active), None)
        logger.info(f"Active profile: {active_profile or 'None'}")
    except Exception as e:
        logger.warning(f"Config load during startup failed: {e}")
        logger.info("Using default configuration - config will be loaded on first tool use")
    
    logger.info("=" * 70)
    logger.info("MCP Server Ready")
    logger.info("=" * 70)
    
    # Run the server
    mcp.run()
    
    logger.info("Team Configuration MCP server completed")


if __name__ == "__main__":
    main()
