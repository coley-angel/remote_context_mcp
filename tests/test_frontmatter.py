"""
Test frontmatter utilities
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontmatter_utils import (
    parseFrontmatter,
    validateFrontmatter,
    addFrontmatterToContent,
    RuleFrontmatter,
    extractRuleMetadata
)


def testParseFrontmatter():
    """Test parsing frontmatter from content"""
    print("Testing frontmatter parsing...")
    
    # Test with valid frontmatter
    content1 = """---
trigger: always_on
---

# My Rule
This is content
"""
    frontmatter, body = parseFrontmatter(content1)
    assert frontmatter is not None
    assert frontmatter["trigger"] == "always_on"
    assert "# My Rule" in body
    print("✓ Valid frontmatter parsed correctly")
    
    # Test without frontmatter
    content2 = "# My Rule\nNo frontmatter here"
    frontmatter, body = parseFrontmatter(content2)
    assert frontmatter is None
    assert body == content2
    print("✓ Content without frontmatter handled correctly")
    
    # Test with frontmatter with multiple fields
    content3 = """---
trigger: manual
glob: *.py
description: Python files only
---

Content here
"""
    frontmatter, body = parseFrontmatter(content3)
    assert frontmatter["trigger"] == "manual"
    assert frontmatter["glob"] == "*.py"
    assert frontmatter["description"] == "Python files only"
    print("✓ Multiple frontmatter fields parsed correctly")


def testValidateFrontmatter():
    """Test frontmatter validation"""
    print("\nTesting frontmatter validation...")
    
    # Valid frontmatter
    valid = {"trigger": "always_on"}
    isValid, error = validateFrontmatter(valid)
    assert isValid
    assert error is None
    print("✓ Valid frontmatter accepted")
    
    # Missing trigger
    invalid1 = {"description": "test"}
    isValid, error = validateFrontmatter(invalid1)
    assert not isValid
    assert "trigger" in error
    print("✓ Missing trigger detected")
    
    # Invalid trigger value
    invalid2 = {"trigger": "invalid_value"}
    isValid, error = validateFrontmatter(invalid2)
    assert not isValid
    assert "Invalid trigger" in error
    print("✓ Invalid trigger value detected")
    
    # None frontmatter
    isValid, error = validateFrontmatter(None)
    assert not isValid
    assert "Missing frontmatter" in error
    print("✓ Missing frontmatter detected")


def testAddFrontmatter():
    """Test adding frontmatter to content"""
    print("\nTesting adding frontmatter...")
    
    # Content without frontmatter
    content1 = "# My Rule\nSome content"
    result = addFrontmatterToContent(content1)
    assert "---" in result
    assert "trigger: always_on" in result
    assert "# My Rule" in result
    print("✓ Frontmatter added to content without frontmatter")
    
    # Content with valid frontmatter - should remain unchanged
    content2 = """---
trigger: manual
---

# My Rule
"""
    result = addFrontmatterToContent(content2)
    assert result == content2
    print("✓ Valid frontmatter left unchanged")
    
    # Content with invalid frontmatter - should be replaced
    content3 = """---
invalid: field
---

# My Rule
"""
    result = addFrontmatterToContent(content3)
    assert "trigger: always_on" in result
    assert "invalid: field" not in result
    assert "# My Rule" in result
    print("✓ Invalid frontmatter replaced with default")
    
    # Custom frontmatter
    customFrontmatter = RuleFrontmatter(
        trigger="manual",
        glob="*.js",
        description="JavaScript files"
    )
    content4 = "# JS Rule"
    result = addFrontmatterToContent(content4, customFrontmatter)
    assert "trigger: manual" in result
    assert "glob: *.js" in result
    assert "description: JavaScript files" in result
    print("✓ Custom frontmatter applied correctly")


def testExtractMetadata():
    """Test extracting metadata from content"""
    print("\nTesting metadata extraction...")
    
    content = """---
trigger: always_on
glob: *.py
---

# Rule content
"""
    metadata = extractRuleMetadata(content)
    assert metadata["hasFrontmatter"] is True
    assert metadata["isValid"] is True
    assert metadata["trigger"] == "always_on"
    assert metadata["glob"] == "*.py"
    print("✓ Metadata extracted correctly")
    
    contentNoFrontmatter = "# Rule without frontmatter"
    metadata = extractRuleMetadata(contentNoFrontmatter)
    assert metadata["hasFrontmatter"] is False
    assert metadata["isValid"] is False
    assert metadata["trigger"] is None
    print("✓ Metadata for content without frontmatter extracted correctly")


if __name__ == "__main__":
    print("Running frontmatter utility tests...\n")
    print("=" * 50)
    
    try:
        testParseFrontmatter()
        testValidateFrontmatter()
        testAddFrontmatter()
        testExtractMetadata()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except AssertionError as e:
        print("\n" + "=" * 50)
        print(f"❌ Test failed: {e}")
        raise
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ Error running tests: {e}")
        raise
