import sys
import json
import logging
import subprocess
import httpx
import os
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_cmd(cmd):
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def run_provider(context, url):
    try:
        run_cmd(["bash", "../provider-cli", "restock", "4", "200"])
        run_cmd(["bash", "../provider-cli", "restock", "5", "200"])
        logger.info("Provider completed turn via CLI mock.")
        
        # Log metrics
        try:
            day = context.get("day", 0)
            stock = httpx.get(f"{url}/api/v1/stock").json()
            orders = httpx.get(f"{url}/api/v1/orders").json()
            with open("provider_metrics.csv", "a", newline="") as f:
                writer = csv.writer(f)
                if os.path.getsize("provider_metrics.csv") == 0:
                    writer.writerow(["day", "stock_qty", "pending_orders"])
                total_stock = sum(s["quantity"] for s in stock)
                pending = len([o for o in orders if o["status"] == "pending"])
                writer.writerow([day, total_stock, pending])
        except Exception as e:
            logger.error(f"Provider metrics failed: {e}")
            
    except Exception as e:
        logger.error(f"Provider failed: {e}")

def run_manufacturer(context, url):
    try:
        run_cmd(["bash", "../manufacturer-cli", "purchase", "create", "--supplier", "ChipSupply Co", "--product", "1", "--qty", "50"])
        run_cmd(["bash", "../manufacturer-cli", "purchase", "create", "--supplier", "ChipSupply Co", "--product", "2", "--qty", "50"])
        run_cmd(["bash", "../manufacturer-cli", "purchase", "create", "--supplier", "ChipSupply Co", "--product", "3", "--qty", "50"])
        logger.info("Manufacturer completed turn via CLI mock.")
        
        # Log metrics
        try:
            day = context.get("day", 0)
            stock = httpx.get(f"{url}/api/v1/inventory").json()
            orders = httpx.get(f"{url}/api/v1/sales-orders").json()
            with open("manufacturer_metrics.csv", "a", newline="") as f:
                writer = csv.writer(f)
                if os.path.getsize("manufacturer_metrics.csv") == 0:
                    writer.writerow(["day", "parts_stock", "printer_stock", "pending_orders"])
                parts = sum(s["quantity"] for s in stock if s.get("product_type", "raw_material") == "raw_material")
                printers = sum(s["quantity"] for s in stock if s.get("product_type", "") == "finished_good")
                pending = len([o for o in orders if o["status"] == "pending"])
                writer.writerow([day, parts, printers, pending])
        except Exception as e:
            logger.error(f"Manufacturer metrics failed: {e}")
    except Exception as e:
        logger.error(f"Manufacturer failed: {e}")

def run_retailer(context, url):
    try:
        # Auto fulfill via CLI
        orders = httpx.get(f"{url}/api/v1/orders").json()
        for order in orders:
            if order["status"] == "pending":
                run_cmd(["bash", "../retailer-cli", "fulfill", str(order["id"])])
        
        run_cmd(["bash", "../retailer-cli", "purchase", "create", "P3D-Classic", "10"])
        run_cmd(["bash", "../retailer-cli", "purchase", "create", "P3D-Pro", "5"])
        logger.info("Retailer completed turn via CLI mock.")
        
        # Log metrics
        try:
            day = context.get("day", 0)
            stock = httpx.get(f"{url}/api/v1/stock").json()
            orders = httpx.get(f"{url}/api/v1/orders").json()
            with open("retailer_metrics.csv", "a", newline="") as f:
                writer = csv.writer(f)
                if os.path.getsize("retailer_metrics.csv") == 0:
                    writer.writerow(["day", "printer_stock", "fulfilled_orders", "backordered"])
                total_stock = sum(s["quantity_available"] for s in stock)
                fulfilled = len([o for o in orders if o["status"] == "fulfilled"])
                backordered = len([o for o in orders if o["status"] == "backordered"])
                writer.writerow([day, total_stock, fulfilled, backordered])
        except Exception as e:
            logger.error(f"Retailer metrics failed: {e}")
    except Exception as e:
        logger.error(f"Retailer failed: {e}")

def main():
    if len(sys.argv) < 4:
        sys.exit(1)
    
    role = sys.argv[1]
    # argv[2] is app_working_dir, but we are already running inside it due to cwd in subprocess
    context = json.loads(sys.argv[3])
    
    if role.startswith("provider"):
        run_provider(context, sys.argv[2])
    elif role.startswith("manufacturer"):
        run_manufacturer(context, sys.argv[2])
    elif role.startswith("retailer"):
        run_retailer(context, sys.argv[2])

if __name__ == "__main__":
    main()
