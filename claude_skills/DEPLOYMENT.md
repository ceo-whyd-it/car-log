# Claude Skills Deployment Guide

This guide explains how to package and deploy Car Log skills to Claude Desktop.

## Overview

Car Log skills are packaged as ZIP files and installed via Claude Desktop's built-in skills interface. This is separate from MCP server deployment.

**Two deployment components:**
1. **MCP Servers** - Deployed using `deployment/scripts/deploy-*.sh` or `install.bat` (see main README.md)
2. **Skills** - Deployed using ZIP files created by `package_skills.py` (this guide)

---

## Quick Start

### 1. Package All Skills

**Windows:**
```cmd
cd claude_skills
package_skills.bat --clean --all
```

**Linux/macOS:**
```bash
cd claude_skills
./package_skills.sh --clean --all
```

**Output:** 6 ZIP files in `dist/` directory (84 KB total)

### 2. Install in Claude Desktop

1. Open Claude Desktop
2. Navigate to **Settings → Skills**
3. Click **"Add Skill"**
4. Select ZIP file from `claude_skills/dist/`
5. Click **"Install"**
6. Repeat for all 6 skills

---

## Packaging Reference

### Package Single Skill

```bash
python package_skills.py vehicle-setup
```

### Package All Skills

```bash
python package_skills.py --all
```

### Clean and Rebuild

```bash
python package_skills.py --clean --all
```

### Verify Packaging

```bash
# Check ZIP contents
cd dist
unzip -l vehicle-setup.zip

# Expected structure:
# vehicle-setup/
# ├── SKILL.md
# ├── references/
# │   ├── guide.md
# │   └── mcp-tools.md
# └── examples/
```

---

## Skills Manifest

### Core Workflow Skills (Install in order)

1. **vehicle-setup.zip** (8.4 KB)
   - Register vehicle with VIN validation
   - Slovak VAT Act 2025 compliance
   - **Activation:** "add vehicle", "register car"

2. **checkpoint-from-receipt.zip** (12.3 KB)
   - Create checkpoints from receipt photos
   - QR scanning + e-Kasa API + GPS extraction
   - **Activation:** Auto-detect image paste, "refuel", "checkpoint"

3. **template-creation.zip** (12.1 KB)
   - Create recurring trip templates with GPS
   - GPS (70%) + address (30%) matching
   - **Activation:** "create template", "save route"

4. **trip-reconstruction.zip** (15.9 KB)
   - Fill gaps using template matching
   - High-confidence automatic proposals
   - **Activation:** Auto-trigger after gap detection

5. **data-validation.zip** (11.1 KB)
   - 4 validation algorithms
   - Distance, fuel, efficiency, deviation checks
   - **Activation:** Auto-trigger after trip creation

6. **report-generation.zip** (9.4 KB)
   - Generate Slovak VAT Act 2025 compliant CSV reports
   - Business trip tax deduction ready
   - **Activation:** "generate report", "export CSV"

---

## Deployment Workflow

### For Developers (Contributing)

```bash
# 1. Make changes to skill SKILL.md or references/ files
cd claude_skills/vehicle-setup
vim SKILL.md  # Edit skill

# 2. Test changes locally (copy SKILL.md content to Claude Desktop)

# 3. Repackage skill
cd ..
python package_skills.py vehicle-setup

# 4. Test packaged ZIP
# Install in Claude Desktop from dist/vehicle-setup.zip

# 5. If good, commit changes
git add vehicle-setup/
git commit -m "feat(skills): update vehicle-setup skill"
```

### For End Users (Installing)

```bash
# 1. Download Car Log repository
git clone https://github.com/your-org/car-log.git
cd car-log/claude_skills

# 2. Package skills (if not pre-packaged)
python package_skills.py --all

# 3. Install in Claude Desktop
# - Open Claude Desktop → Settings → Skills
# - Add each ZIP from dist/ folder

# 4. Verify skills loaded
# - Start new conversation
# - Type "add vehicle" → Should trigger vehicle-setup skill
```

