# Skills vs Guides: Understanding the Structure

## Overview

This directory contains **two types of documentation** that serve different purposes:

### 1. Skills (SKILL.md) - For Claude Desktop

**Purpose:** Concise, directive-style prompts that Claude uses to execute workflows

**Characteristics:**
- **Short:** 200-600 words
- **Directive:** "When user does X, you do Y"
- **Actionable:** Step-by-step instructions
- **Format:** Markdown

**Location:** `<skill-folder>/SKILL.md`

**Usage:** Copy content into Claude Desktop Custom Instructions or Skills

**Example:** vehicle-setup/SKILL.md (300 words)

### 2. Guides (GUIDE.md) - For Humans

**Purpose:** Comprehensive documentation for users and developers

**Characteristics:**
- **Long:** 12-25 KB (3,000-7,000 words)
- **Explanatory:** Detailed workflows, examples, testing scenarios
- **Educational:** Code examples, edge cases, troubleshooting
- **Format:** Markdown with code blocks, tables, diagrams

**Location:** `<skill-folder>/GUIDE.md`

**Usage:** Read for understanding, testing, and development reference

**Example:** vehicle-setup/GUIDE.md (15KB)

### 3. Reference (REFERENCE.md) - For Developers

**Purpose:** MCP tool API specifications

**Characteristics:**
- **Technical:** JSON request/response formats
- **Complete:** All tool parameters documented
- **Concise:** Only API specs, no explanations

**Location:** `<skill-folder>/REFERENCE.md`

**Usage:** Reference when debugging or developing MCP integrations

---

## When to Use Each

| Task | Use |
|------|-----|
| Install skill in Claude Desktop | **SKILL.md** (copy to Custom Instructions) |
| Understand workflow details | **GUIDE.md** (read comprehensive guide) |
| Debug MCP tool calls | **REFERENCE.md** (check API specs) |
| Test with sample data | **examples/*.json** |
| Learn best practices | **../BEST_PRACTICES.md** |
| Troubleshoot issues | **../TROUBLESHOOTING.md** |

---

## Folder Structure

```
vehicle-setup/
├── SKILL.md        # ← Copy this to Claude Desktop (300 words)
├── GUIDE.md        # ← Read this for details (15KB)
├── REFERENCE.md    # ← Check this for MCP API (2KB)
└── examples/       # ← Use this for testing
    └── test-vehicle.json
```

---

## Complete Workflow

**Step 1:** Install skill
- Copy `SKILL.md` → Claude Desktop Custom Instructions

**Step 2:** Understand details
- Read `GUIDE.md` for comprehensive workflows

**Step 3:** Test skill
- Use `examples/*.json` as test data
- Follow `MANUAL_TEST_CHECKLIST.md`

**Step 4:** Debug if needed
- Check `REFERENCE.md` for MCP tool specs
- See `TROUBLESHOOTING.md` for common issues

---

## File Sizes Reference

| Skill | SKILL.md | GUIDE.md | REFERENCE.md |
|-------|----------|----------|--------------|
| vehicle-setup | 300 words | 15KB | 2KB |
| checkpoint-from-receipt | 500 words | 21KB | 3KB |
| trip-reconstruction | 600 words | 25KB | 4KB |
| template-creation | 400 words | 12KB | 2KB |
| report-generation | 300 words | 17KB | 2KB |
| data-validation | 300 words | 16KB | 3KB |

---

**Last Updated:** November 20, 2025
**Status:** All skills implemented with proper structure
