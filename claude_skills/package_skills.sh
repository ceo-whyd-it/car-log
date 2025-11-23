#!/bin/bash
# Claude Skills Packaging Tool - Unix Shell Wrapper
#
# Usage:
#   ./package_skills.sh              - Package all skills
#   ./package_skills.sh vehicle-setup - Package specific skill
#   ./package_skills.sh --clean      - Clean dist folder first

python3 package_skills.py "$@"