---

## CI/CD Automation (Future)

### GitHub Actions Example

```yaml
name: Package Skills

on:
  push:
    paths:
      - 'claude_skills/**'
      - '!claude_skills/dist/**'

jobs:
  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Package skills
        run: |
          cd claude_skills
          python package_skills.py --clean --all

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: car-log-skills
          path: claude_skills/dist/*.zip

      - name: Create release (on tag)
        if: startsWith(github.ref, 'refs/tags/v')
        uses: softprops/action-gh-release@v1
        with:
          files: claude_skills/dist/*.zip
```

---

## Troubleshooting

### Error: "Missing required SKILL.md file"

**Cause:** Skill folder doesn't have SKILL.md (ALL CAPS)

**Fix:**
```bash
cd skill-folder
# Rename from Skill.md to SKILL.md
mv Skill.md SKILL.md  # Linux/macOS
ren Skill.md SKILL.md  # Windows
```

### Error: "Description too long"

**Cause:** Description in SKILL.md YAML frontmatter exceeds 200 characters

**Fix:** Edit SKILL.md and shorten description field

### Error: "Python not found"

**Cause:** Python not in PATH

**Fix:**
```bash
# Check Python installation
python --version  # or python3 --version

# If not installed:
# Windows: Download from python.org
# macOS: brew install python3
# Linux: sudo apt install python3
```

### Skill not activating in Claude Desktop

**Possible causes:**
1. Skill not installed correctly
2. Description doesn't match trigger words
3. MCP servers not deployed

**Fix:**
1. Verify skill installed: Claude Desktop → Settings → Skills
2. Check description in SKILL.md (must include trigger keywords)
3. Deploy MCP servers first: See INSTALLATION.md

---

## Distribution

### Pre-packaged Release

For releases, pre-package all skills:

```bash
# Clean and package
cd claude_skills
python package_skills.py --clean --all

# Verify
ls -lh dist/
# Should show 6 ZIP files (84 KB total)

# Commit packaged ZIPs (optional)
git add dist/
git commit -m "chore: package skills for v1.0.0 release"
```

### User Installation from Release

Users can download pre-packaged ZIPs from releases:

1. Go to: https://github.com/your-org/car-log/releases
2. Download `car-log-skills-v1.0.0.zip`
3. Extract to find 6 individual skill ZIPs
4. Install each in Claude Desktop

---

## Updating Skills

### Update Single Skill

```bash
# 1. Edit skill
vim claude_skills/vehicle-setup/SKILL.md

# 2. Update version in YAML frontmatter
# version: "1.0.0" → "1.1.0"

# 3. Repackage
python package_skills.py vehicle-setup

# 4. Reinstall in Claude Desktop
# - Claude Desktop → Settings → Skills
# - Remove old vehicle-setup
# - Install new vehicle-setup.zip
```

### Update All Skills

```bash
# Repackage all
python package_skills.py --clean --all

# Reinstall all in Claude Desktop
# (ZIP with same name auto-updates)
```

---

## Structure Compliance

Skills follow the official Anthropic skills repository pattern:

**Reference:** https://github.com/anthropics/skills

```
skill-name/
├── SKILL.md              ← ALL CAPS (official convention)
├── references/           ← Supporting docs subfolder
│   ├── guide.md
│   └── mcp-tools.md
└── examples/             ← Example files
```

**Validation:** `python package_skills.py` validates structure before packaging

---

## Related Documentation

- **PACKAGING.md** - Detailed packaging reference
- **INSTALLATION.md** - MCP server + skills installation
- **STRUCTURE_COMPARISON.md** - Official Anthropic pattern comparison
- **README.md** - Skills overview and usage

---

## Support

**Issues:** https://github.com/your-org/car-log/issues
**Discussions:** https://github.com/your-org/car-log/discussions
**Hackathon:** MCP 1st Birthday Hackathon (Nov 2025)
