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
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import yaml
import httpx
import aiofiles
import fnmatch
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

# Initialize FastMCP
mcp = FastMCP("TeamConfigMCP")

# Configuration - read from environment variables (passed via mcp_config.json)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
TEAM_CONFIG_REPO = os.getenv("TEAM_CONFIG_REPO")
TEAM_CONFIG_BRANCH = os.getenv("TEAM_CONFIG_BRANCH", "main")
CONFIG_FILE = os.getenv("TEAM_CONFIG_FILE", "team_config.yaml")
# WORKSPACE_DIR will be detected dynamically - see get_workspace_dir()
WORKSPACE_DIR = None  # Populated dynamically

# Log environment variable status (to stderr for debugging)
logger.info("=" * 80)
logger.info("Team Config MCP Server Starting")
logger.info("=" * 80)
logger.info(f"Environment variables:")
logger.info(f"  TEAM_CONFIG_REPO: {TEAM_CONFIG_REPO or 'NOT SET'}")
logger.info(f"  TEAM_CONFIG_BRANCH: {TEAM_CONFIG_BRANCH}")
logger.info(f"  TEAM_CONFIG_FILE: {CONFIG_FILE}")
logger.info(f"  GITHUB_TOKEN: {'***SET***' if GITHUB_TOKEN else 'NOT SET'}")
logger.info(f"  Working Directory: {os.getcwd()}")
logger.info(f"  Python: {sys.executable}")
logger.info(f"  Script: {__file__}")

# Debug: Log ALL environment variables for troubleshooting
logger.debug("All environment variables:")
for key in sorted(os.environ.keys()):
    if any(x in key.upper() for x in ['TOKEN', 'CONFIG', 'GITHUB', 'TEAM']):
        value = os.environ[key]
        if 'TOKEN' in key.upper():
            value = '***HIDDEN***' if value else 'NOT SET'
        logger.debug(f"  {key}: {value}")
logger.info("=" * 80)

# Determine configuration source
if TEAM_CONFIG_REPO:
    # Build URL from repository
    repo_url = TEAM_CONFIG_REPO.rstrip('/').replace('.git', '')
    
    if "github.com" in repo_url:
        # Use GitHub API for private repos (works with token auth)
        # https://github.com/org/repo -> https://api.github.com/repos/org/repo/contents/file?ref=branch
        parts = repo_url.split('github.com/')[-1]
        config_filename = CONFIG_FILE if not CONFIG_FILE.startswith('http') else 'team_config.yaml'
        CONFIG_FILE = f"https://api.github.com/repos/{parts}/contents/{config_filename}?ref={TEAM_CONFIG_BRANCH}"
        logger.info(f"Loading config from GitHub API: {CONFIG_FILE}")
    
    elif "gitlab.com" in repo_url:
        # https://gitlab.com/org/repo -> https://gitlab.com/org/repo/-/raw/branch/file
        parts = repo_url.split('gitlab.com/')[-1]
        CONFIG_FILE = f"https://gitlab.com/{parts}/-/raw/{TEAM_CONFIG_BRANCH}/{CONFIG_FILE}"
        logger.info(f"Loading config from GitLab: {CONFIG_FILE}")
    
    elif "bitbucket.org" in repo_url:
        # https://bitbucket.org/org/repo -> https://bitbucket.org/org/repo/raw/branch/file
        parts = repo_url.split('bitbucket.org/')[-1]
        CONFIG_FILE = f"https://bitbucket.org/{parts}/raw/{TEAM_CONFIG_BRANCH}/{CONFIG_FILE}"
        logger.info(f"Loading config from Bitbucket: {CONFIG_FILE}")
    
    else:
        logger.warning(f"TEAM_CONFIG_REPO set but not a recognized Git hosting platform: {TEAM_CONFIG_REPO}")
        logger.warning(f"Supported: GitHub, GitLab, Bitbucket")
        # Fallback to local file
        if not CONFIG_FILE.startswith(('http://', 'https://', '/')):
            CONFIG_FILE = str(Path(__file__).parent / CONFIG_FILE)
else:
    # Make CONFIG_FILE absolute if it's a relative path
    if not CONFIG_FILE.startswith(('http://', 'https://', '/')):
        CONFIG_FILE = str(Path(__file__).parent / CONFIG_FILE)

# Base directories - initially use default, will be updated based on config
_BASE_DIR = None
_CACHE_DIR = None
_CONTENT_DIR = None
_BACKUP_DIR = None

# Initialize managers (will be created on first use)
_repo_manager = None
_ide_manager = None
_security_validator = None
_current_config: Optional[TeamConfig] = None
_current_ide: Optional[IDEType] = None  # Detected or user-specified IDE


def get_repo_specific_dirname(repo_url: Optional[str]) -> str:
    """
    Generate a unique directory name for a repository URL.
    
    Args:
        repo_url: Repository URL (e.g., https://github.com/org/repo)
        
    Returns:
        Directory name based on repo URL or 'default' if no URL
    """
    if not repo_url:
        return "default"
    
    # Extract org/repo from common Git URL formats
    # https://github.com/org/repo -> org_repo
    # git@github.com:org/repo.git -> org_repo
    repo_url = repo_url.rstrip('/')
    
    if 'github.com' in repo_url or 'gitlab.com' in repo_url or 'bitbucket.org' in repo_url:
        # Extract the org/repo part
        parts = repo_url.split('/')[-2:]
        if len(parts) == 2:
            org, repo = parts
            repo = repo.replace('.git', '')
            return f"{org}_{repo}"
    
    # Fallback: hash the URL
    url_hash = hashlib.md5(repo_url.encode()).hexdigest()[:8]
    return f"repo_{url_hash}"


