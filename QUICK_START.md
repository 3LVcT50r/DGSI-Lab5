#!/usr/bin/env python3
"""
Quick start guide for the integration test suite.

This file documents all available test runners and how to use them.
"""

# ============================================================================
# QUICK START SUMMARY
# ============================================================================
# 
# The DGSI-Lab5 project includes THREE ways to run the integration test:
#
# 1. PowerShell Script (Windows, native)       → integration-test.ps1
# 2. Bash Script (Linux, WSL, macOS)           → integration-test.sh
# 3. Python Runner (All platforms, unified)    → run-integration-test.py
#
# Choose based on your platform and preference.

# ============================================================================
# OPTION 1: Windows PowerShell (Recommended for Windows Users)
# ============================================================================
#
# Location: integration-test.ps1
# Usage:
#   cd C:\path\to\DGSI-Lab5
#   .\integration-test.ps1
#
# Requirements:
#   - Python 3.10+ with FastAPI installed
#   - PowerShell 5.1 or higher (Windows 10+, or PowerShell Core)
#   - Both apps running (factory on :8000, retailer on :8001)
#
# Advantages:
#   ✓ Native Windows support
#   ✓ ColorizedPowerShell output
#   ✓ Direct integration with Windows ecosystem
#
# Disadvantages:
#   ✗ Windows only
#   ✗ Requires execution policy configuration if restrictive

# ============================================================================
# OPTION 2: Bash Script (Recommended for Linux/WSL/macOS)
# ============================================================================
#
# Location: integration-test.sh
# Usage:
#   cd /path/to/DGSI-Lab5
#   chmod +x integration-test.sh
#   ./integration-test.sh
#
# Requirements:
#   - Bash 4.0+
#   - Python 3.10+ with FastAPI installed
#   - Both apps running (factory on :8000, retailer on :8001)
#
# Advantages:
#   ✓ Works on Linux, WSL, macOS, FreeBSD
#   ✓ Standard Unix conventions
#   ✓ Easy to integrate into CI/CD pipelines
#
# Disadvantages:
#   ✗ Not native on Windows (use WSL or Python runner instead)

# ============================================================================
# OPTION 3: Python Runner (Recommended for All Platforms)
# ============================================================================
#
# Location: run-integration-test.py
# Usage:
#   # From workspace root, any platform
#   python run-integration-test.py
#   python run-integration-test.py --verbose
#   python3 run-integration-test.py
#
# Requirements:
#   - Python 3.6+ (works with any version)
#   - Both apps running (factory on :8000, retailer on :8001)
#
# Advantages:
#   ✓ Works on Windows, Linux, WSL, macOS
#   ✓ Auto-detects workspace location
#   ✓ Built-in error handling and logging
#   ✓ Platform-agnostic approach
#   ✓ Best for CI/CD and cross-platform testing
#
# Disadvantages:
#   ✗ Less fancy output (text only)

# ============================================================================
# STEP-BY-STEP: Running Your First Integration Test
# ============================================================================
#
# 1. START THE APPS
#    ═════════════════════════════════════════════════════════════════════
#
#    Choose your method based on platform:
#
#    A. Windows PowerShell (Two terminals):
#       Terminal 1:  cd factory-app && python src/cli.py serve --port 8000
#       Terminal 2:  cd retailer-app && python -m src.cli serve --port 8001
#
#    B. Linux/WSL/macOS (Two terminals or tmux):
#       Terminal 1:  cd factory-app && python -m src.cli serve --port 8000
#       Terminal 2:  cd retailer-app && python -m src.cli serve --port 8001
#
#       OR with tmux in one command:
#       tmux new-session -d -s lab5 "cd factory-app && python -m src.cli serve --port 8000" \; \
#            send-keys -t lab5 "tmux split-window -h" Enter \; \
#            send-keys -t lab5 "cd retailer-app && python -m src.cli serve --port 8001" Enter
#
# 2. VERIFY BOTH APPS ARE RUNNING
#    ═════════════════════════════════════════════════════════════════════
#
#    # Test factory app
#    curl http://localhost:8000/health
#
#    # Test retailer app
#    curl http://localhost:8001/health
#
#    Both should return: {"status":"ok"}
#
# 3. RUN THE TEST (Choose one method)
#    ═════════════════════════════════════════════════════════════════════
#
#    A. Windows PowerShell:
#       cd C:\path\to\DGSI-Lab5
#       .\integration-test.ps1
#
#    B. Linux/WSL/macOS:
#       cd /path/to/DGSI-Lab5
#       ./integration-test.sh
#
#    C. Any Platform (Recommended):
#       cd /path/to/DGSI-Lab5
#       python run-integration-test.py
#
# 4. OBSERVE THE OUTPUT
#    ═════════════════════════════════════════════════════════════════════
#
#    The test will run through 8 phases:
#    - Phase 1: Initial state
#    - Phase 2: Retailer generates 5 days of customer demand
#    - Phase 3: Retailer creates purchase order to factory
#    - Phase 4: Factory receives the order as a "sales order"
#    - Phase 5: Factory checks capacity and resources
#    - Phase 6: Factory releases order to production
#    - Phase 7: Factory produces goods over 7 days
#    - Phase 8: Final state after production complete
#
#    Look for:
#    ✓ Retailer inventory depleting then replenishing
#    ✓ Sales orders appearing in factory system
#    ✓ Production status changing from pending→released→in_progress→completed
#    ✓ Factory inventory changing as materials consumed and goods produced

