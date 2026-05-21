import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import os

def create_inventory_chart():
    # Read metrics
    if os.path.exists("retailer-app/retailer_metrics.csv") and os.path.getsize("retailer-app/retailer_metrics.csv") > 0:
        ret_df = pd.read_csv("retailer-app/retailer_metrics.csv")
        plt.figure(figsize=(10, 6))
        plt.plot(ret_df['day'], ret_df['printer_stock'], label='Retailer Printer Stock', color='blue')
        plt.plot(ret_df['day'], ret_df['backordered'], label='Backordered Demand', color='red', linestyle='--')
        plt.title('Inventory vs Unfulfilled Demand over Time')
        plt.xlabel('Simulation Day')
        plt.ylabel('Quantity')
        plt.legend()
        plt.grid(True)
        plt.savefig('inventory_vs_demand.png')
        plt.close()
        print("Generated inventory_vs_demand.png")

def create_pricing_chart():
    # Read pricing from events table
    conn = sqlite3.connect("retailer-app/data/retailer.sqlite")
    query = "SELECT sim_day, detail FROM events WHERE event_type = 'price_changed'"
    try:
        events_df = pd.read_sql_query(query, conn)
        # We can extract the price from the detail string: "Retail price for P3D-Classic set to 299.99"
        if not events_df.empty:
            events_df['price'] = events_df['detail'].str.extract(r'set to ([\d.]+)').astype(float)
            events_df['product'] = events_df['detail'].str.extract(r'for ([\w-]+) set')
            
            plt.figure(figsize=(10, 6))
            for prod in events_df['product'].unique():
                prod_df = events_df[events_df['product'] == prod]
                plt.plot(prod_df['sim_day'], prod_df['price'], marker='o', label=f'{prod} Price')
                
            plt.title('Pricing Changes over Time')
            plt.xlabel('Simulation Day')
            plt.ylabel('Price ($)')
            plt.legend()
            plt.grid(True)
            plt.savefig('pricing_changes.png')
            plt.close()
            print("Generated pricing_changes.png")
        else:
            print("No pricing changes found to plot.")
    except Exception as e:
        print(f"Error generating pricing chart: {e}")
    finally:
        conn.close()

def create_latency_chart():
    conn = sqlite3.connect("retailer-app/data/retailer.sqlite")
    query = "SELECT created_day, fulfilled_day FROM customer_orders WHERE status = 'fulfilled'"
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            df['latency'] = df['fulfilled_day'] - df['created_day']
            avg_latency = df.groupby('created_day')['latency'].mean().reset_index()
            
            plt.figure(figsize=(10, 6))
            plt.plot(avg_latency['created_day'], avg_latency['latency'], marker='s', color='green')
            plt.title('Average Order Fulfillment Latency over Time')
            plt.xlabel('Order Creation Day')
            plt.ylabel('Latency (Days)')
            plt.grid(True)
            plt.savefig('fulfillment_latency.png')
            plt.close()
            print("Generated fulfillment_latency.png")
        else:
            print("No fulfilled orders found to plot.")
    except Exception as e:
        print(f"Error generating latency chart: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("Generating simulation charts...")
    create_inventory_chart()
    create_pricing_chart()
    create_latency_chart()
    print("Done.")
