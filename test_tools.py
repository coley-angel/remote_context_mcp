#!/usr/bin/env python3
"""
Test all MCP tools locally
"""

import asyncio
import json
import sys
from pathlib import Path

# Import main module
sys.path.insert(0, str(Path(__file__).parent))
import main

async def test_tool(name: str, coro):
    """Test a tool and print results"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    try:
        result = await coro
        result_dict = json.loads(result)
        print(f"✅ SUCCESS")
        print(f"Result: {json.dumps(result_dict, indent=2)[:500]}...")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def main_test():
    """Run all tool tests"""
    print("\n" + "="*70)
    print("MCP TOOLS TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Test 1: list_ide_configs
    results['list_ide_configs'] = await test_tool(
        "list_ide_configs()",
        main.list_ide_configs()
    )
    
    # Test 2: list_profiles
    results['list_profiles'] = await test_tool(
        "list_profiles()",
        main.list_profiles()
    )
    
    # Test 3: get_config
    results['get_config'] = await test_tool(
        "get_config()",
        main.get_config()
    )
    
    # Test 4: reload_config
    results['reload_config'] = await test_tool(
        "reload_config()",
        main.reload_config()
    )
    
    # Test 5: diagnose_config
    results['diagnose_config'] = await test_tool(
        "diagnose_config()",
        main.diagnose_config()
    )
    
    # Test 6: sync(action="list_ides")
    results['sync_list_ides'] = await test_tool(
        "sync(action='list_ides')",
        main.sync(action="list_ides")
    )
    
    # Test 7: profile(action="list")
    results['profile_list'] = await test_tool(
        "profile(action='list')",
        main.profile(action="list")
    )
    
    # Test 8: profile(action="show")
    results['profile_show'] = await test_tool(
        "profile(action='show')",
        main.profile(action="show")
    )
    
    # Test 9: validate_content_security
    results['validate_content_security'] = await test_tool(
        "validate_content_security('test content')",
        main.validate_content_security("test content", "rule")
    )
    
    # Test 10: clear_cache
    results['clear_cache'] = await test_tool(
        "clear_cache()",
        main.clear_cache("all")
    )
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main_test())
    sys.exit(0 if success else 1)
