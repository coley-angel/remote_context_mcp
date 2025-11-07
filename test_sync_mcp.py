#!/usr/bin/env python3
"""
Test script to manually sync MCP configuration
"""
import asyncio
import json
from pathlib import Path

# Import the MCP tool function
from main import update_mcp_servers, load_team_config, get_ide_manager
from schemas import IDEType


async def test_sync():
    """Test syncing MCP servers to the global Windsurf config"""
    print("=" * 70)
    print("Testing MCP Server Sync")
    print("=" * 70)
    
    # Load current config
    config = load_team_config()
    print(f"\n📋 Team Config: {config.team_name}")
    print(f"   Profiles: {list(config.profiles.keys())}")
    
    # Find active profile
    active_profile = None
    for name, profile in config.profiles.items():
        if profile.active:
            active_profile = name
            print(f"   Active Profile: {name}")
            print(f"   MCP Servers in Profile: {len(profile.mcp_servers)}")
            for server in profile.mcp_servers:
                print(f"     - {server.name}: {'enabled' if server.enabled else 'disabled'}")
    
    if not active_profile:
        print("\n❌ No active profile found!")
        return
    
    # Check Windsurf MCP config path
    ide_manager = get_ide_manager()
    windsurf_mcp_path = ide_manager.get_mcp_config_path(IDEType.WINDSURF)
    print(f"\n📁 Windsurf MCP Config Path: {windsurf_mcp_path}")
    
    # Read current Windsurf MCP config
    if windsurf_mcp_path.exists():
        current_config = ide_manager.read_mcp_config(IDEType.WINDSURF)
        print(f"   Current servers in Windsurf: {list(current_config.get('servers', {}).keys())}")
    else:
        print("   Windsurf MCP config does not exist yet")
    
    # Call the update_mcp_servers tool
    print(f"\n🔄 Syncing MCP servers from profile '{active_profile}'...")
    result = await update_mcp_servers(profile_name=active_profile, reload=False)
    result_data = json.loads(result)
    
    print("\n✅ Sync Result:")
    print(json.dumps(result_data, indent=2))
    
    # Verify the update
    if windsurf_mcp_path.exists():
        updated_config = ide_manager.read_mcp_config(IDEType.WINDSURF)
        print(f"\n📋 Updated Windsurf MCP Servers:")
        for server_name, server_config in updated_config.get('servers', {}).items():
            print(f"   - {server_name}: {server_config.get('command')}")
    
    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)
    print(f"\n💡 Config file location: {windsurf_mcp_path}")
    print("💡 Restart Windsurf to apply changes")


if __name__ == "__main__":
    asyncio.run(test_sync())
