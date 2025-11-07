#!/usr/bin/env python3
"""
Test script to validate team_config.yaml parsing
"""
import sys
from pathlib import Path

# Add the module to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import ConfigLoader

def test_config_file(config_path: str):
    """Test loading and parsing a config file"""
    print(f"\n{'='*80}")
    print(f"Testing config file: {config_path}")
    print('='*80)
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"❌ File not found: {config_path}")
        return False
    
    print(f"✓ File exists ({config_file.stat().st_size} bytes)")
    
    # Try to load config
    print("\nParsing configuration...")
    config = ConfigLoader.load_from_file(config_file)
    
    if not config:
        print("❌ Failed to parse config file")
        return False
    
    print("✓ Configuration parsed successfully")
    print(f"\nConfiguration Summary:")
    print(f"  Team Name: {config.team_name}")
    print(f"  Version: {config.version}")
    print(f"  Central Repo: {config.central_repo_url}")
    print(f"  Profiles: {len(config.profiles)}")
    
    for profile_name, profile in config.profiles.items():
        print(f"\n  Profile: {profile_name}")
        print(f"    Active: {profile.active}")
        print(f"    Description: {profile.description}")
        print(f"    Rules: {len(profile.rules)} sources")
        print(f"    Workflows: {len(profile.workflows)} sources")
        print(f"    MCP Servers: {len(profile.mcp_servers)}")
        
        if profile.mcp_servers:
            print(f"\n    MCP Servers Details:")
            for server in profile.mcp_servers:
                print(f"      - {server.name}")
                print(f"        Command: {server.command or 'N/A'}")
                print(f"        Type: {server.type or 'standard'}")
                print(f"        URL: {server.url or 'N/A'}")
                print(f"        Enabled: {server.enabled}")
                if server.env:
                    print(f"        Env vars: {', '.join(server.env.keys())}")
    
    print(f"\n{'='*80}")
    print("✓ All tests passed!")
    print('='*80)
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        # Default to the user's config file
        config_path = "/Users/coangel/Documents/Ops_Stack_Development/Ops_Stack_Dev_Profiles/team_config.yaml"
    
    success = test_config_file(config_path)
    sys.exit(0 if success else 1)
