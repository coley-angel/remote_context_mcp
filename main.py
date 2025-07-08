#!/usr/bin/env uv run python
"""
Instructions MCP Server Main Entry Point

This MCP server provides tools for fetching and managing remote instruction
files for GitHub Copilot from centralized team locations. It supports 
profile-based management where teams can maintain different instruction sets.
"""
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import yaml
import httpx
import aiofiles
import fnmatch
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("InstructionsMCP")

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CONFIG_FILE = os.getenv("CONTEXT_CONFIG_FILE", "context_config.yaml")
# Make CONFIG_FILE absolute if it's a relative path
if not CONFIG_FILE.startswith(('http://', 'https://', '/')):
    CONFIG_FILE = str(Path(__file__).parent / CONFIG_FILE)
INSTRUCTIONS_DIR = Path(os.getenv("INSTRUCTIONS_DIR", 
                                  "~/vscode-instructions")).expanduser()

# Default context configurations for different profiles
DEFAULT_CONTEXTS = {
    "profiles": {
        "default": {
            "active": True,
            "instructions": []
        }
    }
}


def load_context_config() -> Dict[str, Any]:
    """Load context configuration from file or return defaults"""
    config_source = CONFIG_FILE
    
    try:
        if config_source.startswith(('http://', 'https://')):
            # Remote config file - use synchronous HTTP client to avoid async issues
            try:
                headers = {}
                if GITHUB_TOKEN and "github.com" in config_source:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                
                with httpx.Client(follow_redirects=True) as client:
                    response = client.get(config_source, headers=headers, timeout=30.0)
                    response.raise_for_status()
                    content = response.text
                    config = yaml.safe_load(content)
                    if 'profiles' in config:
                        return config
                    else:
                        return DEFAULT_CONTEXTS
            except Exception as e:
                logger.error(f"Failed to fetch remote config: {e}")
                return DEFAULT_CONTEXTS
        else:
            # Local config file
            config_path = Path(config_source)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    content = f.read()
                    config = yaml.safe_load(content)
                    if 'profiles' in config:
                        return config
                    else:
                        return DEFAULT_CONTEXTS
            else:
                return DEFAULT_CONTEXTS
    except Exception as e:
        logger.warning(f"Failed to load config from {config_source}: {e}")
        return DEFAULT_CONTEXTS


async def _fetch_remote_config(url: str) -> Optional[str]:
    """Helper function to fetch remote config file with retry logic"""
    import ssl
    
    # Create SSL context that's more permissive
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    if GITHUB_TOKEN and "github.com" in url:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Try with different HTTP client configurations
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=timeout,
                verify=False,  # Disable SSL verification
                headers=headers
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text
                return content
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} fetching remote config: {e}")
            if e.response.status_code >= 400:
                break  # Don't retry for client errors
        except (httpx.ConnectError, httpx.TimeoutException, ssl.SSLError) as e:
            logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error fetching remote config: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    logger.error(f"Failed to fetch remote config from {url} after {max_retries} attempts")
    return None


def resolve_repository_urls(
    repo_config: Union[str, Dict[str, Any]]
) -> List[str]:
    """Resolve repository configuration to actual URLs"""
    if isinstance(repo_config, str):
        return [repo_config]
    
    if isinstance(repo_config, dict) and "repo" in repo_config:
        repo = repo_config["repo"]
        branch = repo_config.get("branch", "main")
        paths = repo_config.get("paths", ["*.md"])
        
        # Check if any paths contain wildcards
        has_wildcards = any("*" in path for path in paths)
        
        if has_wildcards and GITHUB_TOKEN:
            # Use async wildcard expansion
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    logger.warning(f"Cannot expand wildcards for {repo}")
                    return _generate_basic_urls(repo, branch, paths)
                else:
                    return loop.run_until_complete(
                        fetch_github_files_with_wildcards(repo, branch, paths)
                    )
            except Exception as e:
                logger.warning(f"Failed to expand wildcards for {repo}: {e}")
                return _generate_basic_urls(repo, branch, paths)
        else:
            return _generate_basic_urls(repo, branch, paths)
    
    return []


def _generate_basic_urls(repo: str, branch: str, paths: List[str]) -> List[str]:
    """Generate basic GitHub raw URLs without wildcard expansion"""
    urls = []
    for path in paths:
        if "*" in path:
            # For wildcard patterns, create a general URL
            base_path = path.replace("*", "").replace(".", "")
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{base_path}"
            urls.append(url)
        else:
            url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            urls.append(url)
    return urls


