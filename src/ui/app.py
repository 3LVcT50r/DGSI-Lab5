import streamlit as st

st.set_page_config(page_title="3D Printer Factory Simulator", layout="wide")

st.title("3D Printer Factory Simulation")

st.sidebar.header("Simulation Controls")
if st.sidebar.button("Advance Day"):
    st.info("Advance Day action will call backend simulation logic.")

st.sidebar.header("Actions")
st.sidebar.button("Release selected order")
st.sidebar.button("Create purchase order")

st.markdown("## Pending Manufacturing Orders")
st.table([])

st.markdown("## Inventory Levels")
st.table([])

st.markdown("## Event Log")
st.table([])

st.markdown("## Bill of Materials")
st.caption("BOM breakdown for each order will appear here.")
