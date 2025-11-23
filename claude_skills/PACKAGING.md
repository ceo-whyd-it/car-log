# Claude Skills Packaging Guide

This directory contains tools to package Car Log custom skills into distributable ZIP files according to [Claude's official specification](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

## Quick Start

### Package All Skills
```bash
# Linux/macOS
python package_skills.py

# Windows
package_skills.bat
```

### Package Specific Skill
```bash
python package_skills.py vehicle-setup
```

### Clean and Rebuild
```bash
python package_skills.py --clean --all
```

## Output Structure

Packaged skills are created in the `dist/` directory:

```
claude_skills/
├── dist/
│   ├── vehicle-setup.zip
│   ├── checkpoint-from-receipt.zip
│   ├── template-creation.zip
│   ├── trip-reconstruction.zip
│   ├── data-validation.zip
│   └── report-generation.zip
├── vehicle-setup/
│   ├── SKILL.md          ← Required (ALL CAPS per official spec)
│   ├── references/       ← Supporting documentation
│   │   ├── guide.md
│   │   └── mcp-tools.md
│   └── examples/         ← Example files
└── ...
```

## ZIP Structure (Per Official Spec)

Each ZIP file contains the skill folder as its root, matching the [official Anthropic skills repository](https://github.com/anthropics/skills) structure:

```
vehicle-setup.zip
└── vehicle-setup/
    ├── SKILL.md              ← ALL CAPS (official convention)
    ├── references/           ← Supporting documentation subfolder
    │   ├── guide.md
    │   └── mcp-tools.md
    └── examples/             ← Example files
        └── test-vehicle.json
```

**Important:**
- Files must NOT be directly in the ZIP root. The skill folder must be the root element.
- Main file must be `SKILL.md` (ALL CAPS) per official Anthropic specification
- Supporting docs go in `references/` subfolder (not at root)

## Validation Rules

The packaging tool validates each skill before creating the ZIP:

### Required: SKILL.md with YAML Frontmatter

**Important:** File must be named `SKILL.md` (ALL CAPS) per [official Anthropic specification](https://github.com/anthropics/skills).

```yaml
---
name: "Vehicle Setup"
description: "Guide users through Slovak VAT Act 2025 compliant vehicle registration with VIN validation"
version: "1.0.0"
---
```

### Field Requirements

| Field | Required | Max Length | Description |
|-------|----------|------------|-------------|
| `name` | ✅ Yes | 64 chars | Human-friendly skill name |
| `description` | ✅ Yes | 200 chars | When to use this skill (Claude uses this for activation) |
| `version` | ✅ Yes | - | Semantic version (e.g., 1.0.0) |
| `dependencies` | ❌ No | - | Software requirements (e.g., python>=3.8) |

### Optional Supporting Files

- **references/**: Supporting documentation subfolder (following official Anthropic pattern)
  - **guide.md**: Detailed usage examples and workflows
  - **mcp-tools.md**: MCP tool specifications, API details
- **examples/**: Sample inputs/outputs, test cases
- **scripts/**: Executable Python/JavaScript (if skill uses them - not used in Car Log skills yet)

## Validation Checks

The tool performs these checks before packaging:

✅ **SKILL.md exists** (filename must be exactly `SKILL.md` - ALL CAPS per official spec)
✅ **YAML frontmatter present** (starts with `---`)
✅ **Required fields exist** (`name`, `description`, `version`)
✅ **Description ≤ 200 characters** (Claude's limit)
✅ **Name ≤ 64 characters** (Claude's limit)
✅ **No hidden files included** (skips `.git`, `.DS_Store`, etc.)
✅ **No Python cache** (skips `__pycache__`, `.pyc` files)
✅ **Structure matches official Anthropic pattern** (references/ subfolder for supporting docs)

## Command-Line Options

```bash
python package_skills.py [OPTIONS] [SKILL_NAME]

Arguments:
  SKILL_NAME          Specific skill to package (optional)

Options:
  --clean             Clean dist directory before packaging
  --all               Package all skills (default if no SKILL_NAME)
  --dist DIR          Output directory (default: dist)
  -h, --help          Show help message
```

## Examples

### Package All Skills
```bash
python package_skills.py
```

Output:
```
📦 Claude Skills Packager
==================================================
✅ Packaged: checkpoint-from-receipt
   Name: Checkpoint from Receipt
   Output: dist/checkpoint-from-receipt.zip
   Size: 45.2 KB

✅ Packaged: data-validation
   Name: Data Validation
   Output: dist/data-validation.zip
   Size: 38.7 KB

...

📊 Summary: 6/6 skills packaged
```

### Package Single Skill with Clean
```bash
python package_skills.py --clean vehicle-setup
```

Output:
```
📦 Claude Skills Packager
==================================================
🗑️  Cleaned dist directory
✅ Packaged: vehicle-setup
   Name: Vehicle Setup
   Output: dist/vehicle-setup.zip
   Size: 22.1 KB
```

### Validation Error Example
```bash
python package_skills.py broken-skill
```

Output:
```
📦 Claude Skills Packager
==================================================
❌ Error validating 'broken-skill': Description too long (245 chars, max 200)
```

## Installing Skills in Claude

### Claude Desktop App

1. Navigate to **Settings > Skills**
2. Click **Add Skill**
3. Select the ZIP file from `dist/` directory
4. Click **Install**

The skill will be available immediately in new conversations.

### Claude Web/API

Skills created with this tool are compatible with Claude Desktop only. For API/web usage, use MCP servers directly.

## Troubleshooting

### Error: "Missing required SKILL.md file"

**Cause:** File is named `Skill.md` (mixed case) instead of `SKILL.md` (all caps)

**Fix:**
```bash
cd skill-folder
# Windows (case-insensitive filesystem)
ren Skill.md SKILL.md.tmp
ren SKILL.md.tmp SKILL.md

# Linux/macOS (case-sensitive filesystem)
mv Skill.md SKILL.md
```

### Error: "Description too long"

**Cause:** Description field exceeds 200 characters

**Fix:** Edit Skill.md and shorten the description:
```yaml
# Before (too long)
description: "This is a very long description that exceeds the 200 character limit imposed by Claude's custom skills specification and will cause validation to fail..."

# After (concise)
description: "Guide users through Slovak VAT Act 2025 compliant vehicle registration with VIN validation"
```

### Error: "Invalid YAML frontmatter format"

**Cause:** Frontmatter doesn't start/end with `---`

**Fix:** Ensure SKILL.md starts with:
```yaml
---
name: "Skill Name"
description: "What it does"
version: "1.0.0"
---
```

**Note:** Per official Anthropic specification, the main skill file must be named `SKILL.md` (ALL CAPS).

## File Structure Best Practices

### Good Structure ✅ (Matches Official Anthropic Pattern)
```
vehicle-setup/
├── SKILL.md                  # 2.8 KB - Core instructions (ALL CAPS)
├── references/               # Supporting documentation subfolder
│   ├── guide.md             # 15.4 KB - Detailed examples
│   └── mcp-tools.md         # 4.0 KB - MCP tool specs
└── examples/                 # Example files
    ├── simple.json
    └── complex.json
```

**Why:**
- SKILL.md is concise (Claude reads this first)
- Supporting docs organized in references/ subfolder
- Matches official Anthropic skills repository structure
- Easy to navigate and maintain

### Bad Structure ❌
```
vehicle-setup/
└── SKILL.md           # 85 KB - Everything in one file
```

**Why:** SKILL.md is too large. Split into supporting files in references/ subfolder.

## Integration with Car Log Workflow

These skills orchestrate Car Log's 7 MCP servers for conversational trip logging:

1. **vehicle-setup** → `car-log-core.create_vehicle`
2. **checkpoint-from-receipt** → `ekasa-api.scan_qr_code` → `dashboard-ocr.extract_metadata` → `car-log-core.create_checkpoint`
3. **trip-reconstruction** → `car-log-core.analyze_gap` → `trip-reconstructor.match_templates`
4. **template-creation** → `geo-routing.geocode_address` → `car-log-core.create_template`
5. **data-validation** → `validation.validate_checkpoint_pair`
6. **report-generation** → `report-generator.generate_csv`

See **INSTALLATION.md** for MCP server configuration.

## Development Workflow

### Adding a New Skill

1. Create skill folder: `mkdir claude_skills/my-new-skill`
2. Create Skill.md with frontmatter
3. Add supporting files (GUIDE.md, examples/)
4. Validate: `python package_skills.py my-new-skill`
5. Test in Claude Desktop
6. Commit to repository

### Updating Existing Skill

1. Edit Skill.md or supporting files
2. Increment version in frontmatter
3. Repackage: `python package_skills.py skill-name`
4. Reinstall in Claude Desktop (ZIP with same name auto-updates)

## CI/CD Integration

The packaging tool returns proper exit codes:

- **0**: All skills packaged successfully
- **1**: One or more skills failed validation

Example GitHub Actions workflow:

```yaml
name: Package Skills

on: [push]

jobs:
  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: cd claude_skills && python package_skills.py
      - uses: actions/upload-artifact@v2
        with:
          name: skills
          path: claude_skills/dist/*.zip
```

## License

Part of Car Log - Slovak Tax-Compliant Mileage Logger
MIT License (see root LICENSE file)

## References

- [Claude Custom Skills Documentation](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Car Log MCP Architecture](../spec/06-mcp-architecture-v2.md)
- [Installation Guide](INSTALLATION.md)
