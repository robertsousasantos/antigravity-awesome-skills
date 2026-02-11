#!/usr/bin/env python3
"""
Debug script to inspect Microsoft Skills repository structure - v2
Handles all skill locations including plugins
"""

import subprocess
import tempfile
from pathlib import Path

MS_REPO = "https://github.com/microsoft/skills.git"

def inspect_repo():
    """Inspect the Microsoft skills repository structure"""
    print("🔍 Inspecting Microsoft Skills Repository Structure")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        print("\n1️⃣ Cloning repository...")
        subprocess.run(
            ["git", "clone", "--depth", "1", MS_REPO, str(temp_path)],
            check=True,
            capture_output=True
        )
        
        print("\n2️⃣ Repository structure:")
        print("\nTop-level directories:")
        for item in temp_path.iterdir():
            if item.is_dir():
                print(f"  📁 {item.name}/")
        
        # Check .github/skills
        github_skills = temp_path / ".github" / "skills"
        if github_skills.exists():
            skill_dirs = [d for d in github_skills.iterdir() if d.is_dir()]
            print(f"\n3️⃣ Found {len(skill_dirs)} directories in .github/skills/:")
            for skill_dir in skill_dirs[:5]:
                has_skill_md = (skill_dir / "SKILL.md").exists()
                print(f"  {'✅' if has_skill_md else '❌'} {skill_dir.name}")
            if len(skill_dirs) > 5:
                print(f"  ... and {len(skill_dirs) - 5} more")
        
        # Check .github/plugins
        github_plugins = temp_path / ".github" / "plugins"
        if github_plugins.exists():
            plugin_skills = list(github_plugins.rglob("SKILL.md"))
            print(f"\n🔌 Found {len(plugin_skills)} plugin skills in .github/plugins/:")
            for skill_file in plugin_skills[:5]:
                try:
                    rel_path = skill_file.relative_to(github_plugins)
                    print(f"  ✅ {rel_path}")
                except ValueError:
                    print(f"  ✅ {skill_file.name}")
            if len(plugin_skills) > 5:
                print(f"  ... and {len(plugin_skills) - 5} more")
        
        # Check skills directory
        skills_dir = temp_path / "skills"
        if skills_dir.exists():
            print(f"\n4️⃣ Checking skills/ directory structure:")
            
            # Count items
            all_items = list(skills_dir.rglob("*"))
            symlink_dirs = [s for s in all_items if s.is_symlink() and s.is_dir()]
            symlink_files = [s for s in all_items if s.is_symlink() and not s.is_dir()]
            regular_dirs = [s for s in all_items if s.is_dir() and not s.is_symlink()]
            
            print(f"  Total items: {len(all_items)}")
            print(f"  Regular directories: {len(regular_dirs)}")
            print(f"  Symlinked directories: {len(symlink_dirs)}")
            print(f"  Symlinked files: {len(symlink_files)}")
            
            # Show directory structure
            print(f"\n  Top-level categories in skills/:")
            for item in skills_dir.iterdir():
                if item.is_dir():
                    # Count subdirs
                    subdirs = [d for d in item.iterdir() if d.is_dir()]
                    print(f"    📁 {item.name}/ ({len(subdirs)} items)")
            
            if symlink_dirs:
                print(f"\n  Sample symlinked directories:")
                for symlink in symlink_dirs[:5]:
                    try:
                        target = symlink.resolve()
                        relative = symlink.relative_to(skills_dir)
                        target_name = target.name if target.exists() else "broken"
                        print(f"    {relative} → {target_name}")
                    except:
                        pass
        
        # Check for all SKILL.md files
        print(f"\n5️⃣ Comprehensive SKILL.md search:")
        all_skill_mds = list(temp_path.rglob("SKILL.md"))
        print(f"  Total SKILL.md files found: {len(all_skill_mds)}")
        
        # Categorize by location
        locations = {}
        for skill_md in all_skill_mds:
            try:
                if ".github/skills" in str(skill_md):
                    loc = ".github/skills"
                elif ".github/plugins" in str(skill_md):
                    loc = ".github/plugins"
                elif "/skills/" in str(skill_md):
                    loc = "skills/ (structure)"
                else:
                    loc = "other"
                
                locations[loc] = locations.get(loc, 0) + 1
            except:
                pass
        
        print(f"\n  Distribution by location:")
        for loc, count in sorted(locations.items()):
            print(f"    {loc}: {count}")
        
        # Show sample skills from each major category
        print(f"\n6️⃣ Sample skills by category:")
        
        if skills_dir.exists():
            for category in list(skills_dir.iterdir())[:3]:
                if category.is_dir():
                    skills_in_cat = [s for s in category.rglob("*") if s.is_dir() and (s.is_symlink() or (s / "SKILL.md").exists())]
                    print(f"\n  {category.name}/ ({len(skills_in_cat)} skills):")
                    for skill in skills_in_cat[:3]:
                        try:
                            rel = skill.relative_to(skills_dir)
                            print(f"    - {rel}")
                        except:
                            pass
        
        print("\n7️⃣ Recommendations:")
        print("  ✅ Preserve skills/ directory structure (Microsoft's organization)")
        print("  ✅ Resolve symlinks to actual content in .github/skills/")
        print("  ✅ Include plugin skills from .github/plugins/")
        print("  ✅ This gives you the cleanest, most maintainable structure")
        
        print("\n✨ Inspection complete!")

if __name__ == "__main__":
    try:
        inspect_repo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()