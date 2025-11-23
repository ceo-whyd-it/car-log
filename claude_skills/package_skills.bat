@echo off
REM Claude Skills Packaging Tool - Windows Batch Wrapper
REM
REM Usage:
REM   package_skills.bat              - Package all skills
REM   package_skills.bat vehicle-setup - Package specific skill
REM   package_skills.bat --clean      - Clean dist folder first

python package_skills.py %*
