"""
IDE Adapter Module

Provides compatibility layer between config-based IDE definitions and the IDE manager.
Allows loading IDE configurations from team_config.yaml while maintaining backward compatibility.
"""
import logging
from typing import Dict, Optional
from schemas import IDEType, IDEConfig, get_default_ide_configs

logger = logging.getLogger(__name__)


# Mapping from IDE names to IDEType enum (for backward compatibility)
IDE_NAME_TO_TYPE = {
    "vscode": IDEType.VSCODE,
    "cursor": IDEType.CURSOR,
    "windsurf": IDEType.WINDSURF,
}

IDE_TYPE_TO_NAME = {
    IDEType.VSCODE: "vscode",
    IDEType.CURSOR: "cursor",
    IDEType.WINDSURF: "windsurf",
}


def loadIdeConfigsFromTeamConfig(teamConfig) -> Dict[str, IDEConfig]:
    """
    Load IDE configurations from team config, merging with defaults
    
    Args:
        teamConfig: TeamConfig object
    
    Returns:
        Dictionary of IDE configurations
    """
    # Start with defaults
    ideConfigs = get_default_ide_configs()
    
    # Override with team config IDE definitions
    if hasattr(teamConfig, 'ide_configs') and teamConfig.ide_configs:
        for ideName, ideConfig in teamConfig.ide_configs.items():
            ideConfigs[ideName] = ideConfig
            logger.info(f"Loaded custom IDE config for: {ideName}")
    
    return ideConfigs


def getIdeTypeFromName(ideName: str) -> Optional[IDEType]:
    """
    Convert IDE name to IDEType enum
    
    Args:
        ideName: IDE name (e.g., "vscode")
    
    Returns:
        IDEType or None if unknown
    """
    return IDE_NAME_TO_TYPE.get(ideName.lower())


def getIdeNameFromType(ideType: IDEType) -> str:
    """
    Convert IDEType enum to IDE name
    
    Args:
        ideType: IDEType enum
    
    Returns:
        IDE name string
    """
    return IDE_TYPE_TO_NAME.get(ideType, ideType.value)


def getSupportedIdesFromConfig(teamConfig) -> list:
    """
    Get list of supported IDE names from config
    
    Args:
        teamConfig: TeamConfig object
    
    Returns:
        List of IDE names
    """
    if hasattr(teamConfig, 'supported_ides'):
        return teamConfig.supported_ides
    
    # Default to common IDEs
    return ["vscode", "cursor", "windsurf"]
