import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime


def create_inventory_chart(inventory_data):
    """Create inventory levels bar chart."""
    if not inventory_data:
        return None

    df = pd.DataFrame(inventory_data)
    df = df.sort_values('quantity', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(df['product_id'].astype(str), df['quantity'])

    # Color bars based on quantity (red for low, green for high)
    max_qty = df['quantity'].max() if not df.empty else 1
    for bar, qty in zip(bars, df['quantity']):
        if qty == 0:
            bar.set_color('red')
        elif qty < max_qty * 0.3:
            bar.set_color('orange')
        else:
            bar.set_color('green')

    ax.set_xlabel('Quantity')
    ax.set_ylabel('Product ID')
    ax.set_title('Current Inventory Levels')
    ax.grid(True, alpha=0.3)

    return fig


def create_orders_status_chart(orders_data):
    """Create pie chart of order statuses."""
    if not orders_data:
        return None

    df = pd.DataFrame(orders_data)
    status_counts = df['status'].value_counts()

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = {'pending': 'orange', 'in_progress': 'blue', 'completed': 'green'}

    wedges, texts, autotexts = ax.pie(
        status_counts.values,
        labels=status_counts.index,
        colors=[colors.get(status, 'gray') for status in status_counts.index],
        autopct='%1.1f%%',
        startangle=90
    )

    ax.set_title('Manufacturing Orders by Status')
    ax.axis('equal')

    return fig


def create_purchase_orders_timeline(po_data):
    """Create timeline chart of purchase orders."""
    if not po_data:
        return None

    df = pd.DataFrame(po_data)
    df['issue_date'] = pd.to_datetime(df['issue_date'])
    df['expected_delivery'] = pd.to_datetime(df['expected_delivery'])

    # Sort by issue date
    df = df.sort_values('issue_date')

    fig, ax = plt.subplots(figsize=(12, 6))

    for idx, row in df.iterrows():
        # Draw line from issue to expected delivery
        ax.plot([row['issue_date'], row['expected_delivery']],
                [idx, idx], marker='o', linewidth=2)

        # Add quantity label
        ax.text(row['issue_date'], idx + 0.1, f"Qty: {row['quantity']}",
                fontsize=8, verticalalignment='bottom')

    ax.set_xlabel('Date')
    ax.set_ylabel('Purchase Order')
    ax.set_title('Purchase Orders Timeline')
    ax.grid(True, alpha=0.3)

    # Format x-axis dates
    fig.autofmt_xdate()

    return fig


def create_daily_production_chart(metrics_data=None):
    """Create daily production chart from historical data."""
    if not metrics_data or len(metrics_data) < 2:
        # Fallback to mock data if no historical data
        days = list(range(1, 11))
        production = np.random.randint(0, 15, size=10)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(days, production, marker='o', linewidth=2, markersize=6, color='blue')
        ax.fill_between(days, production, alpha=0.3, color='lightblue')
        ax.set_xlabel('Day')
        ax.set_ylabel('Units Produced')
        ax.set_title('Daily Production (Mock Data - No Historical Data Yet)')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(days)
        return fig

    # Use real historical data
    df = pd.DataFrame(metrics_data)
    days = df['day'].tolist()
    production = df['production_output'].tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(days, production, marker='o', linewidth=2, markersize=6, color='green')
    ax.fill_between(days, production, alpha=0.3, color='lightgreen')

    ax.set_xlabel('Day')
    ax.set_ylabel('Production Output')
    ax.set_title('Daily Production History')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(days)

    return fig


def create_inventory_trend_chart(metrics_data=None):
    """Create inventory trend chart from historical data."""
    if not metrics_data or len(metrics_data) < 2:
        return None

    df = pd.DataFrame(metrics_data)
    days = df['day'].tolist()
    inventory = df['total_inventory'].tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(days, inventory, marker='s', linewidth=2, markersize=6, color='purple')
    ax.fill_between(days, inventory, alpha=0.3, color='lavender')

    ax.set_xlabel('Day')
    ax.set_ylabel('Total Inventory')
    ax.set_title('Inventory Levels Over Time')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(days)

    return fig


def create_orders_trend_chart(metrics_data=None):
    """Create orders trend chart from historical data."""
    if not metrics_data or len(metrics_data) < 2:
        return None

    df = pd.DataFrame(metrics_data)
    days = df['day'].tolist()
    pending = df['pending_orders'].tolist()
    completed = df['completed_orders'].tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(days, pending, marker='o', linewidth=2, markersize=6, color='orange', label='Pending')
    ax.plot(days, completed, marker='s', linewidth=2, markersize=6, color='green', label='Completed')

    ax.set_xlabel('Day')
    ax.set_ylabel('Number of Orders')
    ax.set_title('Orders Trend Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xticks(days)

    return fig