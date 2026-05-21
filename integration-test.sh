#!/bin/bash

# Integration test: Retailer → Manufacturer flow
# Supports: Linux, WSL, macOS
# Prerequisites: Both apps running on ports 8000 (factory) and 8001 (retailer)

set -e  # Exit on error

# Configuration
FACTORY_CLI_PATH="$HOME/path/to/factory-app"  # Update this
RETAILER_CLI_PATH="$HOME/path/to/retailer-app"  # Update this

# Try to auto-detect workspace
if [ -d "./factory-app" ]; then
    FACTORY_CLI_PATH="./factory-app"
    RETAILER_CLI_PATH="./retailer-app"
elif [ -d "../factory-app" ]; then
    FACTORY_CLI_PATH="../factory-app"
    RETAILER_CLI_PATH="../retailer-app"
fi

function invoke_retailer_cli() {
    (cd "$RETAILER_CLI_PATH" && python -m src.cli "$@")
}

function invoke_factory_cli() {
    (cd "$FACTORY_CLI_PATH" && python -m src.cli "$@")
}

function print_section() {
    local title="$1"
    echo ""
    echo "================================================================"
    echo "$title"
    echo "================================================================"
}

# =============================================================================
# PHASE 1: Initial State
# =============================================================================
print_section "PHASE 1: Initial State"

echo -e "\n[RETAILER] Current day:"
invoke_retailer_cli day current

echo -e "\n[RETAILER] Initial stock:"
invoke_retailer_cli stock

echo -e "\n[RETAILER] Catalog:"
invoke_retailer_cli catalog

echo -e "\n[FACTORY] Current day:"
#invoke_factory_cli day current

echo -e "\n[FACTORY] Initial inventory:"
invoke_factory_cli inventory

# =============================================================================
# PHASE 2: Retailer Advances 5 Days (Generates Customer Demand)
# =============================================================================
print_section "PHASE 2: Retailer Advances 5 Days (Customer Demand)"

for i in {1..5}; do
    echo -e "\n[DAY $i] Advancing retailer day..." 
    invoke_retailer_cli day advance
    
    echo -e "\n[DAY $i] Customer orders:"
    invoke_retailer_cli customers orders
    
    echo -e "\n[DAY $i] Retailer stock after day advance:"
    invoke_retailer_cli stock
    
    sleep 0.3
done

# =============================================================================
# PHASE 3: Retailer Creates Purchase Orders to Factory
# =============================================================================
print_section "PHASE 3: Retailer Creates Purchase Orders to Factory"

echo -e "\n[RETAILER] Current stock before purchase order:"
invoke_retailer_cli stock

echo -e "\n[RETAILER] Current purchase orders (before new request):"
invoke_retailer_cli purchase list

echo -e "\n[RETAILER] Creating purchase order to factory (product 1, qty 30)..."
invoke_retailer_cli purchase create 1 30

echo -e "\n[RETAILER] Updated purchase orders:"
invoke_retailer_cli purchase list

# =============================================================================
# PHASE 4: Factory Receives Retailer's Purchase Order (via API)
# =============================================================================
print_section "PHASE 4: Factory Receives Retailer's Order"

echo -e "\n[FACTORY] Checking incoming sales orders from retailers:"
invoke_factory_cli sales orders

# =============================================================================
# PHASE 5: Factory Production Planning
# =============================================================================
print_section "PHASE 5: Factory Production Planning & Capacity"

echo -e "\n[FACTORY] Check production capacity:"
invoke_factory_cli capacity

echo -e "\n[FACTORY] Current inventory (raw materials and finished goods):"
invoke_factory_cli inventory

# =============================================================================
# PHASE 6: Factory Releases Sales Order to Production
# =============================================================================
print_section "PHASE 6: Factory Releases Order to Production"

echo -e "\n[FACTORY] Listing sales orders before release:"
invoke_factory_cli sales orders

echo -e "\n[FACTORY] Releasing first sales order to production (order ID 1)..."
invoke_factory_cli production release 1

# =============================================================================
# PHASE 7: Factory Advances 7 Days (Production + Fulfillment)
# =============================================================================
print_section "PHASE 7: Factory Advances 7 Days"

for i in {1..7}; do
    echo -e "\n[FAC-DAY $i] Advancing factory day..."
    invoke_factory_cli day advance
    
    echo "[FAC-DAY $i] Production status:"
    invoke_factory_cli production status
    
    echo "[FAC-DAY $i] Factory inventory after production:"
    invoke_factory_cli inventory
    
    sleep 0.3
done

# =============================================================================
# PHASE 8: Final State Comparison
# =============================================================================
print_section "PHASE 8: Final State"

echo -e "\n[RETAILER] Final day:"
invoke_retailer_cli day current

echo -e "\n[RETAILER] Final stock:"
invoke_retailer_cli stock

echo -e "\n[RETAILER] Final purchase orders:"
invoke_retailer_cli purchase list

echo -e "\n[RETAILER] Final customer orders:"
invoke_retailer_cli customers orders

echo -e "\n[FACTORY] Final day:"
invoke_factory_cli day current

echo -e "\n[FACTORY] Final inventory:"
invoke_factory_cli inventory

echo -e "\n[FACTORY] Final sales orders:"
invoke_factory_cli sales orders

echo -e "\n[FACTORY] Final production status:"
invoke_factory_cli production status

print_section "Integration Test Complete"
echo "✓ All phases executed successfully!"
echo ""
