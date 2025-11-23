#!/usr/bin/env python3
"""
Migration Script: Restructure Car Log Skills to Match Official Anthropic Conventions

Changes:
1. Rename Skill.md → SKILL.md
2. Create references/ subfolder
3. Move GUIDE.md → references/guide.md
4. Move REFERENCE.md → references/mcp-tools.md
5. Copy LICENSE.txt to each skill (optional)

Usage:
    python migrate_structure.py --test vehicle-setup    # Test on one skill
    python migrate_structure.py --all                    # Migrate all skills
    python migrate_structure.py --dry-run                # Show what would happen
"""

import os
import sys
import shutil
from pathlib import Path
import argparse

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


SKILLS = [
    "vehicle-setup",
    "checkpoint-from-receipt",
    "template-creation",
    "trip-reconstruction",
    "data-validation",
    "report-generation"
]


class SkillMigrator:
    """Migrate skill structure to match official Anthropic conventions."""

    def __init__(self, skills_dir: Path, dry_run: bool = False):
        self.skills_dir = skills_dir
        self.dry_run = dry_run
        self.changes = []

    def log_change(self, action: str, detail: str):
        """Log a change that will be/was made."""
        self.changes.append((action, detail))
        prefix = "[DRY RUN] " if self.dry_run else ""
        print(f"{prefix}{action}: {detail}")

    def migrate_skill(self, skill_name: str) -> bool:
        """
        Migrate a single skill to the new structure.

        Returns:
            True if successful, False otherwise
        """
        skill_path = self.skills_dir / skill_name

        if not skill_path.exists():
            print(f"❌ Skill folder not found: {skill_name}")
            return False

        print(f"\n{'='*60}")
        print(f"Migrating: {skill_name}")
        print(f"{'='*60}")

        try:
            # Step 1: Rename Skill.md → SKILL.md
            old_skill_md = skill_path / "Skill.md"
            new_skill_md = skill_path / "SKILL.md"

            if old_skill_md.exists():
                self.log_change("RENAME", f"{skill_name}/Skill.md → SKILL.md")
                if not self.dry_run:
                    # Windows is case-insensitive, need temp file
                    temp_md = skill_path / "SKILL.md.tmp"
                    old_skill_md.rename(temp_md)
                    temp_md.rename(new_skill_md)
            elif new_skill_md.exists():
                self.log_change("SKIP", f"{skill_name}/SKILL.md already exists")
            else:
                print(f"⚠️  Warning: No Skill.md or SKILL.md found in {skill_name}")

            # Step 2: Create references/ folder
            references_dir = skill_path / "references"
            if not references_dir.exists():
                self.log_change("CREATE", f"{skill_name}/references/")
                if not self.dry_run:
                    references_dir.mkdir(parents=True, exist_ok=True)
            else:
                self.log_change("SKIP", f"{skill_name}/references/ already exists")

            # Step 3: Move GUIDE.md → references/guide.md
            guide_md = skill_path / "GUIDE.md"
            new_guide = references_dir / "guide.md"

            if guide_md.exists():
                self.log_change("MOVE", f"{skill_name}/GUIDE.md → references/guide.md")
                if not self.dry_run:
                    guide_md.rename(new_guide)
            elif new_guide.exists():
                self.log_change("SKIP", f"{skill_name}/references/guide.md already exists")
            else:
                self.log_change("WARNING", f"{skill_name}/GUIDE.md not found")

            # Step 4: Move REFERENCE.md → references/mcp-tools.md
            reference_md = skill_path / "REFERENCE.md"
            new_reference = references_dir / "mcp-tools.md"

            if reference_md.exists():
                self.log_change("MOVE", f"{skill_name}/REFERENCE.md → references/mcp-tools.md")
                if not self.dry_run:
                    reference_md.rename(new_reference)
            elif new_reference.exists():
                self.log_change("SKIP", f"{skill_name}/references/mcp-tools.md already exists")
            else:
                self.log_change("WARNING", f"{skill_name}/REFERENCE.md not found")

            # Step 5: Copy LICENSE.txt (optional)
            project_license = self.skills_dir.parent / "LICENSE"
            skill_license = skill_path / "LICENSE.txt"

            if project_license.exists() and not skill_license.exists():
                self.log_change("COPY", f"LICENSE → {skill_name}/LICENSE.txt")
                if not self.dry_run:
                    shutil.copy2(project_license, skill_license)
            elif skill_license.exists():
                self.log_change("SKIP", f"{skill_name}/LICENSE.txt already exists")
            else:
                self.log_change("INFO", "No project LICENSE file found, skipping")

            print(f"✅ {skill_name} migration {'planned' if self.dry_run else 'completed'}")
            return True

        except Exception as e:
            print(f"❌ Error migrating {skill_name}: {str(e)}")
            return False

    def verify_structure(self, skill_name: str) -> bool:
        """Verify a skill has the correct structure."""
        skill_path = self.skills_dir / skill_name

        print(f"\nVerifying {skill_name}...")

        required_files = [
            ("SKILL.md", True),
            ("references/guide.md", True),
            ("references/mcp-tools.md", True),
            ("examples", False),  # Directory, not file
            ("LICENSE.txt", False)  # Optional
        ]

        all_good = True
        for file_path, is_required in required_files:
            full_path = skill_path / file_path
            exists = full_path.exists()

            if is_required and not exists:
                print(f"  ❌ Missing required: {file_path}")
                all_good = False
            elif exists:
                print(f"  ✅ {file_path}")
            else:
                print(f"  ⚪ Optional: {file_path} (not present)")

        # Check for old files that should be removed
        old_files = ["Skill.md", "GUIDE.md", "REFERENCE.md"]
        for old_file in old_files:
            old_path = skill_path / old_file
            if old_path.exists():
                print(f"  ⚠️  Old file still exists: {old_file}")
                all_good = False

        return all_good

    def migrate_all(self) -> dict[str, bool]:
        """Migrate all skills."""
        results = {}

        for skill_name in SKILLS:
            results[skill_name] = self.migrate_skill(skill_name)

        return results

    def print_summary(self, results: dict[str, bool]):
        """Print migration summary."""
        print(f"\n{'='*60}")
        print("MIGRATION SUMMARY")
        print(f"{'='*60}")

        successful = sum(1 for v in results.values() if v)
        total = len(results)

        print(f"\nResults: {successful}/{total} skills migrated successfully")

        if successful < total:
            print("\n❌ Failed skills:")
            for skill, success in results.items():
                if not success:
                    print(f"   - {skill}")

        print(f"\nTotal changes {'planned' if self.dry_run else 'made'}: {len(self.changes)}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate Car Log skills to match official Anthropic structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_structure.py --dry-run           # Show what would happen
  python migrate_structure.py --test vehicle-setup # Test on one skill
  python migrate_structure.py --all                # Migrate all skills
  python migrate_structure.py --verify             # Verify structure after migration
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--test',
        metavar='SKILL',
        help='Test migration on a single skill'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all skills'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify structure of all skills'
    )

    args = parser.parse_args()

    # Determine skills directory (script location)
    script_dir = Path(__file__).parent

    migrator = SkillMigrator(skills_dir=script_dir, dry_run=args.dry_run)

    print("🔄 Claude Skills Structure Migration")
    print(f"{'='*60}")
    print(f"Mode: {'DRY RUN (no changes)' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"{'='*60}")

    if args.verify:
        # Verification mode
        print("\n📋 Verifying skill structures...")
        all_valid = True
        for skill_name in SKILLS:
            if not migrator.verify_structure(skill_name):
                all_valid = False

        if all_valid:
            print("\n✅ All skills have correct structure!")
            sys.exit(0)
        else:
            print("\n❌ Some skills have structure issues")
            sys.exit(1)

    elif args.test:
        # Test mode - single skill
        if args.test not in SKILLS:
            print(f"❌ Unknown skill: {args.test}")
            print(f"Available skills: {', '.join(SKILLS)}")
            sys.exit(1)

        success = migrator.migrate_skill(args.test)

        if not args.dry_run and success:
            print("\n📋 Verifying migration...")
            migrator.verify_structure(args.test)

        sys.exit(0 if success else 1)

    elif args.all:
        # Migrate all skills
        results = migrator.migrate_all()
        migrator.print_summary(results)

        if not args.dry_run:
            print("\n📋 Verifying all migrations...")
            all_valid = True
            for skill_name in SKILLS:
                if not migrator.verify_structure(skill_name):
                    all_valid = False

            if all_valid:
                print("\n✅ All skills migrated and verified successfully!")
            else:
                print("\n⚠️  Some skills have verification issues")

        sys.exit(0 if all(results.values()) else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
