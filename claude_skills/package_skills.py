#!/usr/bin/env python3
"""
Claude Skills Packaging Tool

Creates ZIP packages for Claude custom skills according to the official specification:
https://support.claude.com/en/articles/12512198-how-to-create-custom-skills

Requirements:
- Each skill folder must contain Skill.md with YAML frontmatter
- ZIP structure must have skill folder at root (not files directly in ZIP root)
- Output: dist/{skill-name}.zip

Usage:
    python package_skills.py                  # Package all skills
    python package_skills.py vehicle-setup    # Package specific skill
    python package_skills.py --clean          # Clean dist folder first
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import argparse
import re

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


class SkillPackager:
    """Package Claude custom skills into distributable ZIP files."""

    def __init__(self, skills_dir: str = ".", dist_dir: str = "dist"):
        self.skills_dir = Path(skills_dir)
        self.dist_dir = Path(dist_dir)

    def validate_skill(self, skill_path: Path) -> tuple[bool, str]:
        """
        Validate that a skill folder meets requirements.

        Args:
            skill_path: Path to skill folder

        Returns:
            (is_valid, error_message)
        """
        # Check if SKILL.md exists (official Anthropic convention)
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            return False, f"Missing required SKILL.md file"

        # Validate YAML frontmatter
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for YAML frontmatter
            if not content.startswith('---'):
                return False, "SKILL.md missing YAML frontmatter (must start with ---)"

            # Extract frontmatter
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return False, "Invalid YAML frontmatter format"

            frontmatter = match.group(1)

            # Check required fields (per Claude Desktop spec)
            required_fields = ['name', 'description']
            for field in required_fields:
                if not re.search(rf'^{field}:\s*["\']?.+["\']?$', frontmatter, re.MULTILINE):
                    return False, f"Missing required field: {field}"

            # Check for disallowed fields
            # Allowed: name, description, license, allowed-tools, metadata
            allowed_fields = ['name', 'description', 'license', 'allowed-tools', 'metadata']
            for line in frontmatter.split('\n'):
                if ':' in line:
                    field = line.split(':')[0].strip()
                    if field and field not in allowed_fields:
                        return False, f"Disallowed field in frontmatter: {field}. Allowed: {', '.join(allowed_fields)}"

            # Validate description length (max 200 characters)
            desc_match = re.search(r'description:\s*["\'](.+?)["\']', frontmatter)
            if desc_match:
                desc = desc_match.group(1)
                if len(desc) > 200:
                    return False, f"Description too long ({len(desc)} chars, max 200)"

            # Validate name length (max 64 characters)
            name_match = re.search(r'name:\s*["\'](.+?)["\']', frontmatter)
            if name_match:
                name = name_match.group(1)
                if len(name) > 64:
                    return False, f"Name too long ({len(name)} chars, max 64)"

        except Exception as e:
            return False, f"Error reading SKILL.md: {str(e)}"

        return True, ""

    def get_skill_name(self, skill_path: Path) -> str:
        """Extract skill name from SKILL.md frontmatter."""
        skill_md = skill_path / "SKILL.md"
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'name:\s*["\'](.+?)["\']', content)
        if match:
            return match.group(1)
        return skill_path.name

    def package_skill(self, skill_name: str) -> bool:
        """
        Package a single skill into a ZIP file.

        Args:
            skill_name: Name of skill folder to package

        Returns:
            True if successful, False otherwise
        """
        skill_path = self.skills_dir / skill_name

        # Validate skill folder exists
        if not skill_path.exists() or not skill_path.is_dir():
            print(f"❌ Error: '{skill_name}' is not a valid skill folder")
            return False

        # Validate skill structure
        is_valid, error_msg = self.validate_skill(skill_path)
        if not is_valid:
            print(f"❌ Error validating '{skill_name}': {error_msg}")
            return False

        # Create dist directory if needed
        self.dist_dir.mkdir(exist_ok=True)

        # Create ZIP file
        zip_path = self.dist_dir / f"{skill_name}.zip"

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through skill directory
                for root, dirs, files in os.walk(skill_path):
                    # Skip hidden directories and __pycache__
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

                    for file in files:
                        # Skip hidden files and Python cache
                        if file.startswith('.') or file.endswith('.pyc'):
                            continue

                        file_path = Path(root) / file
                        # Calculate archive path (relative to skills_dir, keeping skill folder as root)
                        arcname = file_path.relative_to(self.skills_dir)
                        zipf.write(file_path, arcname)

            # Get skill display name
            display_name = self.get_skill_name(skill_path)

            # Get file size
            size_kb = zip_path.stat().st_size / 1024

            print(f"✅ Packaged: {skill_name}")
            print(f"   Name: {display_name}")
            print(f"   Output: {zip_path}")
            print(f"   Size: {size_kb:.1f} KB")

            return True

        except Exception as e:
            print(f"❌ Error packaging '{skill_name}': {str(e)}")
            return False

    def package_all(self) -> dict[str, bool]:
        """
        Package all valid skill folders.

        Returns:
            Dictionary mapping skill names to success status
        """
        results = {}

        # Find all potential skill folders
        for item in self.skills_dir.iterdir():
            # Skip non-directories and special folders
            if not item.is_dir():
                continue
            if item.name.startswith('.') or item.name in ['dist', '__pycache__']:
                continue

            # Check if it has SKILL.md
            if (item / "SKILL.md").exists():
                results[item.name] = self.package_skill(item.name)

        return results

    def clean_dist(self):
        """Remove all files from dist directory."""
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"🗑️  Cleaned dist directory")


def main():
    parser = argparse.ArgumentParser(
        description="Package Claude custom skills into ZIP files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python package_skills.py                    # Package all skills
  python package_skills.py vehicle-setup      # Package specific skill
  python package_skills.py --clean            # Clean dist first
  python package_skills.py --clean --all      # Clean and package all
        """
    )

    parser.add_argument(
        'skill',
        nargs='?',
        help='Specific skill to package (omit to package all)'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean dist directory before packaging'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Package all skills (default if no skill specified)'
    )

    parser.add_argument(
        '--dist',
        default='dist',
        help='Output directory (default: dist)'
    )

    args = parser.parse_args()

    # Determine skills directory (script location)
    script_dir = Path(__file__).parent

    packager = SkillPackager(skills_dir=script_dir, dist_dir=script_dir / args.dist)

    # Clean if requested
    if args.clean:
        packager.clean_dist()

    print("📦 Claude Skills Packager")
    print("=" * 50)

    # Package specific skill or all
    if args.skill:
        success = packager.package_skill(args.skill)
        sys.exit(0 if success else 1)
    else:
        results = packager.package_all()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Summary: {sum(results.values())}/{len(results)} skills packaged")

        if not all(results.values()):
            print("\n❌ Failed skills:")
            for skill, success in results.items():
                if not success:
                    print(f"   - {skill}")
            sys.exit(1)

        sys.exit(0)


if __name__ == "__main__":
    main()
