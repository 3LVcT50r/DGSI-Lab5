import json
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000/api/v1"
PROVIDER_API_URL = "http://localhost:8001/api/v1"

st.set_page_config(
    page_title="3D Printer Factory Simulator",
    layout="wide",
)


def fetch_data(endpoint: str):
    """GET data from the API."""
    try:
        response = requests.get(
            f"{API_URL}/{endpoint}"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return None
    
def fetch_data_provider(endpoint: str):
    """GET data from the API."""
    try:
        response = requests.get(
            f"{PROVIDER_API_URL}/{endpoint}"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return None


def post_data(endpoint: str, json_data=None):
    """POST data to the API."""
    try:
        response = requests.post(
            f"{API_URL}/{endpoint}", json=json_data
        )
        response.raise_for_status()
        st.success(f"Success: {endpoint}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = e.response.json().get(
            "detail", str(e)
        )
        st.error(f"Error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def post_file(endpoint: str, file):
    """POST a file upload to the API."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type or "application/json")}
        response = requests.post(
            f"{API_URL}/{endpoint}", files=files
        )
        response.raise_for_status()
        st.success(f"Imported: {endpoint}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            error_msg = e.response.json().get("detail", str(e))
        except Exception:
            error_msg = str(e)
        st.error(f"Error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def export_inventory_data():
    """Fetch inventory export JSON from the API."""
    try:
        response = requests.get(f"{API_URL}/state/export/inventory")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error exporting inventory: {e}")
        return None
    
def post_data_provider(endpoint: str, json_data=None):
    """POST data to the API."""
    try:
        response = requests.post(
            f"{PROVIDER_API_URL}/{endpoint}", json=json_data
        )
        response.raise_for_status()
        st.success(f"Success: {endpoint}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_msg = e.response.json().get(
            "detail", str(e)
        )
        st.error(f"Error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def refresh():
    """Trigger a Streamlit rerun."""
    st.rerun()


st.title("🏭 3D Printer Factory Simulation")

# Fetch overall status and mapping
status = fetch_data("simulate/status")
products = fetch_data("products")

if status is None or products is None:
    st.warning(
        "Cannot connect to backend. "
        "Is FastAPI running on port 8000?"
    )
    st.stop()

# Build Product Map { id -> name }
product_map = {
    p["id"]: p["name"] for p in products
}

current_day = status.get("current_day", 0)

# Sidebar Controls
st.sidebar.header(f"📅 Day: {current_day}")

if st.sidebar.button("▶️ Advance Day"):
    post_data("simulate/advance")
    post_data_provider("day/advance")
    refresh()

if st.sidebar.button("🔄 Reset Simulation"):
    post_data("simulate/reset")
    refresh()

st.sidebar.markdown("---")
st.sidebar.header("Purchasing (Raw Materials)")

suppliers = fetch_data("suppliers")
if suppliers:
    unique_supp_names = list(
        set([s["name"] for s in suppliers])
    )
    selected_supp_name = st.sidebar.selectbox(
        "Supplier Name", unique_supp_names
    )

    supp_items = [
        s for s in suppliers
        if s["name"] == selected_supp_name
    ]

    catalog = fetch_data_provider("catalog")
    if catalog:
        # Flatten catalog items
        catalog_options = {}
        for item in catalog:
            product = item["product"]
            for tier in item["pricing_tiers"]:
                label = f"{product['name']} - Qty {tier['min_quantity']}+ @ ${tier['price']}"
                catalog_options[label] = {
                    "product_id": product["id"],
                    "min_quantity": tier["min_quantity"],
                    "price": tier["price"],
                }

        selected_item_label = st.sidebar.selectbox(
            "Product", list(catalog_options.keys())
        )
        selected_item = catalog_options[selected_item_label]

        min_qty = selected_item["min_quantity"]
        qty = st.sidebar.number_input(
            "Quantity",
            min_value=min_qty,
            value=min_qty,
            step=1,
        )

        if st.sidebar.button("Issue PO"):
            post_data_provider("orders", {
                "supplier_id": 1,  # Dummy, since we don't use suppliers anymore
                "product_id": selected_item["product_id"],
                "quantity": qty,
            })
            refresh()

# --- Main Layout ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Pending Manufacturing Orders")
    pending_orders = status.get(
        "pending_orders", []
    )
    if pending_orders:
        df_orders = pd.DataFrame(pending_orders)
        df_orders["Product"] = (
            df_orders["product_id"].map(product_map)
        )

        selected_order_id = st.selectbox(
            "Select Pending Order to Release Manually",
            df_orders["id"].tolist(),
        )
        if st.button("Release Selected Order"):
            post_data(
                f"orders/{selected_order_id}/release"
            )
            refresh()

        st.dataframe(
            df_orders[[
                "id", "Product", "quantity",
                "created_date", "status",
            ]],
            use_container_width=True,
        )
    else:
        st.info("No pending orders.")

    st.markdown("### 🛠 Open Purchase Orders")
    open_pos = fetch_data_provider("orders")
    if open_pos:
        df_pos = pd.DataFrame(open_pos)
        df_pos["Product"] = (
            df_pos["product_id"].map(product_map)
        )
        st.dataframe(
            df_pos[[
                "id", "Product", "quantity",
                "expected_delivery_day", "status",
            ]],
            use_container_width=True,
        )
    else:
        st.info("No open purchase orders.")

with col2:
    st.markdown("### 📦 Inventory Levels")
    inventory_levels = status.get(
        "inventory_levels", []
    )
    if inventory_levels:
        df_inv = pd.DataFrame(inventory_levels)
        df_inv["Product"] = (
            df_inv["product_id"].map(product_map)
        )

        df_inv_viz = df_inv[[
            "Product", "quantity", "reserved",
        ]]

        def _highlight_low(v):
            try:
                return (
                    "background-color: #ffcccc"
                    if float(v) < 5 else ""
                )
            except (ValueError, TypeError):
                return ""

        st.dataframe(
            df_inv_viz.style.map(
                _highlight_low,
                subset=["quantity"],
            ),
            use_container_width=True,
        )
    else:
        st.info("No inventory data.")

    st.markdown("### � Inventory Import / Export")
    export_col, import_col = st.columns(2)
    with export_col:
        if st.button("Export Inventory JSON"):
            inventory_export = export_inventory_data()
            if inventory_export is not None:
                st.download_button(
                    "Download inventory JSON",
                    data=json.dumps(inventory_export, indent=2),
                    file_name="inventory_export.json",
                    mime="application/json",
                    help="Download current inventory as a JSON file.",
                )
    with import_col:
        uploaded_file = st.file_uploader(
            "Import inventory JSON",
            type=["json"],
        )
        if uploaded_file is not None:
            if st.button("Upload Inventory JSON"):
                post_file("state/import/inventory", uploaded_file)
                refresh()

    st.markdown("### �📊 Factory Events")
    events = fetch_data("events")
    if events:
        df_events = pd.DataFrame(events)
        st.dataframe(
            df_events[[
                "sim_date", "type", "details",
            ]],
            use_container_width=True,
        )
    else:
        st.info("No events logged yet.")

# Charts
st.markdown("---")
st.markdown("### 📈 Charts")

if events:
    df_events = pd.DataFrame(events)
    completions = df_events[
        df_events["type"] == "order_completed"
    ]
    if not completions.empty:
        qty_extract = completions["details"].apply(
            lambda x: x.get("qty", 0)
        )
        completions = completions.assign(
            completed_qty=qty_extract
        )

        daily_completions = (
            completions
            .groupby("sim_date")["completed_qty"]
            .sum()
            .reset_index()
        )
        daily_completions["cumulative"] = (
            daily_completions["completed_qty"].cumsum()
        )

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(
            daily_completions["sim_date"],
            daily_completions["cumulative"],
            marker="o",
            color="blue",
        )
        ax.set_title("Cumulative Finished Orders")
        ax.set_xlabel("Simulation Day")
        ax.set_ylabel("Total Models Built")
        st.pyplot(fig)
    else:
        st.info(
            "No completed orders yet to chart."
        )
