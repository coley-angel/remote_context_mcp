"""
Consolidated MCP Tools
Cleaner, more maintainable interface with action-based parameters
"""
import json
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


async def profile(
    action: str = "list",
    profile_name: Optional[str] = None,
    auto_sync: bool = True,
    config=None,
    ide_manager=None,
    workspace_dir=None,
    content_dir=None
) -> str:
    """
    Profile management - all profile operations in one tool
    
    Actions:
        list - List all available profiles
        activate - Set active profile
        show - Show detailed profile configuration
        cleanup - Remove profile rules from IDEs
    
    Args:
        action: Operation to perform (list, activate, show, cleanup)
        profile_name: Profile name (required for activate/cleanup, optional for show)
        auto_sync: Auto-sync after activation (default: True)
    
    Returns:
        JSON response with operation results
    """
    from main import (
        list_profiles as _list_profiles,
        set_active_profile as _set_active_profile,
        get_config as _get_config,
        cleanup_profile_rules as _cleanup_profile_rules
    )
    
    if action == "list":
        return await _list_profiles()
    
    elif action == "activate":
        if not profile_name:
            return json.dumps({
                "success": False,
                "error": "profile_name required for 'activate' action"
            })
        return await _set_active_profile(profile_name, auto_sync)
    
    elif action == "show":
        return await _get_config()
    
    elif action == "cleanup":
        return await _cleanup_profile_rules(profile_name)
    
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["list", "activate", "show", "cleanup"]
        })


async def sync(
    action: str = "full",
    profile_name: Optional[str] = None,
    force_update: bool = False,
    sync_to_ides: bool = True
) -> str:
    """
    Synchronization operations - sync, check, reload
    
    Actions:
        full - Full sync from remote (default)
        check - Check for updates without syncing
        reload - Reload configuration from source
    
    Args:
        action: Operation to perform (full, check, reload)
        profile_name: Profile to sync (uses active if None)
        force_update: Force update even if recently synced
        sync_to_ides: Sync to IDE directories
    
    Returns:
        JSON response with sync results
    """
    from main import (
        sync_team_config as _sync_team_config,
        check_for_updates as _check_for_updates,
        reload_config as _reload_config
    )
    
    if action == "full":
        return await _sync_team_config(profile_name, force_update, sync_to_ides)
    
    elif action == "check":
        return await _check_for_updates()
    
    elif action == "reload":
        return await _reload_config()
    
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["full", "check", "reload"]
        })


async def mcp_servers(
    action: str = "update",
    profile_name: Optional[str] = None,
    reload: bool = True
) -> str:
    """
    MCP server management - update and list servers
    
    Actions:
        update - Update MCP server configurations
        list - List configured MCP servers
    
    Args:
        action: Operation to perform (update, list)
        profile_name: Profile to use (uses active if None)
        reload: Reload IDE after update
    
    Returns:
        JSON response with results
    """
    from main import update_mcp_servers as _update_mcp_servers, load_team_config
    
    if action == "update":
        return await _update_mcp_servers(profile_name, reload)
    
    elif action == "list":
        # List configured MCP servers from profile
        try:
            config = load_team_config()
            
            if profile_name:
                if profile_name not in config.profiles:
                    return json.dumps({
                        "success": False,
                        "error": f"Profile '{profile_name}' not found"
                    })
                profile = config.profiles[profile_name]
            else:
                # Get active profile
                active_profiles = [p for p in config.profiles.values() if p.active]
                if not active_profiles:
                    return json.dumps({
                        "success": False,
                        "error": "No active profile found"
                    })
                profile = active_profiles[0]
            
            servers_info = []
            for server in profile.mcp_servers:
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
                "profile": profile.name,
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
            "available_actions": ["update", "list"]
        })


async def ide(
    action: str = "info",
    ide_name: Optional[str] = None
) -> str:
    """
    IDE management - detect, list, and set IDE
    
    Actions:
        info - Get current IDE information
        list - List all installed IDEs
        set - Set IDE explicitly
    
    Args:
        action: Operation to perform (info, list, set)
        ide_name: IDE name for 'set' action (vscode, cursor, windsurf)
    
    Returns:
        JSON response with IDE information
    """
    from main import (
        get_current_ide_info as _get_current_ide_info,
        list_installed_ides as _list_installed_ides,
        set_ide as _set_ide
    )
    
    if action == "info":
        return await _get_current_ide_info()
    
    elif action == "list":
        return await _list_installed_ides()
    
    elif action == "set":
        if not ide_name:
            return json.dumps({
                "success": False,
                "error": "ide_name required for 'set' action",
                "available_ides": ["vscode", "cursor", "windsurf"]
            })
        return await _set_ide(ide_name)
    
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["info", "list", "set"]
        })


async def validate(
    content: str,
    content_type: str = "general",
    filename: str = "unknown"
) -> str:
    """
    Validate content for security issues
    
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
        JSON response with validation results
    """
    from main import validate_content_security as _validate_content_security
    return await _validate_content_security(content, content_type, filename)


async def cache(
    action: str = "clear",
    cache_type: str = "all"
) -> str:
    """
    Cache management - clear or show cache information
    
    Actions:
        clear - Clear cached data
        info - Show cache information
    
    Args:
        action: Operation to perform (clear, info)
        cache_type: Type of cache (all, repos, content)
    
    Returns:
        JSON response with results
    """
    from main import clear_cache as _clear_cache, CACHE_DIR, CONTENT_DIR
    from pathlib import Path
    
    if action == "clear":
        return await _clear_cache(cache_type)
    
    elif action == "info":
        # Show cache information
        try:
            cache_info = {}
            
            if cache_type in ["all", "repos"]:
                repos_dir = CACHE_DIR / "repos"
                if repos_dir.exists():
                    repo_count = len(list(repos_dir.iterdir()))
                    cache_info["repos"] = {
                        "count": repo_count,
                        "path": str(repos_dir)
                    }
            
            if cache_type in ["all", "content"]:
                if CONTENT_DIR.exists():
                    content_count = len(list(CONTENT_DIR.rglob("*")))
                    cache_info["content"] = {
                        "count": content_count,
                        "path": str(CONTENT_DIR)
                    }
            
            return json.dumps({
                "success": True,
                "cache_info": cache_info
            }, indent=2)
        
        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown action: {action}",
            "available_actions": ["clear", "info"]
        })
