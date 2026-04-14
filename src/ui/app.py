import sys
from pathlib import Path

import streamlit as st
import requests
import pandas as pd

# Ensure the ui package path is on sys.path when Streamlit runs app.py directly
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from charts import (
    create_inventory_chart,
    create_orders_status_chart,
    create_purchase_orders_timeline,
    create_daily_production_chart,
    create_inventory_trend_chart,
    create_orders_trend_chart
)


def main():
    st.set_page_config(
        page_title="3D Printer Factory Simulator",
        page_icon="🏭",
        layout="wide"
    )

    st.title("🏭 3D Printer Factory Simulator")
    st.markdown("---")

    # API base URL
    API_BASE = "http://localhost:8000/api/v1"

    # Sidebar controls
    with st.sidebar:
        st.header("Simulation Controls")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Advance Day", type="primary"):
                try:
                    response = requests.post(f"{API_BASE}/simulate/advance")
                    if response.status_code == 200:
                        st.success("Day advanced!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

        with col2:
            if st.button("🔄 Reset", type="secondary"):
                try:
                    response = requests.post(f"{API_BASE}/simulate/reset")
                    if response.status_code == 200:
                        st.success("Simulation reset!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

        st.markdown("---")

        # Current simulation status
        try:
            status_response = requests.get(f"{API_BASE}/simulate/status")
            if status_response.status_code == 200:
                status = status_response.json()
                st.metric("Current Day", status.get("current_day", 0))
                st.metric("Total Events", status.get("total_events", 0))
            else:
                st.error("Unable to fetch simulation status")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "📦 Inventory",
        "📋 Orders",
        "🚚 Purchase Orders",
        "📈 Historical Trends"
    ])

    # Overview Tab
    with tab1:
        st.header("Factory Overview")

        try:
            # Get current status
            status_response = requests.get(f"{API_BASE}/simulate/status")
            if status_response.status_code == 200:
                status = status_response.json()

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Day", status.get("current_day", 0))
                with col2:
                    st.metric("Total Events", status.get("total_events", 0))
                with col3:
                    st.metric("Active Orders", status.get("active_orders", 0))
                with col4:
                    st.metric("Pending POs", status.get("pending_pos", 0))

                # Recent events
                st.subheader("Recent Events")
                events = status.get("recent_events", [])
                if events:
                    for event in events[-5:]:  # Show last 5 events
                        st.write(f"**Day {event['sim_date']}**: {event['type']} - {event['details']}")
                else:
                    st.info("No events yet. Advance a day to start simulation.")

        except Exception as e:
            st.error(f"Unable to fetch overview data: {e}")

    # Inventory Tab
    with tab2:
        st.header("Inventory Management")

        try:
            # Get inventory data
            inventory_response = requests.get(f"{API_BASE}/inventory")
            if inventory_response.status_code == 200:
                inventory_data = inventory_response.json()

                # Data table
                if inventory_data:
                    df = pd.DataFrame(inventory_data)
                    st.dataframe(df, use_container_width=True)

                    # Chart
                    fig = create_inventory_chart(inventory_data)
                    if fig:
                        st.pyplot(fig)
                else:
                    st.info("No inventory data available.")

        except Exception as e:
            st.error(f"Unable to fetch inventory data: {e}")

    # Orders Tab
    with tab3:
        st.header("Manufacturing Orders")

        try:
            # Get orders data
            orders_response = requests.get(f"{API_BASE}/orders")
            if orders_response.status_code == 200:
                orders_data = orders_response.json()

                if orders_data:
                    df = pd.DataFrame(orders_data)
                    st.dataframe(df, use_container_width=True)

                    # Status chart
                    fig = create_orders_status_chart(orders_data)
                    if fig:
                        st.pyplot(fig)
                else:
                    st.info("No orders data available.")

        except Exception as e:
            st.error(f"Unable to fetch orders data: {e}")

    # Purchase Orders Tab
    with tab4:
        st.header("Purchase Orders")

        try:
            # Get suppliers first for context
            suppliers_response = requests.get(f"{API_BASE}/suppliers")
            suppliers = {}
            if suppliers_response.status_code == 200:
                for supplier in suppliers_response.json():
                    suppliers[supplier['id']] = supplier['name']

            # Get PO data
            po_response = requests.get(f"{API_BASE}/purchase-orders")
            if po_response.status_code == 200:
                po_data = po_response.json()

                if po_data:
                    # Add supplier names
                    for po in po_data:
                        po['supplier_name'] = suppliers.get(po['supplier_id'], 'Unknown')

                    df = pd.DataFrame(po_data)
                    st.dataframe(df, use_container_width=True)

                    # Timeline chart
                    fig = create_purchase_orders_timeline(po_data)
                    if fig:
                        st.pyplot(fig)
                else:
                    st.info("No purchase orders data available.")

        except Exception as e:
            st.error(f"Unable to fetch purchase orders data: {e}")

    # Historical Trends Tab
    with tab5:
        st.header("Historical Trends")

        try:
            # Get historical metrics
            metrics_response = requests.get(f"{API_BASE}/metrics/history")
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()

                if metrics_data and len(metrics_data) > 1:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Daily Production")
                        fig_prod = create_daily_production_chart(metrics_data)
                        if fig_prod:
                            st.pyplot(fig_prod)

                        st.subheader("Inventory Trends")
                        fig_inv = create_inventory_trend_chart(metrics_data)
                        if fig_inv:
                            st.pyplot(fig_inv)

                    with col2:
                        st.subheader("Orders Trend")
                        fig_orders = create_orders_trend_chart(metrics_data)
                        if fig_orders:
                            st.pyplot(fig_orders)

                    # Raw data table
                    st.subheader("Historical Data")
                    df = pd.DataFrame(metrics_data)
                    st.dataframe(df, use_container_width=True)

                else:
                    st.info("Not enough historical data yet. Advance several days to see trends.")

                    # Show mock charts for demonstration
                    st.subheader("Sample Charts (Mock Data)")
                    fig_prod = create_daily_production_chart()
                    if fig_prod:
                        st.pyplot(fig_prod)

        except Exception as e:
            st.error(f"Unable to fetch historical data: {e}")


if __name__ == "__main__":
    main()