#!/usr/bin/env python3
"""
Sync Microsoft Skills Repository - v3
Preserves original structure from skills/ directory and handles all locations
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
import json

MS_REPO = "https://github.com/microsoft/skills.git"
TARGET_DIR = Path(__file__).parent.parent / "skills"

def clone_repo(temp_dir: Path):
    """Clone Microsoft skills repository"""
    print("🔄 Cloning Microsoft Skills repository...")
    subprocess.run(
        ["git", "clone", "--depth", "1", MS_REPO, str(temp_dir)],
        check=True
    )

def find_all_skills(source_dir: Path):
    """Find all SKILL.md files in the repository"""
    all_skills = {}
    
    # Search in .github/skills/
    github_skills = source_dir / ".github" / "skills"
    if github_skills.exists():
        for skill_dir in github_skills.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                all_skills[skill_dir.name] = skill_dir
    
    # Search in .github/plugins/
    github_plugins = source_dir / ".github" / "plugins"
    if github_plugins.exists():
        for skill_file in github_plugins.rglob("SKILL.md"):
            skill_dir = skill_file.parent
            skill_name = skill_dir.name
            if skill_name not in all_skills:
                all_skills[skill_name] = skill_dir
    
    return all_skills

def sync_skills_preserve_structure(source_dir: Path, target_dir: Path):
    """
    Sync skills preserving the original skills/ directory structure.
    This is better than auto-categorization since MS already organized them.
    """
    skills_source = source_dir / "skills"
    
    if not skills_source.exists():
        print("  ⚠️  skills/ directory not found, will use flat structure")
        return sync_skills_flat(source_dir, target_dir)
    
    # First, find all actual skill content
    all_skills = find_all_skills(source_dir)
    print(f"  📂 Found {len(all_skills)} total skills in repository")
    
    synced_count = 0
    skill_metadata = []
    
    # Walk through the skills/ directory structure
    for item in skills_source.rglob("*"):
        # Skip non-directories
        if not item.is_dir():
            continue
        
        # Check if this directory (or its symlink target) contains a SKILL.md
        skill_md = None
        skill_source_dir = None
        
        # If it's a symlink, resolve it
        if item.is_symlink():
            try:
                resolved = item.resolve()
                if (resolved / "SKILL.md").exists():
                    skill_md = resolved / "SKILL.md"
                    skill_source_dir = resolved
            except:
                continue
        elif (item / "SKILL.md").exists():
            skill_md = item / "SKILL.md"
            skill_source_dir = item
        
        if skill_md is None:
            continue
        
        # Get relative path from skills/ directory - this preserves MS's organization
        try:
            relative_path = item.relative_to(skills_source)
        except ValueError:
            # Shouldn't happen, but handle it
            continue
        
        # Create target directory preserving structure
        target_skill_dir = target_dir / "official" / "microsoft" / relative_path
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy SKILL.md
        shutil.copy2(skill_md, target_skill_dir / "SKILL.md")
        
        # Copy other files from the actual skill directory
        for file_item in skill_source_dir.iterdir():
            if file_item.name != "SKILL.md" and file_item.is_file():
                shutil.copy2(file_item, target_skill_dir / file_item.name)
        
        # Collect metadata
        skill_metadata.append({
            "path": str(relative_path),
            "name": item.name,
            "category": str(relative_path.parent),
            "source": str(skill_source_dir.relative_to(source_dir))
        })
        
        synced_count += 1
        print(f"  ✅ Synced: {relative_path}")
    
    # Also sync any skills from .github/plugins that aren't symlinked in skills/
    plugin_skills = find_plugin_skills(source_dir, skill_metadata)
    if plugin_skills:
        print(f"\n  📦 Found {len(plugin_skills)} additional plugin skills")
        for plugin_skill in plugin_skills:
            target_skill_dir = target_dir / "official" / "microsoft" / "plugins" / plugin_skill['name']
            target_skill_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy SKILL.md
            shutil.copy2(plugin_skill['source'] / "SKILL.md", target_skill_dir / "SKILL.md")
            
            # Copy other files
            for file_item in plugin_skill['source'].iterdir():
                if file_item.name != "SKILL.md" and file_item.is_file():
                    shutil.copy2(file_item, target_skill_dir / file_item.name)
            
            skill_metadata.append({
                "path": f"plugins/{plugin_skill['name']}",
                "name": plugin_skill['name'],
                "category": "plugins",
                "source": str(plugin_skill['source'].relative_to(source_dir))
            })
            
            synced_count += 1
            print(f"  ✅ Synced: plugins/{plugin_skill['name']}")
    
    return synced_count, skill_metadata

def find_plugin_skills(source_dir: Path, already_synced: list):
    """Find plugin skills that haven't been synced yet"""
    synced_names = {s['name'] for s in already_synced}
    plugin_skills = []
    
    github_plugins = source_dir / ".github" / "plugins"
    if github_plugins.exists():
        for skill_file in github_plugins.rglob("SKILL.md"):
            skill_dir = skill_file.parent
            skill_name = skill_dir.name
            
            if skill_name not in synced_names:
                plugin_skills.append({
                    'name': skill_name,
                    'source': skill_dir
                })
    
    return plugin_skills

