#!/usr/bin/env python
"""Test MCP tool registration"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import mcp

async def test_tools():
    """Test that MCP tools are registered"""
    print("\n" + "="*60)
    print("  MCP TOOLS REGISTRATION TEST")
    print("="*60 + "\n")
    
    # Get list of registered tools
    tools = await mcp.list_tools()
    
    if not tools:
        print("❌ ERROR: No tools registered!")
        return False
    
    print(f"✅ Found {len(tools)} registered tools:\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        if tool.description:
            # Print first 80 chars of description
            desc = tool.description.strip().split('\n')[0]
            if len(desc) > 80:
                desc = desc[:77] + "..."
            print(f"   {desc}")
        print()
    
    expected_tools = [
        "sync_team_config",
        "list_profiles",
        "set_active_profile",
        "check_for_updates",
        "validate_content_security",
        "update_mcp_servers",
        "list_installed_ides",
        "get_current_ide_info",
        "set_ide",
        "get_config",
        "reload_config",
        "clear_cache"
    ]
    
    tool_names = [t.name for t in tools]
    missing = [t for t in expected_tools if t not in tool_names]
    
    if missing:
        print(f"⚠️  Missing expected tools: {missing}")
    else:
        print("✅ All expected tools are registered!")
    
    return len(tools) > 0

if __name__ == "__main__":
    success = asyncio.run(test_tools())
    sys.exit(0 if success else 1)
