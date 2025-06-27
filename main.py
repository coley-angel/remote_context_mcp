#!/usr/bin/env python3
"""
Remote Context MCP Server Main Entry Point

This MCP server provides tools for fetching and managing remote context files
for GitHub Copilot. It can fetch files from URLs, GitHub repositories, and
other remote sources to provide contextual information based on project type
or repository characteristics.
"""
import sys
import logging
import os
import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from dotenv import load_dotenv
import httpx
import aiofiles
import git
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
mcp = FastMCP("RemoteContextMCP")

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
CONFIG_FILE = os.getenv("CONTEXT_CONFIG_FILE", "context_config.yaml")
WORKDIR = Path(os.getenv("CONTEXT_WORKDIR", "."))

# Default context configurations for different project types
DEFAULT_CONTEXTS = {}


def load_context_config() -> Dict[str, Any]:
    """Load context configuration from file or remote URL or return defaults"""
    config_source = CONFIG_FILE
    
    try:
        if config_source.startswith(('http://', 'https://')):
            # Remote config file
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, can't run another loop
                logger.warning(f"Cannot load remote config {config_source} from async context")
                return DEFAULT_CONTEXTS
            else:
                content = loop.run_until_complete(_fetch_remote_config(config_source))
                if content:
                    config = yaml.safe_load(content)
                    if 'project_types' in config:
                        return config
                    else:
                        pass
                else:
                    logger.warning(f"Failed to load remote config {config_source}")
                    return DEFAULT_CONTEXTS
        else:
            # Local config file
            config_path = Path(config_source)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if 'project_types' in config:
                        return config
                    else:
                        pass
            else:
                logger.info(f"Config file {config_path} not found, using defaults")
                return DEFAULT_CONTEXTS
    except Exception as e:
        logger.warning(f"Failed to load config from {config_source}: {e}")
        return DEFAULT_CONTEXTS


async def _fetch_remote_config(url: str) -> Optional[str]:
    """Helper function to fetch remote config file"""
    try:
        headers = {}
        if GITHUB_TOKEN and "github.com" in url:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to fetch remote config from {url}: {e}")
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
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, can't run another loop
                    logger.warning(f"Cannot expand wildcards for {repo} from sync context")
                    # Fall back to basic URL generation
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


def get_context_urls_for_project(
    project_types: List[str],
    conditions: Dict[str, bool],
    context_type: str = "instructions",
    config: Optional[Dict[str, Any]] = None,
    profile_name: Optional[str] = None
) -> List[str]:
    """Get URLs for a specific context type based on project characteristics"""
    if config is None:
        config = load_context_config()
    
    urls = set()
    
    # Handle the new profile-based config format
    if "project_types" in config:
        project_configs = config.get("project_types", {})
        
        for project_type in project_types:
            if project_type in project_configs:
                # Get the active profile for this project type
                if profile_name:
                    # Use specific profile if provided
                    project_profiles = project_configs[project_type]
                    profile_config = project_profiles.get(profile_name)
                    if not profile_config:
                        continue
                else:
                    # Get active profile
                    active_profile = get_active_profile(config, project_type)
                    profile_config = active_profile["config"]
                
                # Always fetch URLs for this context type
                always_fetch = profile_config.get("always_fetch", {})
                if context_type in always_fetch:
                    for item in always_fetch[context_type]:
                        urls.update(resolve_repository_urls(item))
                
                # Conditional URLs
                conditional = profile_config.get("conditional", {})
                for condition, condition_config in conditional.items():
                    if conditions.get(condition, False):
                        if context_type in condition_config:
                            for item in condition_config[context_type]:
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


