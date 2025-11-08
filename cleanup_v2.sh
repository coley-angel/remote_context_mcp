#!/bin/bash
# V2 Cleanup Script - Remove obsolete V1 code

set -e

echo "============================================"
echo "V2 Cleanup Script"
echo "Removes obsolete V1 code after V2 refactor"
echo "============================================"
echo ""

# Confirmation
read -p "This will delete files and functions. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cleanup cancelled."
    exit 1
fi

echo ""
echo "Phase 1: Deleting obsolete files..."
echo "-----------------------------------"

# Delete empty and obsolete files
if [ -f "main_new_tools.py" ]; then
    echo "✓ Deleting main_new_tools.py (empty file)"
    rm main_new_tools.py
fi

if [ -f "ide_adapter.py" ]; then
    echo "✓ Deleting ide_adapter.py (obsolete - IDE configs from YAML now)"
    rm ide_adapter.py
fi

if [ -f "mcp_tools.py" ]; then
    echo "✓ Deleting mcp_tools.py (obsolete - replaced by sync_with_ide_config)"
    rm mcp_tools.py
fi

if [ -f "mcp_tools_consolidated.py" ]; then
    echo "✓ Deleting mcp_tools_consolidated.py (obsolete)"
    rm mcp_tools_consolidated.py
fi

echo ""
echo "Phase 2: Listing functions to remove from main.py..."
echo "-----------------------------------------------------"
echo "The following functions in main.py are obsolete:"
echo ""
echo "  - detect_current_ide() (~60 lines)"
echo "  - get_current_ide() (~10 lines)"
echo "  - set_current_ide() (~9 lines)"
echo "  - detect_workspace_root() (~53 lines)"
echo "  - get_workspace_dir() (~15 lines)"
echo "  - get_ide_content_dir() (~44 lines)"
echo "  - get_ide_manager() (~9 lines)"
echo "  - sync_team_config() [OLD] (~145 lines)"
echo "  - cleanup_profile_rules() (~45 lines)"
echo "  - deactivate_profile() (~86 lines)"
echo "  - update_mcp_servers() (~60 lines)"
echo "  - list_installed_ides() (~44 lines)"
echo "  - get_current_ide_info() (~44 lines)"
echo "  - set_ide() (~41 lines)"
echo "  - ide() tool wrapper (~31 lines)"
echo ""
echo "  Total: ~600 lines to remove"
echo ""
echo "⚠️  Manual removal required - too risky to automate"
echo "    See docs/V2_CLEANUP_ANALYSIS.md for details"

echo ""
echo "Phase 3: Checking for unused imports..."
echo "----------------------------------------"

if grep -q "from ide_adapter import" main.py; then
    echo "⚠️  main.py imports ide_adapter (line ~217) - needs removal"
fi

if grep -q "from ide_manager import" main.py; then
    echo "⚠️  main.py imports ide_manager (line ~33) - may need review"
fi

if grep -q "from mcp_tools import" main.py; then
    echo "⚠️  main.py imports mcp_tools (line ~788) - needs removal"
fi

echo ""
echo "Phase 4: Summary"
echo "----------------"
echo "✅ Deleted obsolete files"
echo "⚠️  Manual cleanup needed in main.py"
echo "📖 See docs/V2_CLEANUP_ANALYSIS.md for full details"
echo ""
echo "Next steps:"
echo "  1. Remove obsolete functions from main.py"
echo "  2. Remove unused imports"
echo "  3. Test with: python -m pytest tests/"
echo "  4. Commit changes"
echo ""
echo "Estimated code reduction: ~2,000 lines (87%)"
