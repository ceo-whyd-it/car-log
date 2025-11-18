# Car Log - Deployment & Troubleshooting Guide

**Version:** 1.0
**Date:** 2025-11-18
**Status:** Production-Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Detailed Installation](#detailed-installation)
3. [Configuration](#configuration)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Production Deployment](#production-deployment)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Backup & Recovery](#backup--recovery)

---

## Quick Start

**Time**: ~15 minutes

```bash
# 1. Clone repository
git clone <repository-url>
cd car-log

# 2. Install Python dependencies
pip install -r mcp-servers/car_log_core/requirements.txt
pip install -r mcp-servers/trip_reconstructor/requirements.txt
pip install -r mcp-servers/validation/requirements.txt
pip install -r mcp-servers/ekasa_api/requirements.txt
pip install -r mcp-servers/dashboard_ocr/requirements.txt
pip install -r mcp-servers/report_generator/requirements.txt

# 3. Install Node.js dependencies
cd mcp-servers/geo-routing && npm install && cd ../..

# 4. Create data directories
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}

# 5. Run tests
pytest tests/ -v
python tests/integration_checkpoint_day7.py

# 6. Configure Claude Desktop (see below)
# 7. Generate demo data
python scripts/generate_mock_data.py --scenario demo

# 8. Test in Claude Desktop!
```

---

## Detailed Installation

### Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version
# Python 3.11.0 or higher required

# Check Node.js version (need 18+)
node --version
# v18.0.0 or higher required

# Check npm
npm --version

# Check if Claude Desktop is installed
# macOS: /Applications/Claude.app
# Linux: ~/.local/share/applications/claude.desktop
# Windows: C:\Program Files\Claude\Claude.exe
```

### Python Environment Setup

**Option 1: System Python** (simple)
```bash
pip install -r requirements.txt  # If you have a combined file
```

**Option 2: Virtual Environment** (recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r mcp-servers/car_log_core/requirements.txt
pip install -r mcp-servers/trip_reconstructor/requirements.txt
pip install -r mcp-servers/validation/requirements.txt
pip install -r mcp-servers/ekasa_api/requirements.txt
pip install -r mcp-servers/dashboard_ocr/requirements.txt
pip install -r mcp-servers/report_generator/requirements.txt
```

**Option 3: Conda** (for data scientists)
```bash
conda create -n carlog python=3.11
conda activate carlog
# Install dependencies as above
```

### Node.js Setup

```bash
cd mcp-servers/geo-routing

# Install dependencies
npm install

# Verify installation
npm list
# Should show: axios, @modelcontextprotocol/sdk, node-cache

# Test the server (optional)
node index.js --version
```

### Data Directory Setup

```bash
# Default location
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}

# OR custom location
export DATA_PATH="/custom/path/to/data"
mkdir -p ${DATA_PATH}/{vehicles,checkpoints,trips,templates,reports}

# Verify structure
ls -la ~/Documents/MileageLog/data/
# Should see: vehicles/ checkpoints/ trips/ templates/ reports/
```

---

## Configuration

### Claude Desktop Configuration

**Step 1: Locate config file**

```bash
# macOS
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Linux
CONFIG_FILE="$HOME/.config/Claude/claude_desktop_config.json"

# Windows (PowerShell)
$CONFIG_FILE="$env:APPDATA\Claude\claude_desktop_config.json"
```

**Step 2: Update paths**

Copy `claude_desktop_config.json` from this repo and update paths:

```json
{
  "mcpServers": {
    "car-log-core": {
      "command": "/absolute/path/to/python",  // Update!
      "args": ["-m", "mcp_servers.car_log_core"],
      "cwd": "/absolute/path/to/car-log/mcp-servers",  // Update!
      "env": {
        "DATA_PATH": "~/Documents/MileageLog/data",
        "USE_ATOMIC_WRITES": "true"
      }
    },
    // ... rest of config
  }
}
```

**Finding Python path**:
```bash
which python  # macOS/Linux
# OR
where python  # Windows
```

**Step 3: Validate JSON**

```bash
# Check for syntax errors
python -m json.tool < "$CONFIG_FILE"
# Should output formatted JSON without errors
```

**Step 4: Restart Claude Desktop**

```bash
# macOS
killall Claude && open -a Claude

# Linux
pkill claude && claude &

# Windows
# Close Claude from system tray, then reopen
```

### Environment Variables

**Required**: None (for P0 features)

**Optional** (P1 features):
```bash
# For dashboard OCR (Claude Vision)
export ANTHROPIC_API_KEY="sk-ant-..."

# Custom data location
export DATA_PATH="/custom/path/to/data"
```

**Making permanent** (add to `~/.bashrc` or `~/.zshrc`):
```bash
echo 'export DATA_PATH="$HOME/Documents/MileageLog/data"' >> ~/.bashrc
source ~/.bashrc
```

---

## Verification

### Test Suite

```bash
# Run all tests
pytest tests/ -v

# Expected output:
# 70 passed, 1 skipped in X.XXs
```

**If tests fail**, see [Troubleshooting](#troubleshooting) section.

### Integration Checkpoint

```bash
python tests/integration_checkpoint_day7.py

# Expected output:
# ✅ GO - All tests passed! Proceed to Days 8-11 integration.
# 📊 TEST SUMMARY
# Total tests:   20
# Passed:        20 ✅
# Failed:        0
# Success rate:  100.0%
```

### Manual Verification

**1. Generate demo data**:
```bash
python scripts/generate_mock_data.py --scenario demo

# Expected output:
# ✨ Demo scenario complete!
# Data location: /home/user/Documents/MileageLog/data
```

**2. Verify data files**:
```bash
ls -la ~/Documents/MileageLog/data/vehicles/
# Should see: <uuid>.json (vehicle file)

ls -la ~/Documents/MileageLog/data/checkpoints/2025-11/
# Should see: <uuid>.json files (checkpoint files)
```

**3. Test in Claude Desktop**:

Start Claude Desktop and ask:
```
You: What MCP tools do you have available?
```

Expected response should include:
- car-log-core tools (create_vehicle, create_checkpoint, etc.)
- trip-reconstructor tools
- validation tools
- ekasa-api tools
- geo-routing tools
- dashboard-ocr tools
- report-generator tools

**If tools not showing**, see [Troubleshooting: Claude Desktop Issues](#claude-desktop-not-discovering-servers).

---

## Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'mcp_servers'

**Symptom**:
```
ModuleNotFoundError: No module named 'mcp_servers'
```

**Solution 1** - Add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/mcp-servers"
```

**Solution 2** - Use absolute paths in config:
```json
{
  "command": "/usr/bin/python3",
  "args": ["-m", "car_log_core"],
  "cwd": "/absolute/path/to/car-log/mcp-servers"
}
```

**Solution 3** - Install as package:
```bash
cd mcp-servers
pip install -e .
```

#### 2. Claude Desktop Not Discovering Servers

**Symptom**: Tools not appearing in Claude Desktop

**Diagnostic steps**:

1. **Check config file location**:
   ```bash
   # macOS
   ls -la "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

   # Linux
   ls -la "$HOME/.config/Claude/claude_desktop_config.json"
   ```

2. **Validate JSON syntax**:
   ```bash
   python -m json.tool < claude_desktop_config.json
   ```

3. **Check Claude Desktop logs**:
   - Open Claude Desktop
   - Settings → Developer → View Logs
   - Look for errors like:
     - "Failed to start MCP server"
     - "Command not found"
     - "Module not found"

4. **Test server manually**:
   ```bash
   python -m mcp_servers.car_log_core
   # Should start without errors
   # Press Ctrl+C to stop
   ```

5. **Check paths are absolute**:
   ```json
   {
     "command": "/usr/bin/python3",  // ABSOLUTE path
     "cwd": "/home/user/car-log/mcp-servers"  // ABSOLUTE path
   }
   ```

6. **Restart Claude Desktop**:
   ```bash
   # Fully quit (not just close window)
   killall Claude && sleep 2 && open -a Claude
   ```

#### 3. Tests Failing

**Symptom**: `pytest tests/ -v` shows failures

**Common causes**:

1. **Missing dependencies**:
   ```bash
   pip install pytest pytest-asyncio
   pip list | grep mcp
   ```

2. **Python version too old**:
   ```bash
   python --version
   # Need 3.11+
   ```

3. **Data directories missing**:
   ```bash
   mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}
   ```

4. **Permissions issue**:
   ```bash
   chmod -R u+w ~/Documents/MileageLog/data
   ```

#### 4. Node.js Server Not Starting

**Symptom**: geo-routing server fails to start

**Solution**:

1. **Check Node version**:
   ```bash
   node --version
   # Need v18.0.0+
   ```

2. **Reinstall dependencies**:
   ```bash
   cd mcp-servers/geo-routing
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Test manually**:
   ```bash
   node index.js
   # Should see: MCP server started
   ```

4. **Check npm permissions** (if EACCES error):
   ```bash
   mkdir ~/.npm-global
   npm config set prefix '~/.npm-global'
   echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```

#### 5. e-Kasa API Timeout

**Symptom**: Receipt fetching times out after 60 seconds

**Expected behavior**: This is normal. Slovak e-Kasa API can take 5-30 seconds.

**If timing out consistently**:

1. **Check internet connection**:
   ```bash
   curl https://ekasa.financnasprava.sk
   ```

2. **Verify receipt ID format**:
   ```
   Valid: O-E182401234567890123456789
   Invalid: 123456 (too short)
   ```

3. **Use mock data for testing**:
   ```bash
   # Don't rely on real API for automated tests
   python scripts/generate_mock_data.py --scenario demo
   ```

#### 6. File Permission Errors

**Symptom**:
```
PermissionError: [Errno 13] Permission denied: '/path/to/data/vehicles/...'
```

**Solution**:
```bash
# Check ownership
ls -la ~/Documents/MileageLog/data/

# Fix permissions
chmod -R u+rw ~/Documents/MileageLog/data/

# If directory doesn't exist
mkdir -p ~/Documents/MileageLog/data/{vehicles,checkpoints,trips,templates,reports}
```

#### 7. Atomic Write Failures

**Symptom**: Files appear as `.tmp` but not renamed

**Causes**:
- File system doesn't support atomic rename
- Disk full
- Permissions issue

**Solution**:
```bash
# Check disk space
df -h ~/Documents/MileageLog/data

# Clean up temp files
find ~/Documents/MileageLog/data -name "*.tmp" -delete

# Test atomic write
python -c "
from pathlib import Path
import tempfile
p = Path('~/Documents/MileageLog/data/test.json').expanduser()
with tempfile.NamedTemporaryFile(mode='w', dir=p.parent, delete=False) as f:
    f.write('{\"test\": true}')
    temp = Path(f.name)
temp.replace(p)
print(f'Success: {p.exists()}')
"
```

#### 8. Slovak Character Encoding Issues

**Symptom**: Slovak characters (á, č, š, ž) display incorrectly

**Solution**:

1. **Ensure UTF-8 encoding**:
   ```bash
   export LC_ALL=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

2. **Check Python encoding**:
   ```python
   import sys
   print(sys.getdefaultencoding())  # Should be 'utf-8'
   ```

3. **Verify JSON files**:
   ```bash
   file ~/Documents/MileageLog/data/vehicles/*.json
   # Should say: UTF-8 Unicode text
   ```

---

## Production Deployment

### Deployment Checklist

- [ ] All tests passing (70+)
- [ ] Integration checkpoint passing (20/20)
- [ ] Environment variables configured
- [ ] Data directory created and permissions set
- [ ] Claude Desktop configured with absolute paths
- [ ] Backup strategy in place
- [ ] Monitoring configured (optional)
- [ ] User training completed

### Environment Setup

**Production environment variables**:
```bash
# /etc/environment or ~/.profile
export DATA_PATH="/var/lib/carlog/data"
export PYTHONPATH="/opt/carlog/mcp-servers:$PYTHONPATH"
export LOG_LEVEL="INFO"  # DEBUG for troubleshooting
```

**Data directory location**:
```bash
# Production
DATA_PATH="/var/lib/carlog/data"

# Development
DATA_PATH="~/Documents/MileageLog/data"

# Testing
DATA_PATH="/tmp/carlog-test-data"
```

### Security Hardening

1. **File permissions**:
   ```bash
   chmod 700 /var/lib/carlog/data
   chmod 600 /var/lib/carlog/data/*/*.json
   ```

2. **API key protection**:
   ```bash
   # Store in secure location
   echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/.carlog.env
   chmod 600 ~/.carlog.env
   source ~/.carlog.env
   ```

3. **Network isolation**:
   - MCP servers run locally (no network exposure)
   - Only external API calls: e-Kasa, OpenStreetMap

### Performance Optimization

1. **Enable caching** (geo-routing):
   ```json
   {
     "env": {
       "CACHE_TTL_HOURS": "24"
     }
   }
   ```

2. **Batch operations**:
   ```python
   # Instead of creating trips one-by-one
   # Use batch create (if implemented)
   car_log_core.create_trips_batch(trips)
   ```

3. **Index files** (for large datasets):
   ```bash
   # Create index.json in monthly folders
   # Lists all trips for faster filtering
   data/trips/2025-11/index.json
   ```

---

## Monitoring & Maintenance

### Logging

**Enable debug logging**:
```bash
export LOG_LEVEL="DEBUG"
python -m mcp_servers.car_log_core
```

**Log locations**:
- Claude Desktop logs: Settings → Developer → View Logs
- Python logs: stdout/stderr
- Node logs: stdout/stderr

**Structured logging** (optional):
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Checks

**Quick health check script**:
```bash
#!/bin/bash
# health_check.sh

echo "🏥 Car Log Health Check"
echo "======================"

# 1. Check data directory
if [ -d ~/Documents/MileageLog/data ]; then
    echo "✅ Data directory exists"
else
    echo "❌ Data directory missing"
    exit 1
fi

# 2. Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# 3. Check Node version
NODE_VERSION=$(node --version)
echo "Node version: $NODE_VERSION"

# 4. Run quick test
pytest tests/test_validation.py -q
if [ $? -eq 0 ]; then
    echo "✅ Tests passing"
else
    echo "❌ Tests failing"
    exit 1
fi

echo "✅ All health checks passed!"
```

### Maintenance Tasks

**Weekly**:
- Review logs for errors
- Check disk space (`df -h`)
- Verify backups

**Monthly**:
- Run full test suite
- Review performance metrics
- Clean up old temp files

**Quarterly**:
- Update dependencies (`pip list --outdated`)
- Review and archive old data
- Security audit

---

## Backup & Recovery

### Backup Strategy

**Simple backup** (for small datasets):
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/carlog/$(date +%Y-%m-%d)"
DATA_DIR=~/Documents/MileageLog/data

mkdir -p $BACKUP_DIR
cp -r $DATA_DIR $BACKUP_DIR/

echo "✅ Backup complete: $BACKUP_DIR"
```

**Automated backup** (cron job):
```bash
# Add to crontab (crontab -e)
0 2 * * * /path/to/backup.sh  # Daily at 2 AM
```

**Incremental backup** (rsync):
```bash
rsync -av --delete ~/Documents/MileageLog/data/ /backup/carlog/data/
```

### Recovery

**Restore from backup**:
```bash
# 1. Stop Claude Desktop
killall Claude

# 2. Restore data
cp -r /backup/carlog/2025-11-18/data ~/Documents/MileageLog/

# 3. Verify permissions
chmod -R u+rw ~/Documents/MileageLog/data

# 4. Restart Claude Desktop
open -a Claude

# 5. Verify data
# In Claude: "List my vehicles"
```

**Disaster recovery**:
1. Reinstall Claude Desktop
2. Reinstall dependencies (pip, npm)
3. Restore config file (`claude_desktop_config.json`)
4. Restore data directory
5. Run verification tests

---

## Support

### Getting Help

1. **Check this guide** (you're here!)
2. **Review CLAUDE.md** (implementation details)
3. **Check ARCHITECTURE.md** (system design)
4. **Review spec/** (detailed specifications)
5. **Check GitHub issues** (if public repo)

### Reporting Issues

When reporting issues, include:

1. **Environment**:
   ```bash
   python --version
   node --version
   uname -a  # OS version
   ```

2. **Error message**:
   - Full stack trace
   - Claude Desktop logs
   - Relevant screenshots

3. **Steps to reproduce**:
   - What you did
   - What you expected
   - What actually happened

4. **Relevant files**:
   - `claude_desktop_config.json` (redact sensitive data)
   - Test output
   - Sample data files

---

## Quick Reference

### Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run integration checkpoint
python tests/integration_checkpoint_day7.py

# Generate demo data
python scripts/generate_mock_data.py --scenario demo

# Start server manually
python -m mcp_servers.car_log_core

# Check config
python -m json.tool < claude_desktop_config.json

# Backup data
cp -r ~/Documents/MileageLog/data /backup/location

# View logs (Claude Desktop)
# Settings → Developer → View Logs
```

### File Locations

```
Config:
  macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
  Linux: ~/.config/Claude/claude_desktop_config.json
  Windows: %APPDATA%\Claude\claude_desktop_config.json

Data:
  Default: ~/Documents/MileageLog/data/
  Custom: $DATA_PATH

Logs:
  Claude Desktop: Settings → Developer → View Logs
  Tests: pytest output (stdout)
```

---

**Deployment Guide Version:** 1.0
**Last Updated:** 2025-11-18
**Status:** Production-Ready ✅