def detect_project_type(directory: Path) -> List[str]:
    """Detect project type(s) based on files in directory"""
    project_types = []
    
    # Check for various file indicators
    files = {f.name for f in directory.rglob("*") if f.is_file()}
    
    # Python indicators
    python_files = ["requirements.txt", "setup.py", "pyproject.toml",
                    "__init__.py"]
    if any(f in files for f in python_files):
        project_types.append("python")
    
    # JavaScript/TypeScript indicators
    if "package.json" in files:
        project_types.append("javascript")
        if "tsconfig.json" in files or any(f.endswith('.ts') for f in files):
            project_types.append("typescript")
    
    # Rust indicators
    if "Cargo.toml" in files:
        project_types.append("rust")
    
    # Go indicators
    if "go.mod" in files or any(f.endswith('.go') for f in files):
        project_types.append("go")
    
    return project_types or ["generic"]


def detect_frameworks_and_libraries(directory: Path) -> Dict[str, bool]:
    """Detect specific frameworks and libraries in the project"""
    conditions = {}
    
    try:
        # Check package.json for JS/TS dependencies
        package_json = directory / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {})
                }
                
                conditions["has_package_json"] = True
                conditions["has_react"] = "react" in deps
                conditions["has_nextjs"] = "next" in deps
                conditions["has_express"] = "express" in deps
                conditions["has_typescript"] = "typescript" in deps
        
        # Check requirements.txt for Python dependencies
        requirements_txt = directory / "requirements.txt"
        if requirements_txt.exists():
            with open(requirements_txt, 'r') as f:
                content = f.read().lower()
                conditions["has_requirements_txt"] = True
                conditions["has_django"] = "django" in content
                conditions["has_flask"] = "flask" in content
                conditions["has_fastapi"] = "fastapi" in content
        
        # Check pyproject.toml
        pyproject_toml = directory / "pyproject.toml"
        if pyproject_toml.exists():
            conditions["has_pyproject_toml"] = True
            # Could parse TOML to check for specific dependencies
        
        # Check setup.py
        setup_py = directory / "setup.py"
        if setup_py.exists():
            conditions["has_setup_py"] = True
        
        # Check for other config files
        conditions["has_tsconfig"] = (directory / "tsconfig.json").exists()
        conditions["has_cargo_toml"] = (directory / "Cargo.toml").exists()
        conditions["has_go_mod"] = (directory / "go.mod").exists()
        
    except Exception as e:
        logger.warning(f"Error detecting frameworks: {e}")
    
    return conditions


async def fetch_remote_content(
    url: str,
    save_to_directory: Optional[Path] = None,
    context_type: str = "instructions",
    profile_name: str = "default"
) -> Optional[str]:
    """
    Fetch content from a remote URL and optionally save directly to
    context directories. Handles redirects and GitHub API wildcards.
    
    Args:
        url: URL to fetch content from
        save_to_directory: Directory to save the file to (if provided)
        context_type: Type of context (instructions, chatmodes, prompts)
        profile_name: Profile name for unique file naming
    
    Returns:
        Content string if successful, file path if saved, None if failed
    """
    try:
        headers = {}
        if GITHUB_TOKEN and "github.com" in url:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            content = response.text
        
        # If save_to_directory is provided, save directly to context directory
        if save_to_directory:
            base_filename = url.split("/")[-1]
            
            # Remove existing extensions
            if base_filename.endswith((".md", ".txt")):
                base_filename = base_filename.rsplit(".", 1)[0]
            
            # Generate profile-specific filename
            filename = get_profile_filename(
                base_filename, profile_name, context_type
            )
            
            file_path = save_to_directory / filename
            save_to_directory.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            logger.info(f"Saved {context_type} content to {file_path}")
            return str(file_path)  # Return file path when saved
        
        logger.info(f"Fetched remote content from {url}")
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
    import fnmatch
    return fnmatch.fnmatch(file_path, pattern)


def get_github_file_url(
    repo: str, file_path: str, branch: str = "main"
) -> str:
    """Convert GitHub repo/file reference to raw URL"""
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"


