#!/usr/bin/env python3
"""
Test sync tool with actual parameters from user
"""

import asyncio
import json
import sys
from pathlib import Path

# Import main module
sys.path.insert(0, str(Path(__file__).parent))
import main

async def test_sync():
    """Test sync with user's actual parameters"""
    print("\n" + "="*70)
    print("TESTING SYNC WITH USER PARAMETERS")
    print("="*70)
    
    workspace_path = "/Users/coangel/Documents/Ops_Stack_Development/Ops_Stack_Dev_Profiles"
    
    print(f"\nParameters:")
    print(f"  action: full")
    print(f"  workspace_path: {workspace_path}")
    print(f"  ide_choice: 1")
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
            print(f"\nResult:")
            print(json.dumps(result_dict, indent=2))
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
    success = asyncio.run(test_sync())
    sys.exit(0 if success else 1)
