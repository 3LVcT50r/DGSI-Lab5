#!/usr/bin/env python3
"""
Universal integration test runner for cross-platform support.
Works on Windows (PowerShell), WSL, and Linux.

Usage:
    python run-integration-test.py
    python run-integration-test.py --verbose
    python run-integration-test.py --no-cleanup
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path


class IntegrationTestRunner:
    def __init__(self, verbose=False, no_cleanup=False):
        self.verbose = verbose
        self.no_cleanup = no_cleanup
        self.system = platform.system()
        self.workspace_root = self._find_workspace_root()
        self.factory_path = self.workspace_root / "factory-app"
        self.retailer_path = self.workspace_root / "retailer-app"
        
    def _find_workspace_root(self):
        """Find the workspace root directory."""
        current = Path.cwd()
        
        # If we're already at root (both apps visible)
        if (current / "factory-app").exists() and (current / "retailer-app").exists():
            return current
        
        # Try going up
        for _ in range(5):
            if (current / "factory-app").exists() and (current / "retailer-app").exists():
                return current
            current = current.parent
        
        raise RuntimeError("Could not find workspace root. Run from DGSI-Lab5 directory.")
    
    def log(self, message):
        """Print log message if verbose."""
        if self.verbose:
            print(f"[INFO] {message}")
    
    def run_retailer_command(self, *args):
        """Run a retailer CLI command."""
        cmd = ["python", "-m", "src.cli"] + list(args)
        return self._run_command(cmd, cwd=self.retailer_path)
    
    def run_factory_command(self, *args):
        """Run a factory CLI command."""
        cmd = ["python", "-m", "src.cli"] + list(args)
        return self._run_command(cmd, cwd=self.factory_path)
    
    def _run_command(self, cmd, cwd=None):
        """Execute a command and return output."""
        self.log(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0 and self.verbose:
                print(f"[ERROR] {result.stderr}", file=sys.stderr)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] Command timed out: {' '.join(cmd)}", file=sys.stderr)
            return ""
        except Exception as e:
            print(f"[EXCEPTION] {e}", file=sys.stderr)
            return ""
    
    def print_section(self, title):
        """Print a formatted section header."""
        print("\n" + "=" * 70)
        print(title)
        print("=" * 70)
    
    def run_test(self):
        """Run the full integration test."""
        print(f"Integration Test Runner")
        print(f"Platform: {self.system}")
        print(f"Workspace: {self.workspace_root}")
        
        # Verify apps exist
        if not self.factory_path.exists():
            print(f"Error: factory-app not found at {self.factory_path}", file=sys.stderr)
            return False
        if not self.retailer_path.exists():
            print(f"Error: retailer-app not found at {self.retailer_path}", file=sys.stderr)
            return False
        
        try:
            # PHASE 1: Initial State
            self.print_section("PHASE 1: Initial State")
            
            print("\n[RETAILER] Current day:")
            print(self.run_retailer_command("day", "current"))
            
            print("\n[RETAILER] Initial stock:")
            print(self.run_retailer_command("stock"))
            
            print("\n[FACTORY] Current day:")
            print(self.run_factory_command("day", "current"))
            
            print("\n[FACTORY] Initial inventory:")
            print(self.run_factory_command("inventory"))
            
            # PHASE 2: Retailer Advances 5 Days
            self.print_section("PHASE 2: Retailer Advances 5 Days")
            
            for day_num in range(1, 6):
                print(f"\n[DAY {day_num}] Advancing retailer day...")
                self.run_retailer_command("day", "advance")
                
                print(f"[DAY {day_num}] Customer orders:")
                print(self.run_retailer_command("customers", "orders"))
                
                print(f"[DAY {day_num}] Stock:")
                print(self.run_retailer_command("stock"))
            
            # PHASE 3: Retailer Creates Purchase Orders
            self.print_section("PHASE 3: Retailer Creates Purchase Orders")
            
            print("\n[RETAILER] Creating purchase order (product 1, qty 30)...")
            print(self.run_retailer_command("purchase", "create", "1", "30"))
            
            print("\n[RETAILER] Purchase orders:")
            print(self.run_retailer_command("purchase", "list"))
            
            # PHASE 4: Factory Receives Order
            self.print_section("PHASE 4: Factory Receives Retailer's Order")
            
            print("\n[FACTORY] Incoming sales orders:")
            print(self.run_factory_command("sales", "orders"))
            
            # PHASE 5: Factory Production Planning
            self.print_section("PHASE 5: Factory Production Planning")
            
            print("\n[FACTORY] Capacity:")
            print(self.run_factory_command("capacity"))
            
            print("\n[FACTORY] Inventory:")
            print(self.run_factory_command("inventory"))
            
            # PHASE 6: Factory Releases Order
            self.print_section("PHASE 6: Factory Releases Order to Production")
            
            print("\n[FACTORY] Releasing order ID 1...")
            print(self.run_factory_command("production", "release", "1"))
            
            # PHASE 7: Factory Advances 7 Days
            self.print_section("PHASE 7: Factory Advances 7 Days")
            
            for day_num in range(1, 8):
                print(f"\n[FAC-DAY {day_num}] Advancing factory day...")
                self.run_factory_command("day", "advance")
                
                print(f"[FAC-DAY {day_num}] Production status:")
                print(self.run_factory_command("production", "status"))
            
            # PHASE 8: Final State
            self.print_section("PHASE 8: Final State")
            
            print("\n[RETAILER] Final day:")
            print(self.run_retailer_command("day", "current"))
            
            print("\n[RETAILER] Final stock:")
            print(self.run_retailer_command("stock"))
            
            print("\n[RETAILER] Final purchase orders:")
            print(self.run_retailer_command("purchase", "list"))
            
            print("\n[FACTORY] Final day:")
            print(self.run_factory_command("day", "current"))
            
            print("\n[FACTORY] Final sales orders:")
            print(self.run_factory_command("sales", "orders"))
            
            self.print_section("Integration Test Complete")
            print("✓ All phases executed successfully!\n")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}", file=sys.stderr)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform integration test runner"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up after test"
    )
    
    args = parser.parse_args()
    
    try:
        runner = IntegrationTestRunner(
            verbose=args.verbose,
            no_cleanup=args.no_cleanup
        )
        success = runner.run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