def sync_skills_flat(source_dir: Path, target_dir: Path):
    """Fallback: sync all skills in a flat structure"""
    all_skills = find_all_skills(source_dir)
    
    synced_count = 0
    skill_metadata = []
    
    for skill_name, skill_dir in all_skills.items():
        target_skill_dir = target_dir / "official" / "microsoft" / skill_name
        target_skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy SKILL.md
        shutil.copy2(skill_dir / "SKILL.md", target_skill_dir / "SKILL.md")
        
        # Copy other files
        for item in skill_dir.iterdir():
            if item.name != "SKILL.md" and item.is_file():
                shutil.copy2(item, target_skill_dir / item.name)
        
        skill_metadata.append({
            "path": skill_name,
            "name": skill_name,
            "category": "root"
        })
        
        synced_count += 1
        print(f"  ✅ Synced: {skill_name}")
    
    return synced_count, skill_metadata

def create_attribution_file(target_dir: Path, metadata: list):
    """Create attribution and metadata file"""
    attribution = {
        "source": "microsoft/skills",
        "repository": "https://github.com/microsoft/skills",
        "license": "MIT",
        "synced_skills": len(metadata),
        "skills": metadata,
        "note": "Symlinks resolved and content copied for compatibility. Original directory structure preserved."
    }
    
    ms_dir = target_dir / "official" / "microsoft"
    ms_dir.mkdir(parents=True, exist_ok=True)
    
    with open(ms_dir / "ATTRIBUTION.json", "w") as f:
        json.dump(attribution, f, indent=2)

def copy_documentation(source_dir: Path, target_dir: Path):
    """Copy LICENSE and README files"""
    ms_dir = target_dir / "official" / "microsoft"
    ms_dir.mkdir(parents=True, exist_ok=True)
    
    if (source_dir / "LICENSE").exists():
        shutil.copy2(source_dir / "LICENSE", ms_dir / "LICENSE")
    
    if (source_dir / "README.md").exists():
        shutil.copy2(source_dir / "README.md", ms_dir / "README-MICROSOFT.md")

def main():
    """Main sync function"""
    print("🚀 Microsoft Skills Sync Script v3")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # Clone repository
            clone_repo(temp_path)
            
            # Create target directory
            TARGET_DIR.mkdir(parents=True, exist_ok=True)
            
            # Sync skills (preserving structure)
            print("\n🔗 Resolving symlinks and preserving directory structure...")
            count, metadata = sync_skills_preserve_structure(temp_path, TARGET_DIR)
            
            # Copy documentation
            print("\n📄 Copying documentation...")
            copy_documentation(temp_path, TARGET_DIR)
            
            # Create attribution file
            print("📝 Creating attribution metadata...")
            create_attribution_file(TARGET_DIR, metadata)
            
            print(f"\n✨ Success! Synced {count} Microsoft skills")
            print(f"📁 Location: {TARGET_DIR / 'official' / 'microsoft'}")
            
            # Show structure summary
            ms_dir = TARGET_DIR / "official" / "microsoft"
            categories = set()
            for skill in metadata:
                cat = skill.get('category', 'root')
                if cat != 'root':
                    categories.add(cat.split('/')[0] if '/' in cat else cat)
            
            print(f"\n📊 Organization:")
            print(f"  Total skills: {count}")
            print(f"  Categories: {', '.join(sorted(categories)[:10])}")
            if len(categories) > 10:
                print(f"  ... and {len(categories) - 10} more")
            
            print("\n📋 Next steps:")
            print("1. Review synced skills")
            print("2. Run: npm run validate")
            print("3. Update CATALOG.md")
            print("4. Update docs/SOURCES.md")
            print("5. Commit changes and create PR")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())