# ============================================================================
# PLATFORM SELECTION GUIDE
# ============================================================================
#
# Platform          | Recommended      | Also Works           | Avoid
# ─────────────────────────────────────────────────────────────────────────
# Windows 10/11     | PowerShell       | Python runner        | Bash (use WSL)
# WSL Ubuntu        | Bash or Python   | Python runner        | PowerShell
# Linux             | Bash             | Python runner        | PowerShell
# macOS             | Bash             | Python runner        | PowerShell
# CI/CD Pipeline    | Python runner    | Bash (if Unix)       | PowerShell
#
# ─────────────────────────────────────────────────────────────────────────
# General Rule: 
#   - If you're on Windows and comfortable with PowerShell → use .ps1
#   - If you're on Linux/WSL/macOS → use .sh
#   - If you want something that works everywhere → use .py

# ============================================================================
# ADVANCED OPTIONS
# ============================================================================
#
# Run the Python runner with verbose output:
#   python run-integration-test.py --verbose
#
# Run the Bash script with error tracing:
#   bash -x integration-test.sh
#
# Run the PowerShell script with detailed output:
#   .\integration-test.ps1 -Verbose
#
# Use custom ports (edit the script files to change 8000/8001):
#   # In integration-test.ps1, retailer-app, or factory-app, modify:
#   # $RETAILER_PORT = 8001
#   # $FACTORY_PORT = 8000

# ============================================================================
# TROUBLESHOOTING
# ============================================================================
#
# Q: "ModuleNotFoundError: No module named 'src'"
# A: You're running from the wrong directory. The test runner should handle
#    this, but if not, make sure:
#    - You're in the DGSI-Lab5 root directory
#    - Both factory-app/ and retailer-app/ are visible
#    - Try the Python runner: python run-integration-test.py
#
# Q: "Connection refused" / Apps not responding
# A: Check if both apps are running:
#    - curl http://localhost:8000/health
#    - curl http://localhost:8001/health
#    If either fails, start the apps again in separate terminals
#
# Q: Bash script says "command not found"
# A: Make sure the script is executable:
#    - chmod +x integration-test.sh
#    - Then run: ./integration-test.sh
#
# Q: PowerShell says "execution policy" error
# A: Run once:
#    - Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#    Then try again
#
# Q: Still having issues?
# A: Use the Python runner as a fallback:
#    - python run-integration-test.py --verbose
#    This has the best error messages and works everywhere

# ============================================================================
# FILES INCLUDED IN THIS TEST SUITE
# ============================================================================
#
# integration-test.ps1      - PowerShell test runner (Windows native)
# integration-test.sh       - Bash test runner (Unix/Linux/WSL/macOS)
# run-integration-test.py   - Python test runner (All platforms, recommended)
# INTEGRATION_TEST.md       - Full documentation with detailed walkthrough
# QUICK_START.md           - This file (quick reference)

# ============================================================================
# NEXT STEPS
# ============================================================================
#
# After running the test successfully:
#
# 1. Experiment with manual CLI commands (see INTEGRATION_TEST.md)
# 2. Try different order quantities and observe effects
# 3. Test edge cases: backorders, stockouts, capacity limits
# 4. Export and analyze event logs
# 5. Run the test multiple times to observe stochastic behavior
#
# For full documentation, see: INTEGRATION_TEST.md