def get_instruction_urls_for_profile(
    profile_name: str,
    config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Get instruction URLs for a specific profile"""
    if config is None:
        config = load_context_config()
    
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        return []
    
    profile_config = profiles[profile_name]
    instruction_configs = profile_config.get("instructions", [])
    
    urls = set()
    for item in instruction_configs:
        urls.update(resolve_repository_urls(item))
    
    return list(urls)


def save_context_config(config: Dict[str, Any]) -> None:
    """Save context configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        logger.info(f"Context configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save config file {CONFIG_FILE}: {e}")


async def fetch_remote_content(
    url: str,
    save_to_directory: Optional[Path] = None,
    profile_name: str = "default"
) -> Optional[str]:
    """
    Fetch content from a remote URL and optionally save to directory.
    
    Args:
        url: URL to fetch content from
        save_to_directory: Directory to save the file to (if provided)
        profile_name: Profile name for unique file naming
    
    Returns:
        Content string if successful, file path if saved, None if failed
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        if GITHUB_TOKEN and "github.com" in url:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(
            follow_redirects=True, 
            timeout=timeout, 
            verify=False  # Disable SSL verification to avoid SSL errors
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            content = response.text
        
        # If save_to_directory is provided, save the file
        if save_to_directory:
            base_filename = url.split("/")[-1]
            
            # Remove existing extensions
            if base_filename.endswith((".md", ".txt")):
                base_filename = base_filename.rsplit(".", 1)[0]
            
            # Generate profile-specific filename
            filename = f"{base_filename}.instructions.md"
            
            file_path = save_to_directory / filename
            save_to_directory.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return str(file_path)  # Return file path when saved
        
        return content
        
    except Exception as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        return None


async def fetch_github_files_with_wildcards(
    repo: str,
    branch: str,
    path_patterns: List[str]
) -> List[str]:
    """
    Fetch file URLs from GitHub repository using wildcard patterns
    
    Args:
        repo: GitHub repository in format "owner/repo"
        branch: Branch name
        path_patterns: List of path patterns with wildcards
    
    Returns:
        List of raw GitHub URLs matching the patterns
    """
    urls = []
    
    if not GITHUB_TOKEN:
        logger.warning("GitHub token not available for wildcard expansion")
        return urls
    
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for pattern in path_patterns:
                if "*" in pattern:
                    # Use GitHub API to search for files
                    api_url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
                    response = await client.get(api_url, headers=headers, timeout=30.0)
                    response.raise_for_status()
                    
                    tree_data = response.json()
                    for item in tree_data.get("tree", []):
                        if item["type"] == "blob":
                            file_path = item["path"]
                            # Simple wildcard matching
                            if _matches_pattern(file_path, pattern):
                                raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
                                urls.append(raw_url)
                else:
                    # Direct file path
                    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{pattern}"
                    urls.append(raw_url)
                    
    except Exception as e:
        logger.error(f"Failed to expand GitHub wildcards for {repo}: {e}")
    
    return urls


def _matches_pattern(file_path: str, pattern: str) -> bool:
    """Simple wildcard pattern matching"""
    return fnmatch.fnmatch(file_path, pattern)


def get_active_profile(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get the active profile configuration"""
    profiles = config.get("profiles", {})
    
    for profile_name, profile_config in profiles.items():
        if profile_config.get("active", False):
            return {
                "name": profile_name,
                "config": profile_config,
                "directory": INSTRUCTIONS_DIR / profile_name
            }
    
    # Default fallback - use first profile if none active
    first_profile = next(iter(profiles.keys()), "default")
    first_config = profiles.get(first_profile, {"instructions": []})
    return {
        "name": first_profile,
        "config": first_config,
        "directory": INSTRUCTIONS_DIR / first_profile
    }


def get_all_profiles(config: Dict[str, Any]) -> List[str]:
    """Get all available profiles"""
    profiles = config.get("profiles", {})
    return list(profiles.keys())


def update_user_settings(profile_directories: Dict[str, bool]) -> None:
    """Update VS Code user settings with instruction directories"""
    try:
        # Get VS Code user settings path
        if sys.platform == "darwin":  # macOS
            settings_path = Path.home() / "Library/Application Support/Code/User/settings.json"
        elif sys.platform == "win32":  # Windows
            settings_path = Path.home() / "AppData/Roaming/Code/User/settings.json"
        else:  # Linux
            settings_path = Path.home() / ".config/Code/User/settings.json"
        
        settings = {}
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                content = f.read()
                if content.strip():
                    settings = json.loads(content)
        
        # Update instruction locations
        settings["chat.instructionsFilesLocations"] = profile_directories
        
        # Ensure directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write updated settings
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        
        logger.info(f"Updated VS Code user settings at {settings_path}")
        
    except Exception as e:
        logger.error(f"Failed to update user settings: {e}")


@mcp.tool()
async def fetch_and_sync_instructions(profile_name: Optional[str] = None) -> str:
    """
    Fetch and sync instruction files for a profile.

    Note: If switching between profiles, start a NEW CHAT conversation
    for the updated instructions to take effect properly.

    Args:
        profile_name: Profile to sync (uses active profile if None)

    Returns:
        JSON response indicating success or failure
    """
    try:
        config = load_context_config()
        
        if profile_name is None:
            active_profile = get_active_profile(config)
            profile_name = active_profile["name"]
        
        profiles = config.get("profiles", {})
        if profile_name not in profiles:
            return json.dumps({
                "success": False,
                "error": f"Profile '{profile_name}' not found"
            })
        
        # Get instruction URLs for the profile
        instruction_urls = get_instruction_urls_for_profile(profile_name, config)
        
        if not instruction_urls:
            return json.dumps({
                "success": True,
                "message": f"No instruction URLs configured for profile '{profile_name}'",
                "synced_files": []
            })
        
        # Create profile directory
        profile_dir = INSTRUCTIONS_DIR / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Fetch and save instructions
        synced_files = []
        failed_urls = []
        
        for url in instruction_urls:
            file_path = await fetch_remote_content(
                url, profile_dir, profile_name
            )
            if file_path:
                synced_files.append(file_path)
            else:
                failed_urls.append(url)
        
        # Update user settings with all profile directories
        profile_directories = {}
        for prof_name in profiles.keys():
            prof_dir = str(INSTRUCTIONS_DIR / prof_name)
            profile_directories[prof_dir] = profiles[prof_name].get("active", False)
        
        update_user_settings(profile_directories)
        
        return json.dumps({
            "success": True,
            "message": f"Synced instructions for profile '{profile_name}'",
            "synced_files": synced_files,
            "failed_urls": failed_urls,
            "profile_directory": str(profile_dir)
        })
        
    except Exception as e:
        logger.error(f"Error syncing instructions: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def get_available_profiles() -> str:
    """
    Get all available profiles and their configurations.
    
    Returns:
        JSON response with available profiles
    """
    try:
        config = load_context_config()
        profiles = config.get("profiles", {})
        
        profile_info = {}
        for profile_name, profile_config in profiles.items():
            profile_info[profile_name] = {
                "active": profile_config.get("active", False),
                "directory": str(INSTRUCTIONS_DIR / profile_name),
                "instruction_count": len(profile_config.get("instructions", []))
            }
        
        return json.dumps({
            "success": True,
            "profiles": profile_info,
            "instructions_base_dir": str(INSTRUCTIONS_DIR)
        })
        
    except Exception as e:
        logger.error(f"Error getting available profiles: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def set_active_profile(profile_name: str) -> str:
    """
    Set the active profile.

    IMPORTANT: After switching profiles, start a NEW CHAT conversation
    to use the new instructions effectively, or manually tell Copilot
    to ignore previous context from the old profile.

    Args:
        profile_name: Name of the profile to activate

    Returns:
        JSON response indicating success or failure
    """
    try:
        config = load_context_config()
        profiles = config.get("profiles", {})
        
        if profile_name not in profiles:
            available_profiles = list(profiles.keys())
            return json.dumps({
                "success": False,
                "error": f"Profile '{profile_name}' not found. Available profiles: {available_profiles}"
            })
        
        # Deactivate all profiles
        for name, profile_config in profiles.items():
            profile_config["active"] = False
        
        # Activate the requested profile
        profiles[profile_name]["active"] = True
        
        # Save updated configuration
        save_context_config(config)
        
        # Update user settings with all profile directories
        profile_directories = {}
        for prof_name in profiles.keys():
            prof_dir = str(INSTRUCTIONS_DIR / prof_name)
            profile_directories[prof_dir] = profiles[prof_name].get("active", False)
        
        update_user_settings(profile_directories)
        
        return json.dumps({
            "success": True,
            "message": f"Profile '{profile_name}' activated",
            "active_profile": {
                "name": profile_name,
                "directory": str(INSTRUCTIONS_DIR / profile_name)
            }
        })
        
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_context_config() -> str:
    """
    List the current context configuration showing all profiles and their instructions.

    Returns:
        JSON string with the complete context configuration
    """
    try:
        config = load_context_config()
        return json.dumps(config, indent=2)
    except Exception as e:
        logger.error(f"Error listing context config: {e}")
        return json.dumps({"error": str(e)})


def main():
    """Main function to run the Instructions MCP server"""
    logger.info("Starting Instructions MCP server...")
    logger.info(f"Config file: {CONFIG_FILE}")
    logger.info(f"Instructions directory: {INSTRUCTIONS_DIR}")
    
    # Test config loading and print what we get
    logger.info("=" * 50)
    logger.info("TESTING CONFIG LOADING:")
    config = load_context_config()
    logger.info(f"Loaded config: {json.dumps(config, indent=2)}")
    logger.info("=" * 50)
    
    # Create instructions directory if it doesn't exist
    INSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create default config if it doesn't exist (only for local files)
    if not CONFIG_FILE.startswith(('http://', 'https://')):
        config_path = Path(CONFIG_FILE)
        if not config_path.exists():
            save_context_config(DEFAULT_CONTEXTS)
            logger.info("Created default context configuration")
    
    mcp.run()
    logger.info("Instructions MCP server completed")


if __name__ == "__main__":
    main()
