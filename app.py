import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import json

with open("scenarios.json", "r", encoding="utf-8") as file:
        scenarios = json.load(file)
    
# Load the existing dataset
current_day_sales = pd.read_csv('current_day_sales.csv')
current_day_sales['Time'] = pd.to_datetime(current_day_sales['Time'])

# Load data
daily_sales = pd.read_csv('daily_sales.csv')
cart_data = pd.read_csv('items_in_cart.csv')
available_data = pd.read_csv('available_items.csv')

# Convert dates
daily_sales['Date'] = pd.to_datetime(daily_sales['Date'])

platforms = current_day_sales['Platform'].unique()
products = current_day_sales['Product'].unique()

# Streamlit setup
st.set_page_config(page_title="Phân Tích Sản Phẩm và Báo Cáo Doanh Số", layout="wide")

# Sidebar navigation
page = st.sidebar.selectbox("Chọn trang", ["Phân Tích Sản Phẩm", "Báo Cáo Tự Động Về Doanh Số"])

if page == "Phân Tích Sản Phẩm":
    st.title("Phân Tích Sản Phẩm")

    # Biểu đồ cột: Tổng số lượng bán ra theo tháng
    daily_sales['Month'] = daily_sales['Date'].dt.to_period('M')
    sales_by_month = daily_sales.groupby(['Month', 'Platform'])['Daily Sales'].sum().reset_index()

    fig_bar = go.Figure()
    for platform in sales_by_month['Platform'].unique():
        platform_data = sales_by_month[sales_by_month['Platform'] == platform]
        fig_bar.add_trace(go.Bar(
            x=platform_data['Month'].astype(str),
            y=platform_data['Daily Sales'],
            name=platform
        ))

    fig_bar.update_layout(
        title="Total Sales by Month and Platform",
        xaxis_title="Month",
        yaxis_title="Total Sales",
        barmode='group',
        xaxis=dict(tickangle=45),
        margin=dict(l=40, r=40, t=50, b=20),
        height=700,
        width=500 
    )

    # Hiển thị biểu đồ cột
    st.plotly_chart(fig_bar, use_container_width=True)

    # Biểu đồ tròn: Phân phối sản phẩm trong giỏ hàng
    cart_data = pd.read_csv('items_in_cart.csv')
    platforms = cart_data['Platform'].unique()

    fig_pie_row = []
    for platform in platforms:
        platform_cart = cart_data[cart_data['Platform'] == platform]
        items_in_cart = platform_cart.groupby('Product')['Items in Cart'].sum().reset_index()

        fig_pie = go.Figure(data=[
            go.Pie(labels=items_in_cart['Product'], values=items_in_cart['Items in Cart'], hole=0.3)
        ])
        fig_pie.update_layout(
            title=f"Cart Distribution on {platform}",
            margin=dict(l=10, r=10, t=50, b=10),
            height=350,
            width=350
        )
        fig_pie_row.append(fig_pie)

    # Hiển thị 3 biểu đồ tròn trên cùng một hàng ngang
    st.write("### Phân phối sản phẩm trong giỏ hàng")
    cols = st.columns(len(fig_pie_row))
    for col, fig in zip(cols, fig_pie_row):
        with col:
            st.plotly_chart(fig, use_container_width=False)
         # Biểu đồ cột và đường: Tổng số lượng bán ra theo sản phẩm trong 30 ngày gần nhất tách theo sàn
    selected_platform = st.sidebar.selectbox("Chọn nền tảng", platforms)

    # Filter data based on selected platform
    platform_data = daily_sales[daily_sales['Platform'] == selected_platform]
    
    # Filter data for the last 30 days
    last_30_days = platform_data[platform_data['Date'] >= platform_data['Date'].max() - pd.Timedelta(days=30)]
    
    # Group data by product and date
    grouped_data = last_30_days.groupby(['Product', 'Date'])['Daily Sales'].sum().reset_index()
    
    # Generate plots for each product
    cols = st.columns(len(products))  # Adjust layout for each product
    
    for i, product in enumerate(products):
        product_data = grouped_data[grouped_data['Product'] == product]
    
        if product_data.empty:
            with cols[i % len(cols)]:
                st.warning(f"Không có dữ liệu cho sản phẩm {product}")
            continue
    
        # Calculate rolling sales (3-day sum)
        product_data['Rolling Sales'] = product_data['Daily Sales'].rolling(window=3).sum()
    
        # Create plot
        fig = go.Figure()
    
        # Add bar chart for daily sales
        fig.add_trace(go.Bar(
            x=product_data['Date'],
            y=product_data['Daily Sales'],
            name='Daily Sales',
            marker_color='blue'
        ))
    
        # Add line chart for rolling sales
        fig.add_trace(go.Scatter(
            x=product_data['Date'],
            y=product_data['Rolling Sales'],
            mode='lines+markers',
            name='3-Day Rolling Sales',
            line=dict(color='red', width=2)
        ))
    
        # Update layout
        fig.update_layout(
            title=f"Sales for {product} (Last 30 Days - {selected_platform})",
            xaxis_title="Date",
            yaxis_title="Sales",
            xaxis=dict(tickformat="%b %d"),
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center")
        )
    
        # Display plot
        with cols[i % len(cols)]:
            st.plotly_chart(fig, use_container_width=True)

    
   
    
