"""
MCP Tools - New comprehensive MCP tools for team configuration management
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from content_tracker import create_content_tracker

logger = logging.getLogger(__name__)


async def sync_profile_tool(
    profile_name: Optional[str],
    config,
    content_dir: Path,
    ide_manager,
    fetch_content_from_source_func,
    workspace_dir: Optional[Path] = None,
    current_ide = None,
    get_ide_content_dir_func = None
) -> str:
    """
    Sync all content (instructions, rules, workflows, prompts) for a profile
    """
    try:
        # Find active profile
        if profile_name is None:
            active_profiles = [p for p in config.profiles.values() if p.active]
            if not active_profiles:
                return json.dumps({
                    "success": False,
                    "error": "No active profile found"
                })
            profile = active_profiles[0]
            profile_name = profile.name
        else:
            if profile_name not in config.profiles:
                return json.dumps({
                    "success": False,
                    "error": f"Profile '{profile_name}' not found",
                    "available_profiles": list(config.profiles.keys())
                })
            profile = config.profiles[profile_name]
        
        # Use IDE-specific directory if available
        if current_ide and get_ide_content_dir_func:
            profile_dir = get_ide_content_dir_func(current_ide, profile_name)
        else:
            # Fallback to generic content directory
            profile_dir = content_dir / profile_name
        
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize content tracker
        content_tracker = create_content_tracker()
        
        # Fetch all content types
        results = {
            "instructions": [],
            "rules": [],
            "workflows": [],
            "prompts": []
        }
        
        security_issues = []
        
        from schemas import ContentType
        
        # Fetch instructions
        for source in profile.instructions:
            items = await fetch_content_from_source_func(source, ContentType.INSTRUCTION, profile_name)
            for item in items:
                # Save to file
                filename = f"instruction_{len(results['instructions'])}.md"
                file_path = profile_dir / "instructions" / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(item["content"], encoding='utf-8')
                
                results["instructions"].append({
                    "file": str(file_path),
                    "source": item["source"],
                    "size": item["size"],
                    "security_valid": item["security_valid"]
                })
                
                if not item["security_valid"]:
                    security_issues.append({
                        "type": "instruction",
                        "source": item["source"],
                        "violations": item["security_violations"]
                    })
        
        # Fetch rules
        for source in profile.rules:
            items = await fetch_content_from_source_func(source, ContentType.RULE, profile_name)
            for item in items:
                filename = f"rule_{len(results['rules'])}.md"
                file_path = profile_dir / "rules" / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(item["content"], encoding='utf-8')
                
                results["rules"].append({
                    "file": str(file_path),
                    "source": item["source"],
                    "size": item["size"]
                })
        
        # Fetch workflows
        for source in profile.workflows:
            items = await fetch_content_from_source_func(source, ContentType.WORKFLOW, profile_name)
            for item in items:
                filename = f"workflow_{len(results['workflows'])}.md"
                file_path = profile_dir / "workflows" / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(item["content"], encoding='utf-8')
                
                results["workflows"].append({
                    "file": str(file_path),
                    "source": item["source"],
                    "size": item["size"]
                })
        
        # Fetch prompts
        for source in profile.prompts:
            items = await fetch_content_from_source_func(source, ContentType.PROMPT, profile_name)
            for item in items:
                filename = f"prompt_{len(results['prompts'])}.md"
                file_path = profile_dir / "prompts" / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(item["content"], encoding='utf-8')
                
                results["prompts"].append({
                    "file": str(file_path),
                    "source": item["source"],
                    "size": item["size"]
                })
        
        # Clean up managed content that's no longer in profile
        removed_counts = content_tracker.cleanup_managed_content(
            profile_name,
            profile_dir,
            results
        )
        
        # Track newly synced content
        content_tracker.track_content(profile_name, profile_dir, results)
        
        # Update IDE settings
        instruction_paths = {}
        instructions_base = profile_dir / "instructions"
        if instructions_base.exists():
            instruction_paths[str(instructions_base)] = True
        
        # Prepare rules content for IDE syncing
        rules_content = {}
        for rule_item in results.get("rules", []):
            rule_path = Path(rule_item["file"])
            if rule_path.exists():
                rules_content[rule_path.name] = rule_path.read_text(encoding='utf-8')
        
        ide_sync_results = ide_manager.sync_to_all_ides(
            instruction_paths,
            profile.mcp_servers if profile.mcp_servers else None,
            workspace_dir,
            profile_name=profile_name,
            rules_content=rules_content if rules_content else None
        )
        
        return json.dumps({
            "success": True,
            "profile": profile_name,
            "synced_content": {
                "instructions": len(results["instructions"]),
                "rules": len(results["rules"]),
                "workflows": len(results["workflows"]),
                "prompts": len(results["prompts"])
            },
            "removed_content": removed_counts,
            "files": results,
            "security_issues": security_issues,
            "ide_sync": {ide.value: success for ide, success in ide_sync_results.items()},
            "profile_directory": str(profile_dir)
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error syncing profile: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })
