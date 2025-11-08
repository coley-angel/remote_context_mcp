#!/usr/bin/env python3
"""
Test IDE detection to help debug environment variable issues
"""
import os
import sys

print("=" * 80)
print("IDE Detection Test")
print("=" * 80)

# Check all relevant environment variables
env_vars_to_check = [
    'VSCODE_PID', 'VSCODE_CWD', 'VSCODE_IPC_HOOK', 'VSCODE_NLS_CONFIG',
    'CURSOR_PID', 'CURSOR_USER_DATA_DIR',
    'WINDSURF_PID', 'CODEIUM_PID', 'CODEIUM_API_KEY',
    'TERM_PROGRAM', 'TERM_PROGRAM_VERSION',
    'PWD', 'HOME'
]

print("\nEnvironment Variables:")
print("-" * 80)
found_any = False
for var in env_vars_to_check:
    value = os.getenv(var)
    if value:
        found_any = True
        # Truncate long values
        display_value = value[:60] + '...' if len(value) > 60 else value
        print(f"  {var:25} = {display_value}")

if not found_any:
    print("  No IDE-related environment variables found")

print("\nDetected IDE:")
print("-" * 80)

# Detect IDE
if os.getenv("CODEIUM_PID") or os.getenv("WINDSURF_PID"):
    print("  ✓ WINDSURF (via CODEIUM_PID/WINDSURF_PID)")
elif os.getenv("TERM_PROGRAM") and "windsurf" in os.getenv("TERM_PROGRAM").lower():
    print(f"  ✓ WINDSURF (via TERM_PROGRAM={os.getenv('TERM_PROGRAM')})")
elif os.getenv("CURSOR_PID") or os.getenv("CURSOR_USER_DATA_DIR"):
    print("  ✓ CURSOR")
elif os.getenv("VSCODE_PID") or os.getenv("VSCODE_CWD") or os.getenv("VSCODE_IPC_HOOK"):
    print("  ✓ VSCODE")
else:
    print("  ✗ Could not detect IDE from environment variables")
    print("\n  If you're running in Windsurf, you can manually set the IDE:")
    print("    Use MCP tool: ide(action='set', ide_name='windsurf')")

print("\nCurrent Working Directory:")
print("-" * 80)
print(f"  {os.getcwd()}")

print("\nRecommendations:")
print("-" * 80)
if not os.getenv("CODEIUM_PID") and not os.getenv("WINDSURF_PID"):
    print("  ⚠️  Windsurf environment variables not detected")
    print("  → Run this script from within Windsurf's terminal")
    print("  → Or manually set IDE: ide(action='set', ide_name='windsurf')")
else:
    print("  ✓ Windsurf should be properly detected")

print("=" * 80)