def get_base_directories(config: Optional[TeamConfig] = None) -> tuple[Path, Path, Path, Path]:
    """
    Get or create base directories for the current configuration.
    
    Args:
        config: Team configuration (uses loaded config if None)
        
    Returns:
        Tuple of (BASE_DIR, CACHE_DIR, CONTENT_DIR, BACKUP_DIR)
    """
    global _BASE_DIR, _CACHE_DIR, _CONTENT_DIR, _BACKUP_DIR
    
    if config is None:
        config = _current_config
    
    # Determine repo-specific directory name
    repo_dirname = "default"
    if config and config.central_repo_url:
        repo_dirname = get_repo_specific_dirname(config.central_repo_url)
    
    # Use environment variable base or default
    base_parent = Path(os.getenv("MCP_BASE_DIR_ROOT", "~/.mcp-team-config")).expanduser()
    
    # Create repo-specific directory
    base_dir = base_parent / repo_dirname
    cache_dir = base_dir / "cache"
    content_dir = base_dir / "content"
    backup_dir = base_dir / "backups"
    
    # Create directories
    for directory in [base_dir, cache_dir, content_dir, backup_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Update globals
    _BASE_DIR = base_dir
    _CACHE_DIR = cache_dir
    _CONTENT_DIR = content_dir
    _BACKUP_DIR = backup_dir
    
    return base_dir, cache_dir, content_dir, backup_dir


# Initialize with default directories
BASE_DIR, CACHE_DIR, CONTENT_DIR, BACKUP_DIR = get_base_directories()


def get_repo_manager():
    """Get or create repository manager"""
    global _repo_manager
    _, cache_dir, _, _ = get_base_directories()
    if _repo_manager is None:
        _repo_manager = create_repo_manager(cache_dir / "repos")
    return _repo_manager


def get_ide_manager():
    """Get or create IDE manager with IDE configs from team config"""
    global _ide_manager
    if _ide_manager is None:
        from ide_adapter import loadIdeConfigsFromTeamConfig
        config = load_team_config()
        ide_configs = loadIdeConfigsFromTeamConfig(config)
        _ide_manager = create_ide_manager(ide_configs)
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
    # Log all potentially relevant environment variables for debugging
    relevant_env_vars = [
        'VSCODE_PID', 'VSCODE_CWD', 'VSCODE_IPC_HOOK', 'VSCODE_NLS_CONFIG',
        'CURSOR_PID', 'CURSOR_USER_DATA_DIR',
        'WINDSURF_PID', 'CODEIUM_PID', 'CODEIUM_API_KEY',
        'TERM_PROGRAM', 'TERM_PROGRAM_VERSION'
    ]
    
    env_status = {}
    for var in relevant_env_vars:
        val = os.getenv(var)
        if val:
            # Truncate long values for logging
            display_val = val[:50] + '...' if len(val) > 50 else val
            env_status[var] = display_val
    
    if env_status:
        logger.debug(f"IDE detection environment variables: {env_status}")
    
    # Check for Windsurf FIRST (most specific)
    # Windsurf uses Codeium infrastructure but also sets VSCODE_* vars
    # So we need to check for Windsurf before checking VS Code
    
    # Primary Windsurf indicators
    if os.getenv("CODEIUM_PID"):
        logger.info("✓ Detected IDE: Windsurf (via CODEIUM_PID)")
        return IDEType.WINDSURF
    
    if os.getenv("WINDSURF_PID"):
        logger.info("✓ Detected IDE: Windsurf (via WINDSURF_PID)")
        return IDEType.WINDSURF
    
    # Check TERM_PROGRAM for Windsurf
    term_program = os.getenv("TERM_PROGRAM")
    if term_program and "windsurf" in term_program.lower():
        logger.info(f"✓ Detected IDE: Windsurf (via TERM_PROGRAM={term_program})")
        return IDEType.WINDSURF
    
    # Check if VSCODE_* vars are set but with Windsurf-specific paths
    vscode_ipc = os.getenv("VSCODE_IPC_HOOK")
    if vscode_ipc and ("windsurf" in vscode_ipc.lower() or "codeium" in vscode_ipc.lower()):
        logger.info(f"✓ Detected IDE: Windsurf (via VSCODE_IPC_HOOK path containing windsurf/codeium)")
        return IDEType.WINDSURF
    
    # Check for Cursor
    if os.getenv("CURSOR_PID") or os.getenv("CURSOR_USER_DATA_DIR"):
        logger.info("Detected IDE: Cursor")
        return IDEType.CURSOR
    
    # Check for VS Code (check last as it's most generic)
    if os.getenv("VSCODE_PID") or os.getenv("VSCODE_CWD") or os.getenv("VSCODE_IPC_HOOK"):
        logger.info("Detected IDE: VS Code")
        return IDEType.VSCODE
    
    # Fallback: check which IDE's settings directory exists
    logger.warning("Could not detect IDE from environment variables, checking installed IDEs...")
    ide_mgr = get_ide_manager()
    installed = ide_mgr.detect_installed_ides()
    
    # Return the first installed IDE as a guess
    if installed:
        logger.info(f"Using first installed IDE as fallback: {installed[0]}")
        return installed[0]
    
    logger.warning("No IDE could be detected")
    return None


def get_current_ide() -> Optional[IDEType]:
    """
    Get the current IDE (detected or user-specified).
    
    Returns:
        Current IDE type, or None if cannot determine
    """
    global _current_ide
    
    if _current_ide is None:
        _current_ide = detect_current_ide()
    
    return _current_ide


def set_current_ide(ide_type: IDEType):
    """
    Set the current IDE explicitly.
    
    Args:
        ide_type: IDE type to use
    """
    global _current_ide
    _current_ide = ide_type


def detect_workspace_root(ide_type: Optional[IDEType] = None, start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Dynamically detect the workspace root directory by looking for IDE-specific markers.
    
    Detection order:
    1. IDE-provided environment variables (VSCODE_CWD, etc.)
    2. Walk up from start_path looking for markers:
       - .windsurf/ directory (Windsurf)
       - .cursor/ directory (Cursor)
       - .vscode/ directory (VS Code)
       - .git/ directory (fallback)
    
    Args:
        ide_type: IDE type to search for (searches all if None)
        start_path: Starting path to search from (uses cwd if None)
    
    Returns:
        Path to workspace root, or None if not found
    """
    # First, check for IDE-provided workspace environment variables
    ide_workspace_vars = [
        'VSCODE_CWD',           # VS Code workspace directory
        'VSCODE_WORKSPACE',     # VS Code workspace file location
        'CURSOR_WORKSPACE',     # Cursor workspace (if available)
        'WINDSURF_WORKSPACE',   # Windsurf workspace (if available)
    ]
    
    for var in ide_workspace_vars:
        workspace_path = os.getenv(var)
        if workspace_path:
            workspace = Path(workspace_path)
            if workspace.exists() and workspace.is_dir():
                logger.info(f"Found workspace from {var}: {workspace}")
                return workspace
            elif workspace.exists() and workspace.suffix in ['.code-workspace', '.workspace']:
                # It's a workspace file, use its parent directory
                workspace_dir = workspace.parent
                logger.info(f"Found workspace from {var} (workspace file): {workspace_dir}")
                return workspace_dir
    
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)
    
    logger.debug(f"Workspace detection starting from: {start_path}")
    
    # IDE-specific directory markers
    ide_markers = {
        IDEType.WINDSURF: ['.windsurf'],
        IDEType.CURSOR: ['.cursor'],
        IDEType.VSCODE: ['.vscode']
    }
    
    # Build list of markers to search for
    markers_to_search = []
    if ide_type:
        markers_to_search = ide_markers.get(ide_type, [])
        logger.debug(f"Searching for {ide_type} markers: {markers_to_search}")
    else:
        # Search for all IDE markers
        for markers in ide_markers.values():
            markers_to_search.extend(markers)
        logger.debug(f"Searching for all IDE markers")
    
    # Add common markers
    markers_to_search.append('.git')
    logger.debug(f"All markers to search: {markers_to_search}")
    
    # Walk up the directory tree
    current = start_path.resolve()
    
    # Limit search depth to prevent infinite loops
    max_depth = 10
    depth = 0
    
    while current != current.parent and depth < max_depth:
        logger.debug(f"Checking directory [{depth}]: {current}")
        # Check for any marker directory
        for marker in markers_to_search:
            marker_path = current / marker
            if marker_path.exists() and marker_path.is_dir():
                logger.info(f"✓ Found workspace root at {current} (marker: {marker})")
                return current
        
        current = current.parent
        depth += 1
    
    # No workspace root found
    logger.warning(f"✗ Could not detect workspace root from {start_path}")
    return None


def get_workspace_dir(ide_type: Optional[IDEType] = None) -> Path:
    """
    Get the workspace directory, attempting dynamic detection first.
    
    Args:
        ide_type: IDE type for targeted detection
    
    Returns:
        Path to workspace directory
    """
    # Try environment variable first
    env_workspace = os.getenv("WORKSPACE_DIR")
    if env_workspace:
        workspace = Path(env_workspace)
        if workspace.exists():
            logger.info(f"Using workspace from WORKSPACE_DIR: {workspace}")
            return workspace
    
    # Try dynamic detection
    detected = detect_workspace_root(ide_type)
    if detected:
        return detected
    
    # Fallback to current working directory
    fallback = Path.cwd()
    logger.warning(f"Using fallback workspace: {fallback}")
    return fallback


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
    """Load team configuration from file or URL with detailed error reporting"""
    global _current_config, BASE_DIR, CACHE_DIR, CONTENT_DIR, BACKUP_DIR
    
    config_source = CONFIG_FILE
    
    try:
        if config_source.startswith(('http://', 'https://')):
            # Remote config file
            logger.info(f"Loading remote config from: {config_source}")
            headers = {}
            if GITHUB_TOKEN and "github" in config_source:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
                headers["Accept"] = "application/vnd.github.v3+json"
            
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(config_source, headers=headers, timeout=10.0)
                response.raise_for_status()
                
                # Handle GitHub API response (base64 encoded content)
                if "api.github.com" in config_source:
                    import base64
                    response_json = response.json()
                    content = base64.b64decode(response_json['content']).decode('utf-8')
                    logger.info(f"Successfully fetched config from GitHub API ({len(content)} bytes)")
                else:
                    content = response.text
                    logger.info(f"Successfully fetched config ({len(content)} bytes)")
                
                config = ConfigLoader.load_from_string(content)
                
                if not config:
                    logger.error("⚠️  CONFIG PARSE ERROR: Failed to parse YAML content")
                    logger.error("   Check for YAML syntax errors in your team_config.yaml")
                    logger.error(f"   Source: {config_source}")
                    return create_default_config()
        else:
            # Local config file
            config_path = Path(config_source)
            logger.info(f"Loading local config from: {config_path}")
            
            if config_path.exists():
                logger.info(f"Config file found, parsing...")
                config = ConfigLoader.load_from_file(config_path)
                
                if not config:
                    logger.error("⚠️  CONFIG PARSE ERROR: Failed to parse local config file")
                    logger.error(f"   File: {config_path}")
                    logger.error("   Check for YAML syntax errors or missing required fields")
                    return create_default_config()
            else:
                # Create default config
                logger.warning(f"⚠️  Config file not found: {config_path}")
                logger.info("Creating default configuration...")
                config = create_default_config()
                ConfigLoader.save_to_file(config, config_path)
                logger.info(f"✓ Created default configuration at {config_path}")
        
        if config:
            _current_config = config
            # Reinitialize directories based on the loaded config's repo URL
            BASE_DIR, CACHE_DIR, CONTENT_DIR, BACKUP_DIR = get_base_directories(config)
            
            logger.info("="*80)
            logger.info("✓ Configuration loaded successfully")
            logger.info(f"  Source: {config_source}")
            logger.info(f"  Team: {config.team_name}")
            logger.info(f"  Profiles: {len(config.profiles)}")
            logger.info(f"  Directory: {BASE_DIR}")
            
            # Verify this is not the default fallback config
            if config.team_name == "default_fallback":
                logger.warning("⚠️  ATTENTION: Using fallback default configuration!")
                logger.warning("   This means the GitHub config could not be loaded.")
            
            # Log any profiles with MCP servers
            for profile_name, profile in config.profiles.items():
                logger.info(f"  Profile '{profile_name}': Active={profile.active}")
                if profile.mcp_servers:
                    logger.info(f"    - {len(profile.mcp_servers)} MCP servers configured")
                if profile.rules:
                    logger.info(f"    - {len(profile.rules)} rule sources configured")
                if profile.workflows:
                    logger.info(f"    - {len(profile.workflows)} workflow sources configured")
            logger.info("="*80)
            
            return config
        else:
            logger.warning("⚠️  Config loaded but returned None, using default")
            return create_default_config()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"⚠️  HTTP ERROR: Failed to fetch remote config")
        logger.error(f"   URL: {config_source}")
        logger.error(f"   Status: {e.response.status_code}")
        if e.response.status_code == 401:
            logger.error(f"   Authentication failed - check your GITHUB_TOKEN")
            logger.error(f"   Token is {'SET' if GITHUB_TOKEN else 'NOT SET'}")
        elif e.response.status_code == 404:
            logger.error(f"   Config file not found in repository")
            logger.error(f"   Repository: {TEAM_CONFIG_REPO}")
            logger.error(f"   Branch: {TEAM_CONFIG_BRANCH}")
            logger.error(f"   File: {os.getenv('TEAM_CONFIG_FILE', 'team_config.yaml')}")
        logger.error(f"   Response: {e.response.text[:200]}...")
        
        # If TEAM_CONFIG_REPO is set, don't fall back to default - fail clearly
        if TEAM_CONFIG_REPO:
            logger.error("❌ TEAM_CONFIG_REPO is set but cannot fetch config from GitHub")
            logger.error("   Please fix the GitHub configuration or unset TEAM_CONFIG_REPO")
            logger.error("   Using default config as fallback...")
        return create_default_config()
    except httpx.RequestError as e:
        logger.error(f"⚠️  NETWORK ERROR: Cannot reach config source")
        logger.error(f"   URL: {config_source}")
        logger.error(f"   Error: {e}")
        
        if TEAM_CONFIG_REPO:
            logger.error("❌ TEAM_CONFIG_REPO is set but cannot connect to GitHub")
            logger.error("   Check your network connection")
            logger.error("   Using default config as fallback...")
        return create_default_config()
    except Exception as e:
        logger.error(f"⚠️  UNEXPECTED ERROR loading config from {config_source}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Error message: {e}")
        import traceback
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        
        if TEAM_CONFIG_REPO:
            logger.error("❌ TEAM_CONFIG_REPO is set but config loading failed")
            logger.error("   Using default config as fallback...")
        return create_default_config()


def create_default_config() -> TeamConfig:
    """Create a default team configuration"""
    from schemas import Profile, SecurityConfig, SecurityLevel
    
    logger.warning("="*80)
    logger.warning("⚠️  USING DEFAULT CONFIGURATION")
    logger.warning("="*80)
    logger.warning("This is a fallback configuration with no profiles or content.")
    if TEAM_CONFIG_REPO:
        logger.warning(f"Expected to load from: {TEAM_CONFIG_REPO}")
        logger.warning(f"But encountered an error. See above for details.")
    logger.warning("="*80)
    
    default_profile = Profile(
        name="default",
        active=True,
        description="Default profile - no content configured",
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
        team_name="default_fallback",
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
# INTERNAL HELPER FUNCTIONS
# These are NOT exposed as MCP tools - they're called by the consolidated tools
# ============================================================================

async def sync_team_config(
    profile_name: Optional[str] = None,
    force_update: bool = False,
    sync_to_ides: bool = True,
    scope: str = "workspace",
    workspace_path: Optional[str] = None
) -> str:
    """
    Sync team configuration from central repository and update all IDEs.
    
    This is the main tool to fetch and apply team configurations including:
    - Instructions (AI guidance files)
    - Rules (coding standards)
    - Workflows (development processes)
    - Prompts (reusable AI prompts)
    - MCP server configurations
    
    Files are saved to IDE-specific directories based on scope:
    
    Scope Options:
    - "workspace" (default): Only sync to current workspace (.windsurf/, .cursor/, .vscode/)
    - "global": Only sync to global user directories (~/.windsurf/, etc.)
    - "both": Sync to both global and workspace
    - "auto": Detects workspace automatically, falls back to global if not found
    
    Global locations:
    - VS Code: ~/vscode-instructions/{profile}/
    - Cursor: ~/cursor-instructions/{profile}/
    - Windsurf: ~/windsurf-instructions/{profile}/
    
    Workspace locations:
    - VS Code: {workspace}/.vscode/rules/
    - Cursor: {workspace}/.cursor/rules/
    - Windsurf: {workspace}/.windsurf/rules/
    
    Args:
        profile_name: Profile to sync (uses active profile if None)
        force_update: Force pull from remote even if recently updated
        sync_to_ides: Sync to all detected IDEs (Windsurf, Cursor, VS Code)
        scope: Where to sync - "workspace" (default), "global", "both", or "auto"
        workspace_path: Absolute path to project root (auto-detected if not provided)
    
    Returns:
        JSON response with sync results, scope used, and any security issues
    """
    from mcp_tools import sync_profile_tool
    
    config = load_team_config()
    ide_manager = get_ide_manager()
    current_ide = get_current_ide()
    
    # Determine workspace based on scope and provided workspace_path
    workspace_dir = None
    scope_used = scope
    
    if sync_to_ides:
        # If workspace_path provided, use it
        if workspace_path:
            workspace_dir = Path(workspace_path)
            if not workspace_dir.exists():
                return json.dumps({
                    "success": False,
                    "error": f"Provided workspace_path does not exist: {workspace_path}",
                    "hint": "Provide an absolute path to an existing project directory"
                })
            logger.info(f"Using provided workspace path: {workspace_dir}")
            if scope == "auto":
                scope_used = "workspace"
        
        if scope == "workspace":
            # Default behavior: sync to workspace (local)
            if not workspace_dir:
                workspace_dir = detect_workspace_root(current_ide)
            if not workspace_dir:
                return json.dumps({
                    "success": False,
                    "error": "No workspace provided or detected. Please provide workspace_path parameter.",
                    "hint": "sync(action='full', workspace_path='/absolute/path/to/project')",
                    "example": "sync(action='full', workspace_path='/Users/username/my-project')",
                    "note": "Default scope is 'workspace' (local). Use scope='global' for global sync."
                })
            logger.info(f"Using workspace scope: {workspace_dir}")
        
        elif scope == "auto":
            # Use provided workspace_path or try to detect
            if not workspace_dir:
                detected = detect_workspace_root(current_ide)
                if detected:
                    workspace_dir = detected
                    scope_used = "workspace"
                    logger.info(f"Auto-detected workspace scope: {workspace_dir}")
                else:
                    workspace_dir = None
                    scope_used = "global"
                    logger.info("Auto-detected global scope (no workspace found)")
        
        elif scope == "workspace_old":
            # Old workspace handling (kept for backward compatibility)
            # Must have workspace_path or be able to detect it
            if not workspace_dir:
                workspace_dir = detect_workspace_root(current_ide)
            if not workspace_dir:
                return json.dumps({
                    "success": False,
                    "error": "No workspace provided or detected. Please provide workspace_path parameter.",
                    "hint": "sync(action='full', workspace_path='/absolute/path/to/project', scope='workspace')",
                    "example": "sync(action='full', workspace_path='/Users/username/my-project')"
                })
            logger.info(f"Using workspace scope: {workspace_dir}")
        
        elif scope == "global":
            # Force global scope (no workspace)
            workspace_dir = None
            logger.info("Using global scope (user home directories)")
        
        elif scope == "both":
            # Use provided workspace_path or detect
            if not workspace_dir:
                workspace_dir = detect_workspace_root(current_ide)
            logger.info(f"Using both scopes - workspace: {workspace_dir if workspace_dir else 'none'}")
    
    result = await sync_profile_tool(
        profile_name,
        config,
        CONTENT_DIR,
        ide_manager,
        fetch_content_from_source,
        workspace_dir,
        current_ide,
        get_ide_content_dir
    )
    
    # Add scope info to result
    try:
        result_data = json.loads(result)
        result_data["scope"] = scope_used
        if workspace_dir:
            result_data["workspace_path"] = str(workspace_dir)
        return json.dumps(result_data, indent=2)
    except:
        return result


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
        current_ide = get_current_ide()
        workspace_dir = get_workspace_dir(current_ide)
        
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
            workspace_dir
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


async def deactivate_profile(profile_name: Optional[str] = None) -> str:
    """
    Fully deactivate a profile by removing all its managed content and MCP servers.
    
    This performs a complete cleanup:
    - Removes MCP servers managed by the profile
    - Cleans up rules, workflows, prompts from all IDEs
    - Clears tracking statefiles
    - Sets profile as inactive (if local config)
    
    Args:
        profile_name: Profile name to deactivate (uses active profile if None)
    
    Returns:
        JSON response with deactivation results
    """
    try:
        config = load_team_config()
        ide_manager = get_ide_manager()
        current_ide = get_current_ide()
        workspace_dir = get_workspace_dir(current_ide)
        
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
        
        profile = config.profiles[profile_name]
        results = {}
        
        # Step 1: Remove MCP servers managed by this profile
        logger.info(f"Removing MCP servers for profile '{profile_name}'")
        mcp_removal_results = {}
        
        for ide_type in config.supported_ides:
            try:
                # Windsurf uses global config, others use workspace-specific
                workspace = None if ide_type == IDEType.WINDSURF else workspace_dir
                
                # Clear the managed servers for this profile by updating with empty list
                success = ide_manager.update_mcp_servers(
                    ide_type,
                    [],  # Empty list to remove all managed servers
                    workspace,
                    merge=True,
                    profile_name=profile_name
                )
                mcp_removal_results[ide_type.value] = success
            except Exception as e:
                logger.error(f"Error removing MCP servers from {ide_type.value}: {e}")
                mcp_removal_results[ide_type.value] = False
        
        results["mcp_servers_removed"] = mcp_removal_results
        
        # Step 2: Cleanup rules, workflows, prompts
        logger.info(f"Cleaning up content for profile '{profile_name}'")
        cleanup_results = ide_manager.cleanup_all_ides(
            profile_name,
            workspace_dir
        )
        results["content_cleaned"] = {ide.value: success for ide, success in cleanup_results.items()}
        
        # Step 3: Mark profile as inactive (if local config)
        if not CONFIG_FILE.startswith(('http://', 'https://')):
            try:
                profile.active = False
                config_path = Path(CONFIG_FILE)
                ConfigLoader.save_to_file(config, config_path)
                results["profile_marked_inactive"] = True
            except Exception as e:
                logger.warning(f"Could not mark profile as inactive: {e}")
                results["profile_marked_inactive"] = False
        else:
            results["profile_marked_inactive"] = "skipped (remote config)"
        
        return json.dumps({
            "success": True,
            "profile": profile_name,
            "results": results,
            "message": f"Profile '{profile_name}' fully deactivated",
            "details": {
                "mcp_servers_count": len(profile.mcp_servers),
                "rules_sources": len(profile.rules),
                "workflows_sources": len(profile.workflows),
                "prompts_sources": len(profile.prompts)
            }
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error deactivating profile: {e}")
        return json.dumps({"success": False, "error": str(e)})


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
            current_ide = get_current_ide()
            workspace_dir = get_workspace_dir(current_ide)
            cleanup_results = ide_manager.cleanup_all_ides(
                previously_active,
                workspace_dir
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
        current_ide = get_current_ide()
        workspace_dir = get_workspace_dir(current_ide)
        
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
            # Windsurf uses global config, others use workspace-specific
            workspace = None if ide_type == IDEType.WINDSURF else workspace_dir
            success = ide_manager.update_mcp_servers(
                ide_type,
                profile.mcp_servers,
                workspace,
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
        workspace_dir = get_workspace_dir(current_ide)
        
        ide_info = {}
        for ide_type in installed:
            settings_path = ide_manager.get_settings_path(ide_type)
            # Windsurf uses global config
            workspace = None if ide_type == IDEType.WINDSURF else workspace_dir
            mcp_path = ide_manager.get_mcp_config_path(ide_type, workspace)
            
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
        
        # Check if IDE could not be detected
        if current_ide is None:
            ide_manager = get_ide_manager()
            installed_ides = ide_manager.detect_installed_ides()
            
            return json.dumps({
                "success": False,
                "error": "Could not detect current IDE",
                "message": "Please specify which IDE you are using with the 'set_ide' tool",
                "detected_ide": None,
                "installed_ides": [ide.value for ide in installed_ides],
                "instructions": "Call set_ide with one of: vscode, cursor, or windsurf"
            }, indent=2)
        
        ide_manager = get_ide_manager()
        settings_path = ide_manager.get_settings_path(current_ide)
        
        return json.dumps({
            "success": True,
            "current_ide": current_ide.value,
            "detected_ide": detected_ide.value if detected_ide else "unknown",
            "auto_detected": detected_ide is not None,
            "settings_path": str(settings_path),
            "instructions_dir": str(get_ide_content_dir(current_ide, "default")),
            "installed_ides": [ide.value for ide in ide_manager.detect_installed_ides()]
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting current IDE: {e}")
        return json.dumps({"success": False, "error": str(e)})


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


# ============================================================================
# EXPOSED MCP TOOLS - Only these 6 tools are exposed to clients
# ============================================================================
# Consolidated action-based tools (4):
#   - profile()       -> list, activate, show, cleanup, deactivate
#   - sync()          -> full, check, reload  
#   - ide()           -> info, list, set
#   - mcp_servers()   -> update, list
#
# Standalone utility tools (2):
#   - validate_content_security()
#   - clear_cache()
# ============================================================================

@mcp.tool()
async def profile(
    action: str = "list",
    profile_name: Optional[str] = None,
    auto_sync: bool = True
) -> str:
    """
    Profile management - unified tool for all profile operations.
    
    Actions:
        list - List all available profiles with their configurations
        activate - Set a profile as active and optionally sync
        show - Show detailed configuration for current or specified profile
        cleanup - Remove profile rules from IDEs (rules/workflows only)
        deactivate - Fully deactivate profile (removes MCP servers, rules, workflows, prompts)
    
    Args:
        action: Operation to perform (list, activate, show, cleanup, deactivate)
        profile_name: Profile name (required for activate/cleanup/deactivate)
        auto_sync: Auto-sync after activation (default: True)
    
    Examples:
        profile(action="list")
        profile(action="activate", profile_name="production", auto_sync=True)
        profile(action="show")
        profile(action="cleanup", profile_name="old-profile")
        profile(action="deactivate", profile_name="default")
    
    Returns:
        JSON response with operation results
    """
    if action == "list":
        return await list_profiles()
    elif action == "activate":
        if not profile_name:
            return json.dumps({
                "success": False,
                "error": "profile_name required for 'activate' action"
            })
        return await set_active_profile(profile_name, auto_sync)
    elif action == "show":
        return await get_config()
    elif action == "cleanup":
        return await cleanup_profile_rules(profile_name)
    elif action == "deactivate":
        return await deactivate_profile(profile_name)
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["list", "activate", "show", "cleanup", "deactivate"],
            "usage": "profile(action='list') or profile(action='deactivate', profile_name='default')"
        })


@mcp.tool()
async def sync(
    action: str = "full",
    workspace_path: Optional[str] = None,
    profile_name: Optional[str] = None,
    force_update: bool = False,
    sync_to_ides: bool = True,
    scope: str = "workspace"
) -> str:
    """
    Synchronization operations - sync content from remote repositories.
    
    ⚠️  IMPORTANT: Always provide workspace_path parameter when syncing!
    
    Actions:
        full - Full sync from remote repository (fetch rules, workflows, etc.)
        check - Check for updates without syncing
        reload - Reload configuration from source
    
    Scope (for 'full' action):
        workspace - (DEFAULT) Only sync to workspace (.windsurf/, .cursor/, .vscode/)
        global - Only sync to global user directories (~/.windsurf/, etc.)
        both - Sync to both global and workspace
        auto - Use provided workspace_path, fallback to global if None
    
    Args:
        action: Operation to perform (full, check, reload)
        workspace_path: **REQUIRED for workspace sync** - Absolute path to project root
                       (where .vscode/.cursor/.windsurf directories should be created)
        profile_name: Profile to sync (uses active if None)
        force_update: Force update even if recently synced
        sync_to_ides: Sync to IDE directories
        scope: Where to sync - "workspace" (default), "global", "both", or "auto"
    
    Examples:
        # Sync to specific workspace (RECOMMENDED)
        sync(action="full", workspace_path="/absolute/path/to/project")
        
        # Sync only to workspace
        sync(action="full", workspace_path="/absolute/path/to/project", scope="workspace")
        
        # Sync only to global user directories
        sync(action="full", scope="global")
        
        # Sync to both global and workspace
        sync(action="full", workspace_path="/absolute/path/to/project", scope="both")
        
        # Other actions
        sync(action="check")
        sync(action="reload")
    
    Returns:
        JSON response with sync results and scope information
    """
    if action == "full":
        return await sync_team_config(profile_name, force_update, sync_to_ides, scope, workspace_path)
    elif action == "check":
        return await check_for_updates()
    elif action == "reload":
        return await reload_config()
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["full", "check", "reload"],
            "usage": "sync(action='full', scope='workspace') or sync(action='check')"
        })


@mcp.tool()
async def mcp_servers(
    action: str = "update",
    profile_name: Optional[str] = None,
    reload: bool = True
) -> str:
    """
    MCP server management - configure and list MCP servers.
    
    Actions:
        update - Update MCP server configurations from profile
        list - List configured MCP servers
    
    Args:
        action: Operation to perform (update, list)
        profile_name: Profile to use (uses active if None)
        reload: Reload IDE after update
    
    Examples:
        mcp_servers(action="list")
        mcp_servers(action="update")
        mcp_servers(action="update", profile_name="production")
    
    Returns:
        JSON response with results
    """
    if action == "update":
        return await update_mcp_servers(profile_name, reload)
    elif action == "list":
        try:
            config = load_team_config()
            
            if profile_name:
                if profile_name not in config.profiles:
                    return json.dumps({
                        "success": False,
                        "error": f"Profile '{profile_name}' not found"
                    })
                prof = config.profiles[profile_name]
            else:
                active_profiles = [p for p in config.profiles.values() if p.active]
                if not active_profiles:
                    return json.dumps({"success": False, "error": "No active profile found"})
                prof = active_profiles[0]
            
            servers_info = []
            for server in prof.mcp_servers:
                servers_info.append({
                    "name": server.name,
                    "enabled": server.enabled,
                    "command": server.command if server.command else None,
                    "url": server.url if server.url else None,
                    "type": server.type if server.type else "stdio",
                    "description": server.description
                })
            
            return json.dumps({
                "success": True,
                "profile": prof.name,
                "servers": servers_info,
                "total": len(servers_info)
            }, indent=2)
        except Exception as e:
            logger.error(f"Error listing MCP servers: {e}")
            return json.dumps({"success": False, "error": str(e)})
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["update", "list"],
            "usage": "mcp_servers(action='list') or mcp_servers(action='update')"
        })


@mcp.tool()
async def ide(
    action: str = "info",
    ide_name: Optional[str] = None
) -> str:
    """
    IDE management - detect, list, and configure IDE.
    
    Actions:
        info - Get current IDE information
        list - List all installed IDEs
        set - Set IDE explicitly
    
    Args:
        action: Operation to perform (info, list, set)
        ide_name: IDE name for 'set' action (vscode, cursor, windsurf)
    
    Examples:
        ide(action="info")
        ide(action="list")
        ide(action="set", ide_name="windsurf")
    
    Returns:
        JSON response with IDE information
    """
    if action == "info":
        return await get_current_ide_info()
    elif action == "list":
        return await list_installed_ides()
    elif action == "set":
        if not ide_name:
            return json.dumps({
                "success": False,
                "error": "ide_name required for 'set' action",
                "available_ides": ["vscode", "cursor", "windsurf"]
            })
        return await set_ide(ide_name)
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["info", "list", "set"],
            "usage": "ide(action='info') or ide(action='set', ide_name='windsurf')"
        })


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
        validator = get_security_validator()
        is_valid, violations, severity = validator.validate_content(
            content,
            content_type,
            filename
        )
        
        return json.dumps({
            "success": True,
            "valid": is_valid,
            "violations": violations,
            "severity": severity,
            "filename": filename,
            "content_type": content_type
        }, indent=2)
    except Exception as e:
        logger.error(f"Error validating content: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


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
        repo_manager = get_repo_manager()
        
        if cache_type in ["all", "repos"]:
            # Clear repo cache
            if CACHE_DIR and CACHE_DIR.exists():
                import shutil
                shutil.rmtree(CACHE_DIR)
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared repository cache: {CACHE_DIR}")
        
        if cache_type in ["all", "content"]:
            # Clear content cache
            if CONTENT_DIR and CONTENT_DIR.exists():
                import shutil
                shutil.rmtree(CONTENT_DIR)
                CONTENT_DIR.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared content cache: {CONTENT_DIR}")
        
        return json.dumps({
            "success": True,
            "cleared": cache_type,
            "message": f"Cache '{cache_type}' cleared successfully"
        })
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def diagnose_config() -> str:
    """
    Diagnostic tool to check configuration loading and GitHub connection.
    
    Returns:
        JSON response with diagnostic information
    """
    try:
        diagnostics = {
            "environment": {
                "TEAM_CONFIG_REPO": TEAM_CONFIG_REPO or "NOT SET",
                "TEAM_CONFIG_BRANCH": TEAM_CONFIG_BRANCH,
                "TEAM_CONFIG_FILE": os.getenv('TEAM_CONFIG_FILE', 'team_config.yaml'),
                "GITHUB_TOKEN": "SET" if GITHUB_TOKEN else "NOT SET",
                "CONFIG_SOURCE": CONFIG_FILE
            },
            "current_config": {},
            "github_test": {},
            "recommendations": []
        }
        
        # Test current config
        config = load_team_config()
        diagnostics["current_config"] = {
            "team_name": config.team_name,
            "is_default_fallback": config.team_name == "default_fallback",
            "profiles": list(config.profiles.keys()),
            "active_profile": next((p.name for p in config.profiles.values() if p.active), None)
        }
        
        # Test GitHub connection if TEAM_CONFIG_REPO is set
        if TEAM_CONFIG_REPO:
            try:
                headers = {}
                if GITHUB_TOKEN and "github" in CONFIG_FILE:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                    headers["Accept"] = "application/vnd.github.v3+json"
                
                with httpx.Client(follow_redirects=True) as client:
                    response = client.get(CONFIG_FILE, headers=headers, timeout=10.0)
                    
                    diagnostics["github_test"] = {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "url": CONFIG_FILE,
                        "content_length": len(response.content) if response.status_code == 200 else 0
                    }
                    
                    if response.status_code != 200:
                        diagnostics["github_test"]["error"] = response.text[:200]
            except Exception as e:
                diagnostics["github_test"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Generate recommendations
        if config.team_name == "default_fallback":
            diagnostics["recommendations"].append("⚠️  Using fallback config - GitHub config not loaded")
        
        if TEAM_CONFIG_REPO and not GITHUB_TOKEN:
            diagnostics["recommendations"].append("⚠️  GITHUB_TOKEN not set - may fail for private repos")
        
        if TEAM_CONFIG_REPO and diagnostics.get("github_test", {}).get("status_code") == 404:
            diagnostics["recommendations"].append(f"❌ Config file not found: {os.getenv('TEAM_CONFIG_FILE', 'team_config.yaml')}")
            diagnostics["recommendations"].append(f"   Check that the file exists in branch '{TEAM_CONFIG_BRANCH}'")
        
        if TEAM_CONFIG_REPO and diagnostics.get("github_test", {}).get("status_code") == 401:
            diagnostics["recommendations"].append("❌ Authentication failed - check GITHUB_TOKEN")
        
        if not TEAM_CONFIG_REPO:
            diagnostics["recommendations"].append("ℹ️  TEAM_CONFIG_REPO not set - using local config")
        
        return json.dumps(diagnostics, indent=2)
        
    except Exception as e:
        logger.error(f"Error in diagnostics: {e}")
        import traceback
        return json.dumps({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, indent=2)


def main():
    """Main function to run the Team Configuration MCP server"""
    logger.info("=" * 70)
    logger.info("Starting Team Configuration MCP Server")
    logger.info("=" * 70)
    logger.info(f"Config file: {CONFIG_FILE}")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Content directory: {CONTENT_DIR}")
    
    # Detect workspace and IDE
    detected_ide = detect_current_ide()
    logger.info("=" * 70)
    logger.info("IDE DETECTION")
    logger.info("=" * 70)
    logger.info(f"Current working directory: {Path.cwd()}")
    if detected_ide:
        logger.info(f"✓ Detected IDE: {detected_ide.value.upper()}")
        logger.info(f"  Rules will sync to: .{detected_ide.value}/ directories")
    else:
        logger.warning("⚠️  Could not detect IDE")
        logger.warning("  Use ide(action='set', ide_name='windsurf') to set explicitly")
    
    detected_workspace = detect_workspace_root(detected_ide)
    if detected_workspace:
        logger.info(f"✓ Detected workspace: {detected_workspace}")
    else:
        logger.info(f"  Workspace: Will be detected per-request (dynamic)")
    logger.info("=" * 70)
    
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
