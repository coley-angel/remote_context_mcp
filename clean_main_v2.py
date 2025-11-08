#!/usr/bin/env python3
"""
Clean main.py by removing V1-only functions
"""

# Functions to remove (V1 only, obsolete in V2)
FUNCTIONS_TO_REMOVE = [
    "get_ide_manager",
    "detect_current_ide",
    "get_current_ide",
    "set_current_ide",
    "detect_workspace_root",
    "get_workspace_dir",
    "get_ide_content_dir",
    "sync_team_config",  # OLD version, not V2 version
    "cleanup_profile_rules",
    "deactivate_profile",
    "update_mcp_servers",
    "list_installed_ides",
    "get_current_ide_info",
    "set_ide",
]

# MCP tool wrappers to remove
TOOLS_TO_REMOVE = [
    "ide",  # Tool wrapper for IDE management
]

import re

def remove_function(content, func_name):
    """Remove a function definition and its body"""
    # Pattern to match function definition and its body
    # This is a simple approach - matches from 'def func_name' to next 'def' or '@mcp.tool'
    pattern = rf'(^async def {func_name}\(.*?\n(?:.*?\n)*?)(?=^(?:def |async def |@mcp\.tool|if __name__))'
    content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    # Also try sync functions
    pattern = rf'(^def {func_name}\(.*?\n(?:.*?\n)*?)(?=^(?:def |async def |@mcp\.tool|if __name__))'
    content = re.sub(pattern, '', content, flags=re.MULTILINE)
    
    return content

def main():
    with open('main.py.v1_backup', 'r') as f:
        content = f.read()
    
    original_lines = len(content.splitlines())
    
    # Remove each obsolete function
    for func in FUNCTIONS_TO_REMOVE:
        old_len = len(content)
        content = remove_function(content, func)
        removed = old_len - len(content)
        if removed > 0:
            print(f"✓ Removed {func}() - {removed} chars")
    
    for tool in TOOLS_TO_REMOVE:
        old_len = len(content)
        content = remove_function(content, tool)
        removed = old_len - len(content)
        if removed > 0:
            print(f"✓ Removed {tool}() tool - {removed} chars")
    
    final_lines = len(content.splitlines())
    print(f"\nTotal: {original_lines} -> {final_lines} lines ({original_lines - final_lines} removed)")
    
    # Write cleaned version
    with open('main_v2_cleaned.py', 'w') as f:
        f.write(content)
    
    print(f"\nCleaned version written to main_v2_cleaned.py")
    print("Review and then: mv main_v2_cleaned.py main.py")

if __name__ == "__main__":
    main()
