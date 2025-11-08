"""
Frontmatter Utilities

Handles frontmatter parsing, validation, and generation for rule files.
Rules must have frontmatter with trigger configuration.
Supports MDC (Markdown with Configuration) format for Cursor rules.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple
from schemas import FrontmatterConfig

logger = logging.getLogger(__name__)


def frontmatter_to_yaml(config: FrontmatterConfig) -> str:
    """
    Convert FrontmatterConfig to YAML format for MDC files
    
    Args:
        config: FrontmatterConfig object with default values
    
    Returns:
        YAML formatted string
    """
    lines = []
    
    # Required fields
    lines.append(f"trigger: {config.trigger}")
    
    # Optional fields
    if config.glob:
        lines.append(f"glob: {config.glob}")
    if config.description:
        lines.append(f"description: {config.description}")
    if config.priority:
        lines.append(f"priority: {config.priority}")
    if config.tags:
        # Format tags as YAML array
        tags_str = "[" + ", ".join(config.tags) + "]"
        lines.append(f"tags: {tags_str}")
    if config.author:
        lines.append(f"author: {config.author}")
    if config.version:
        lines.append(f"version: {config.version}")
    
    return "\n".join(lines)


def parseFrontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Parse YAML frontmatter from content
    
    Args:
        content: File content with optional frontmatter
    
    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter)
    """
    # Match frontmatter pattern: ---\ndata\n---
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return None, content
    
    frontmatterText = match.group(1)
    contentWithoutFrontmatter = content[match.end():]
    
    # Parse simple YAML (key: value pairs)
    frontmatter = {}
    for line in frontmatterText.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            frontmatter[key] = value
    
    return frontmatter, contentWithoutFrontmatter


def validateFrontmatter(frontmatter: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Validate frontmatter for rules
    
    Args:
        frontmatter: Parsed frontmatter dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not frontmatter:
        return False, "Missing frontmatter"
    
    if "trigger" not in frontmatter:
        return False, "Frontmatter missing 'trigger' field"
    
    validTriggers = ["always_on", "manual", "on_demand"]
    if frontmatter["trigger"] not in validTriggers:
        return False, f"Invalid trigger value. Must be one of: {', '.join(validTriggers)}"
    
    return True, None


def addFrontmatterToContent(
    content: str,
    frontmatter_config: Optional[FrontmatterConfig] = None
) -> str:
    """
    Add frontmatter to content if missing or invalid (MDC format)
    
    Args:
        content: File content
        frontmatter_config: Optional custom frontmatter defaults
    
    Returns:
        Content with valid frontmatter in MDC format
    """
    existingFrontmatter, contentBody = parseFrontmatter(content)
    
    # Check if existing frontmatter is valid
    isValid, errorMsg = validateFrontmatter(existingFrontmatter)
    
    if isValid:
        # Return content as-is if frontmatter is valid
        return content
    
    # Add default frontmatter if missing or invalid
    if frontmatter_config is None:
        frontmatter_config = FrontmatterConfig()
    
    # Log the action
    if existingFrontmatter:
        logger.info(f"Replacing invalid frontmatter: {errorMsg}")
    else:
        logger.info(f"Adding missing frontmatter (trigger: {frontmatter_config.trigger})")
    
    # Build content with frontmatter (MDC format)
    frontmatterYaml = frontmatter_to_yaml(frontmatter_config)
    return f"---\n{frontmatterYaml}\n---\n\n{contentBody}"


def extractRuleMetadata(content: str) -> Dict[str, Any]:
    """
    Extract metadata from rule content for tracking
    
    Args:
        content: Rule file content
    
    Returns:
        Dictionary with metadata
    """
    frontmatter, _ = parseFrontmatter(content)
    isValid, _ = validateFrontmatter(frontmatter)
    
    return {
        "hasFrontmatter": frontmatter is not None,
        "isValid": isValid,
        "trigger": frontmatter.get("trigger") if frontmatter else None,
        "glob": frontmatter.get("glob") if frontmatter else None,
        "description": frontmatter.get("description") if frontmatter else None
    }