def analyze_git_repository(directory: Path) -> Dict[str, Any]:
    """Analyze git repository for additional context"""
    try:
        repo = git.Repo(directory)
        
        # Get repository information
        origin_url = None
        try:
            origin_url = repo.remotes.origin.url
        except Exception:
            pass
        
        # Get recent commits for context
        recent_commits = []
        try:
            for commit in repo.iter_commits(max_count=5):
                recent_commits.append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat()
                })
        except Exception:
            pass
        
        # Get current branch
        current_branch = None
        try:
            current_branch = repo.active_branch.name
        except Exception:
            pass
        
        return {
            "is_git_repo": True,
            "origin_url": origin_url,
            "current_branch": current_branch,
            "recent_commits": recent_commits
        }
    except Exception:
        return {"is_git_repo": False}


def get_active_profile(
    config: Dict[str, Any], project_type: str
) -> Dict[str, Any]:
    """Get the active profile configuration for a project type"""
    project_configs = config.get("project_types", {})
    if project_type not in project_configs:
        # Default fallback
        return {
            "name": "default",
            "project_type": project_type,
            "config": {"always_fetch": {}, "conditional": {}},
            "directories": {
                "instructions": ".github/default/instructions",
                "chatmodes": ".github/default/chatmodes",
                "prompts": ".github/default/prompts"
            }
        }
    
    profiles = project_configs[project_type]
    for profile_name, profile_config in profiles.items():
        if profile_config.get("active", False):
            return {
                "name": profile_name,
                "project_type": project_type,
                "config": profile_config,
                "directories": {
                    "instructions": f".github/{profile_name}/instructions",
                    "chatmodes": f".github/{profile_name}/chatmodes",
                    "prompts": f".github/{profile_name}/prompts"
                }
            }
    
    # Default fallback - use first profile if none active
    first_profile = next(iter(profiles.keys()), "default")
    first_config = profiles.get(
        first_profile, {"always_fetch": {}, "conditional": {}}
    )
    return {
        "name": first_profile,
        "project_type": project_type,
        "config": first_config,
        "directories": {
            "instructions": f".github/{first_profile}/instructions",
            "chatmodes": f".github/{first_profile}/chatmodes",
            "prompts": f".github/{first_profile}/prompts"
        }
    }


def get_all_profiles_for_project(
    config: Dict[str, Any], project_type: str
) -> List[str]:
    """Get all available profiles for a project type"""
    project_configs = config.get("project_types", {})
    if project_type not in project_configs:
        return ["default"]
    
    return list(project_configs[project_type].keys())


def get_profile_filename(
    base_filename: str, profile_name: str, context_type: str
) -> str:
    """Generate profile-specific filename"""
    if base_filename.endswith((".md", ".txt")):
        base_filename = base_filename.rsplit(".", 1)[0]
    
    return f"{base_filename}.{context_type}.md"