elif page == "Báo Cáo Tự Động Về Doanh Số":
    st.title('Báo Cáo Tự Động Về Doanh Số')
    st.write("Hiển thị doanh số, lợi nhuận và thông tin liên quan.")

    # Placeholder for charts
    area_placeholder1 = st.empty()
    area_placeholder2 = st.empty()

    # Initialize simulation data
    simulation_data_platform = daily_sales.groupby(['Date', 'Platform'])['Daily Sales'].sum().reset_index()
    simulation_data_product = daily_sales.groupby(['Date', 'Product'])['Daily Sales'].sum().reset_index()

    # Add initial normalized percentages
    def normalize_data(grouped_data, group_by):
        total_sales_by_date = grouped_data.groupby('Date')['Daily Sales'].sum().reset_index()
        grouped_data = grouped_data.merge(total_sales_by_date, on='Date', suffixes=(None, '_Total'))
        grouped_data['Percentage'] = (grouped_data['Daily Sales'] / grouped_data['Daily Sales_Total']) * 100
        return grouped_data

    simulation_data_platform = normalize_data(simulation_data_platform, 'Platform')
    simulation_data_product = normalize_data(simulation_data_product, 'Product')

    def simulate_and_update_area():
        global simulation_data_platform, simulation_data_product

        # Simulate new data by adding a new timestamp and adjusting existing percentages
        latest_date = simulation_data_platform['Date'].max()
        new_date = latest_date + pd.Timedelta(days=1)

        for group, simulation_data in [('Platform', simulation_data_platform), ('Product', simulation_data_product)]:
            for value in simulation_data[group].unique():
                # Create new data point
                new_percentage = np.random.uniform(5, 25)  # Randomized percentage for new data
                new_entry = {
                    'Date': new_date,
                    group: value,
                    'Daily Sales': 0,  # Placeholder for actual sales
                    'Daily Sales_Total': 0,  # Placeholder
                    'Percentage': new_percentage
                }
                simulation_data = pd.concat([simulation_data, pd.DataFrame([new_entry])], ignore_index=True)

            # Adjust percentages for the existing data to ensure they sum to 100%
            for date in simulation_data['Date'].unique():
                date_mask = simulation_data['Date'] == date
                simulation_data.loc[date_mask, 'Percentage'] = (
                    simulation_data.loc[date_mask, 'Percentage'] /
                    simulation_data.loc[date_mask, 'Percentage'].sum()
                ) * 100

            # Remove old data points to simulate "scrolling"
            if len(simulation_data['Date'].unique()) > 10:  # Keep only the latest 10 timestamps
                oldest_date = simulation_data['Date'].min()
                simulation_data = simulation_data[simulation_data['Date'] > oldest_date]

            # Update the global variable
            if group == 'Platform':
                simulation_data_platform = simulation_data
            else:
                simulation_data_product = simulation_data

        # Update area charts
        fig_area_platform = go.Figure()
        for platform in platforms:
            platform_data = simulation_data_platform[simulation_data_platform['Platform'] == platform]
            fig_area_platform.add_trace(go.Scatter(
                x=platform_data['Date'],
                y=platform_data['Percentage'],
                stackgroup='one',
                name=platform
            ))

        fig_area_platform.update_layout(
            title="Tỷ lệ doanh số theo nền tảng",
            xaxis_title="Thời gian",
            yaxis_title="Tỷ lệ (%)",
            height=400,
            template="plotly_white"
        )

        fig_area_product = go.Figure()
        for product in products:
            product_data = simulation_data_product[simulation_data_product['Product'] == product]
            fig_area_product.add_trace(go.Scatter(
                x=product_data['Date'],
                y=product_data['Percentage'],
                stackgroup='one',
                name=product
            ))

        fig_area_product.update_layout(
            title="Tỷ lệ doanh số theo loại sản phẩm",
            xaxis_title="Thời gian",
            yaxis_title="Tỷ lệ (%)",
            height=400,
            template="plotly_white"
        )

        # Display updated charts
        area_placeholder1.plotly_chart(fig_area_platform, use_container_width=True)
        area_placeholder2.plotly_chart(fig_area_product, use_container_width=True)

    # Continuous updates
    while True:
        simulate_and_update_area()
        time.sleep(5)
