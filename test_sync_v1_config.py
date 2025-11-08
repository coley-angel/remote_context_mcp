#!/usr/bin/env python3
"""
Test sync tool with V1 config that has actual content from Ops_Stack_Dev_Profiles
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Set environment to use the V1 config with real content
os.environ["TEAM_CONFIG_FILE"] = "/Users/coangel/Documents/Ops_Stack_Development/Ops_Stack_Dev_Profiles/team_config.yaml"

# Import main module
sys.path.insert(0, str(Path(__file__).parent))
import main

async def test_sync_with_v1_config():
    """Test sync with V1 config that has actual content sources"""
    print("\n" + "="*70)
    print("TESTING SYNC WITH V1 CONFIG (Real Content)")
    print("="*70)
    
    workspace_path = "/Users/coangel/Documents/Ops_Stack_Development/Ops_Stack_Dev_Profiles"
    
    print(f"\nConfig: team_config.yaml (V1 with real rules/workflows)")
    print(f"Parameters:")
    print(f"  action: full")
    print(f"  workspace_path: {workspace_path}")
    print(f"  ide_choice: 1 (Windsurf)")
    print(f"  force_update: true")
    
    try:
        result = await main.sync(
            action="full",
            workspace_path=workspace_path,
            ide_choice=1,
            force_update=True
        )
        
        result_dict = json.loads(result)
        
        if result_dict.get("success"):
            print(f"\n✅ SYNC SUCCESS")
            print(f"\n{result_dict.get('message')}")
            
            synced_files = result_dict.get("synced_files", {})
            total = sum(len(files) for files in synced_files.values())
            
            print(f"\nTotal files synced: {total}")
            print(f"\nFiles by type:")
            for content_type, files in synced_files.items():
                if files:
                    print(f"\n  {content_type.upper()}: {len(files)} files")
                    for file in files:
                        print(f"    ✓ {file}")
            
            return True
        else:
            print(f"\n❌ SYNC FAILED")
            print(f"\nError: {result_dict.get('error')}")
            if 'traceback' in result_dict:
                print(f"\nTraceback:\n{result_dict['traceback']}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sync_with_v1_config())
    sys.exit(0 if success else 1)