@mcp.tool()
async def get_workspace_context(
    workspace_path: Optional[str] = None,
    include_git_info: bool = True,
    include_file_analysis: bool = True
) -> str:
    """
    Get comprehensive context about the current workspace for input to
    other tools.
    
    This tool gathers workspace information that can be used as input for
    other context fetching operations.
    
    Args:
        workspace_path: Path to workspace (defaults to current directory)
        include_git_info: Whether to include git repository information
        include_file_analysis: Whether to analyze project files
    
    Returns:
        JSON with workspace context that can be used as input for other tools
    """
    try:
        if workspace_path is None:
            workspace_path = "."
        
        workspace_dir = Path(workspace_path)
        
        context = {
            "workspace_path": str(workspace_dir.absolute()),
            "project_types": detect_project_type(workspace_dir),
            "detected_conditions": detect_frameworks_and_libraries(
                workspace_dir)
        }
        
        if include_git_info:
            context["git_info"] = analyze_git_repository(workspace_dir)
        
        if include_file_analysis:
            # Analyze key files for additional context
            key_files = {}
            files_to_check = [
                "package.json", "requirements.txt", "pyproject.toml",
                "Cargo.toml", "go.mod", "tsconfig.json"
            ]
            
            for filename in files_to_check:
                file_path = workspace_dir / filename
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            key_files[filename] = {
                                "exists": True,
                                "size": len(content),
                                "lines": len(content.split('\n'))
                            }
                    except Exception:
                        key_files[filename] = {
                            "exists": True,
                            "error": "Could not read file"
                        }
            
            context["key_files"] = key_files
        
        # Provide suggested actions based on context
        suggestions = []
        for project_type in context["project_types"]:
            suggestions.append(f"Fetch context for {project_type} project")
        
        if context["detected_conditions"].get("has_react"):
            suggestions.append("Consider fetching React-specific docs")
        
        if context["detected_conditions"].get("has_django"):
            suggestions.append("Consider fetching Django-specific docs")
        
        context["suggested_actions"] = suggestions
        
        return json.dumps(context, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting workspace context: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def fetch_and_setup_copilot_files(
    workspace_dir: Optional[str] = None,
    instructions_urls: Optional[List[str]] = None,
    chatmodes_urls: Optional[List[str]] = None,
    prompts_urls: Optional[List[str]] = None,
    auto_detect: bool = True
) -> str:
    """
    Fetch remote instructions, chat modes, and prompts, save them to
    appropriate directories, and update VS Code settings.
    
    Args:
        workspace_dir: Optional workspace path. Uses WORKDIR if None.
        instructions_urls: URLs to fetch instruction files from
        chatmodes_urls: URLs to fetch chat mode files from
        prompts_urls: URLs to fetch prompt files from
        auto_detect: Whether to auto-detect project type and fetch accordingly
        
    Returns:
        JSON response indicating success or failure
    """
    try:
        if workspace_dir is None:
            workspace_path = WORKDIR.absolute()
        else:
            workspace_path = Path(workspace_dir).absolute()
        
        # Verify this is a git repository
        try:
            repo = git.Repo(workspace_path, search_parent_directories=True)
            repo_root = Path(repo.working_tree_dir)
        except git.InvalidGitRepositoryError:
            return json.dumps({
                "success": False,
                "error": "Not a git repository. Context requires git."
            })
        
        # Create directories
        vscode_dir = repo_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        results = {
            "instructions": [],
            "chatmodes": [],
            "prompts": [],
            "failed_urls": [],
            "project_info": {}
        }
        
        # Auto-detect project characteristics if enabled
        if auto_detect:
            project_types = detect_project_type(workspace_path)
            conditions = detect_frameworks_and_libraries(workspace_path)
            results["project_info"] = {
                "project_types": project_types,
                "conditions": conditions
            }
            
            # Get URLs from configuration based on project type and
            # active profile
            config = load_context_config()
            
            # Use the first detected project type for profile selection
            primary_project_type = (
                project_types[0] if project_types else "generic"
            )
            active_profile = get_active_profile(config, primary_project_type)
            
            if not instructions_urls:
                instructions_urls = get_context_urls_for_project(
                    project_types, conditions, "instructions", config
                )
            
            if not chatmodes_urls:
                chatmodes_urls = get_context_urls_for_project(
                    project_types, conditions, "chatmodes", config
                )
            
            if not prompts_urls:
                prompts_urls = get_context_urls_for_project(
                    project_types, conditions, "prompts", config
                )
        else:
            # If not auto-detecting, use default profile
            config = load_context_config()
            active_profile = {
                "name": "default",
                "project_type": "generic",
                "directories": {
                    "instructions": ".github/default/instructions",
                    "chatmodes": ".github/default/chatmodes",
                    "prompts": ".github/default/prompts"
                }
            }
        
        # Use profile-specific directories
        profile_directories = active_profile["directories"]
        instructions_dir = repo_root / profile_directories["instructions"]
        chatmodes_dir = repo_root / profile_directories["chatmodes"]
        prompts_dir = repo_root / profile_directories["prompts"]
        
        # Ensure directories exist
        instructions_dir.mkdir(parents=True, exist_ok=True)
        chatmodes_dir.mkdir(parents=True, exist_ok=True)
        prompts_dir.mkdir(parents=True, exist_ok=True)
 
        # Fetch and save instructions
        for url in instructions_urls:
            file_path = await fetch_remote_content(
                url, instructions_dir, "instructions", active_profile["name"]
            )
            if file_path:
                results["instructions"].append(file_path)
            else:
                results["failed_urls"].append(url)
        
        # Fetch and save chat modes
        for url in chatmodes_urls:
            file_path = await fetch_remote_content(
                url, chatmodes_dir, "chatmodes", active_profile["name"]
            )
            if file_path:
                results["chatmodes"].append(file_path)
            else:
                results["failed_urls"].append(url)
        
        # Fetch and save prompts
        for url in prompts_urls:
            file_path = await fetch_remote_content(
                url, prompts_dir, "prompts", active_profile["name"]
            )
            if file_path:
                results["prompts"].append(file_path)
            else:
                results["failed_urls"].append(url)
        
        # Update VS Code settings with all available profiles as options
        settings_file = vscode_dir / "settings.json"
        settings = {}
        if settings_file.exists():
            async with aiofiles.open(settings_file, 'r') as f:
                content = await f.read()
                if content.strip():
                    settings = json.loads(content)
        
        # Collect all available profile directories for all project types
        all_profile_dirs = {
            "instructions": {},
            "chatmodes": {},
            "prompts": {}
        }
        
        project_configs = config.get("project_types", {})
        for project_type, profiles in project_configs.items():
            for profile_name in profiles.keys():
                for context_type in ["instructions", "chatmodes", "prompts"]:
                    profile_dir = f".github/{profile_name}/{context_type}"
                    all_profile_dirs[context_type][profile_dir] = True
        
        # Always include the current active profile directories
        for context_type in ["instructions", "chatmodes", "prompts"]:
            current_dir = profile_directories[context_type]
            all_profile_dirs[context_type][current_dir] = True
        
        # Define the settings to add/update with all profiles as options
        new_settings = {
            "chat.promptFilesLocations": all_profile_dirs["prompts"],
            "chat.modeFilesLocations": all_profile_dirs["chatmodes"],
            "chat.instructionsFilesLocations": all_profile_dirs["instructions"]
        }
        
        # Update settings
        settings.update(new_settings)
        
        # Write updated settings
        async with aiofiles.open(settings_file, 'w') as f:
            await f.write(json.dumps(settings, indent=4))
        
        return json.dumps({
            "success": True,
            "message": "Successfully fetched and configured Copilot files",
            "results": results,
            "settings_updated": True
        })
        
    except Exception as e:
        logger.error(f"Error fetching and setting up Copilot files: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
async def list_context_config() -> str:
    """
    List the current context configuration showing all project types
    and their URLs.

    Returns:
        JSON string with the complete context configuration
    """
    try:
        config = load_context_config()
        return json.dumps(config, indent=2)
    except Exception as e:
        logger.error(f"Error listing context config: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def set_active_profile(project_type: str, profile_name: str) -> str:
    """
    Set the active profile for a specific project type.
    
    Args:
        project_type: The project type (python, javascript, etc.)
        profile_name: Name of the profile to activate
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        config = load_context_config()
        
        # Check if project type exists
        project_configs = config.get("project_types", {})
        if project_type not in project_configs:
            return json.dumps({
                "success": False,
                "error": (f"Project type '{project_type}' not found in "
                          f"configuration")
            })
        
        # Check if profile exists for this project type
        profiles = project_configs[project_type]
        if profile_name not in profiles:
            available_profiles = list(profiles.keys())
            return json.dumps({
                "success": False,
                "error": (f"Profile '{profile_name}' not found for project "
                          f"type '{project_type}'. Available profiles: "
                          f"{available_profiles}")
            })
        
        # Deactivate all profiles for this project type
        for name, profile_config in profiles.items():
            profile_config["active"] = False
        
        # Activate the requested profile
        profiles[profile_name]["active"] = True
        
        # Save updated configuration
        save_context_config(config)
        
        # Get profile info for response
        active_profile = get_active_profile(config, project_type)
        
        # Update VS Code settings with all available profiles as options
        try:
            # Find the git repository root
            current_path = Path(WORKDIR).absolute()
            try:
                repo = git.Repo(current_path, search_parent_directories=True)
                repo_root = Path(repo.working_tree_dir)
            except git.InvalidGitRepositoryError:
                # If not in a git repo, use current directory
                repo_root = current_path
            
            vscode_dir = repo_root / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            settings_file = vscode_dir / "settings.json"
            
            # Load existing settings
            settings = {}
            if settings_file.exists():
                async with aiofiles.open(settings_file, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        settings = json.loads(content)
            
            # Collect all available profile directories for all project types
            all_profile_dirs = {
                "instructions": {},
                "chatmodes": {},
                "prompts": {}
            }
            
            for proj_type, proj_profiles in project_configs.items():
                for prof_name in proj_profiles.keys():
                    for context_type in ["instructions", "chatmodes",
                                         "prompts"]:
                        profile_dir = f".github/{prof_name}/{context_type}"
                        # Include all profiles as options, but only set
                        # active ones to true
                        profile_is_active = proj_profiles[prof_name].get(
                            "active", False
                        )
                        all_profile_dirs[context_type][profile_dir] = (
                            profile_is_active
                        )
            
            # Define the settings to add/update with all profiles as options
            new_settings = {
                "chat.promptFilesLocations": all_profile_dirs["prompts"],
                "chat.modeFilesLocations": all_profile_dirs["chatmodes"],
                "chat.instructionsFilesLocations": (
                    all_profile_dirs["instructions"]
                )
            }
            
            # Update settings
            settings.update(new_settings)
            
            # Write updated settings
            async with aiofiles.open(settings_file, 'w') as f:
                await f.write(json.dumps(settings, indent=4))
            
        except Exception as settings_error:
            logger.warning(
                f"Failed to update VS Code settings: {settings_error}"
            )
        
        return json.dumps({
            "success": True,
            "message": (f"Profile '{profile_name}' activated for project "
                        f"type '{project_type}'"),
            "active_profile": {
                "name": active_profile["name"],
                "project_type": active_profile["project_type"],
                "directories": active_profile["directories"]
            },
            "settings_updated": True
        })
        
    except Exception as e:
        logger.error(f"Error setting active profile: {e}")
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_available_profiles(project_type: str) -> str:
    """
    Get all available profiles for a specific project type.
    
    Args:
        project_type: The project type (python, javascript, etc.)
    
    Returns:
        JSON response with available profiles and their configurations
    """
    try:
        config = load_context_config()
        project_configs = config.get("project_types", {})
        
        if project_type not in project_configs:
            return json.dumps({
                "success": False,
                "error": f"Project type '{project_type}' not found"
            })
        
        profiles = project_configs[project_type]
        profile_info = {}
        
        for profile_name, profile_config in profiles.items():
            profile_info[profile_name] = {
                "active": profile_config.get("active", False),
                "directories": {
                    "instructions": f".github/{profile_name}/instructions",
                    "chatmodes": f".github/{profile_name}/chatmodes",
                    "prompts": f".github/{profile_name}/prompts"
                },
                "has_always_fetch": bool(profile_config.get("always_fetch")),
                "has_conditional": bool(profile_config.get("conditional"))
            }
        
        return json.dumps({
            "success": True,
            "project_type": project_type,
            "profiles": profile_info
        })
        
    except Exception as e:
        logger.error(f"Error getting available profiles: {e}")
        return json.dumps({"error": str(e)})


def main():
    """Main function to run the Remote Context MCP server"""
    logger.info("Starting Remote Context MCP server...")
    logger.info(f"Config file: {CONFIG_FILE}")
    logger.info(f"Working directory: {WORKDIR}")
    
    # Create default config if it doesn't exist (only for local files)
    if not CONFIG_FILE.startswith(('http://', 'https://')):
        config_path = Path(CONFIG_FILE)
        if not config_path.exists():
            save_context_config(DEFAULT_CONTEXTS)
            logger.info("Created default context configuration")
    
    mcp.run()
    logger.info("Remote Context MCP server completed")


if __name__ == "__main__":
    main()
