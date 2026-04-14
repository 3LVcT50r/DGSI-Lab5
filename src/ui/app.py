import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="3D Printer Factory Simulator", layout="wide")

def fetch_data(endpoint: str):
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return None

def post_data(endpoint: str, json_data=None):
    try:
        response = requests.post(f"{API_URL}/{endpoint}", json=json_data)
        response.raise_for_status()
        st.success(f"Success: {endpoint}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = e.response.json().get("detail", str(e))
        st.error(f"Error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def refresh():
    st.rerun()

st.title("🏭 3D Printer Factory Simulation")

# Fetch overall status
status = fetch_data("simulate/status")

if status is None:
    st.warning("Cannot connect to backend. Is FastAPI running on port 8000?")
    st.stop()

current_day = status.get("current_day", 0)

# Sidebar Controls
st.sidebar.header(f"📅 Day: {current_day}")

if st.sidebar.button("▶️ Advance Day"):
    post_data("simulate/advance")
    refresh()

if st.sidebar.button("🔄 Reset Simulation"):
    post_data("simulate/reset")
    refresh()

st.sidebar.markdown("---")
st.sidebar.header("Purchasing")

suppliers = fetch_data("suppliers")
products_list = fetch_data("inventory")  # to get product names, but let's fetch BOM instead
# Better yet, the suppliers endpoint has products we can just look up.
if suppliers:
    supp_options = {s["name"]: s["id"] for s in suppliers}
    selected_supp_name = st.sidebar.selectbox("Supplier", list(supp_options.keys()))
    selected_supp_id = supp_options[selected_supp_name]
    
    # Filter products for selected supplier
    supp_products = [s for s in suppliers if s["id"] == selected_supp_id]
    
    # Since we lack a direct product lookup, we will just use the product_id of the supplier
    # A single supplier object in our model represents 1 product offering.
    # Wait, our Supplier model has product_id. Let's group them by name in UI if they have same name
    
    # Let's rebuild supp_options as unique supplier names
    unique_supp_names = list(set([s["name"] for s in suppliers]))
    selected_supp_name = st.sidebar.selectbox("Supplier Name", unique_supp_names)
    
    # Get products for this supplier name
    supp_items = [s for s in suppliers if s["name"] == selected_supp_name]
    
    item_options = {f"Prod ID: {s['product_id']} (${s['unit_cost']})": s for s in supp_items}
    selected_item_label = st.sidebar.selectbox("Product", list(item_options.keys()))
    selected_item = item_options[selected_item_label]
    
    min_qty = selected_item.get("min_order_qty", 1)
    qty = st.sidebar.number_input("Quantity", min_value=min_qty, value=min_qty, step=1)
    
    if st.sidebar.button("Issue PO"):
        post_data("purchase-orders", {
            "supplier_id": selected_item["id"],
            "product_id": selected_item["product_id"],
            "quantity": qty
        })
        refresh()

# --- Main Layout ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Pending Manufacturing Orders")
    pending_orders = status.get("pending_orders", [])
    if pending_orders:
        df_orders = pd.DataFrame(pending_orders)
        
        # Display selected orders for manual release
        selected_order_id = st.selectbox("Select Pending Order to Release Manually", df_orders["id"].tolist())
        if st.button("Release Selected Order"):
            post_data(f"orders/{selected_order_id}/release")
            refresh()
            
        st.dataframe(df_orders, use_container_width=True)
    else:
        st.info("No pending orders.")

    st.markdown("### 🛠 Open Purchase Orders")
    open_pos = status.get("open_purchase_orders", [])
    if open_pos:
        df_pos = pd.DataFrame(open_pos)
        st.dataframe(df_pos, use_container_width=True)
    else:
        st.info("No open purchase orders.")


with col2:
    st.markdown("### 📦 Inventory Levels")
    inventory_levels = status.get("inventory_levels", [])
    if inventory_levels:
        df_inv = pd.DataFrame(inventory_levels)
        # Assuming product lookup is hard without an endpoint, but we can display IDs and Quantities
        # color code: < 5 red
        def highlight_stock(s):
            return ['background-color: #ffcccc' if v < 5 else '' for v in s]
        
        st.dataframe(df_inv.style.map(lambda v: 'background-color: #ffcccc' if float(v) < 5 else '', subset=['quantity']), use_container_width=True)
    else:
        st.info("No inventory data.")

    st.markdown("### 📊 Factory Events")
    events = fetch_data("events")
    if events:
        df_events = pd.DataFrame(events)
        st.dataframe(df_events[["sim_date", "type", "details"]], use_container_width=True)
    else:
        st.info("No events logged yet.")


# Charts
st.markdown("---")
st.markdown("### 📈 Charts")

if events:
    # Example chart: Cumulative Finished Orders
    df_events = pd.DataFrame(events)
    # filter for completions
    completions = df_events[df_events["type"] == "order_completed"]
    if not completions.empty:
        qty_extract = completions["details"].apply(lambda x: x.get("qty", 0))
        completions = completions.assign(completed_qty=qty_extract)
        
        # Agrupar por dia
        daily_completions = completions.groupby("sim_date")["completed_qty"].sum().reset_index()
        daily_completions["cumulative"] = daily_completions["completed_qty"].cumsum()
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(daily_completions["sim_date"], daily_completions["cumulative"], marker="o", color="blue")
        ax.set_title("Cumulative Finished Orders")
        ax.set_xlabel("Simulation Day")
        ax.set_ylabel("Total Models Built")
        st.pyplot(fig)
    else:
        st.info("No completed orders yet to chart.")
