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

    
   
    
    # Thêm phần chiến dịch Affiliate dưới biểu đồ
    if page == "Phân Tích Sản Phẩm":
        st.title("Định Hướng Chiến Dịch Affiliate")
        
        if "current_scenario_index" not in st.session_state:
                st.session_state["current_scenario_index"] = 0    

        # Hiển thị kịch bản hiện tại
        scenario = scenarios[st.session_state["current_scenario_index"]]
        st.write(f"### {scenario['title']}")
        st.markdown(f"**Mục tiêu:** {scenario['objective']}")
    
        st.write("**Phân bổ ngân sách:**")
        for item, cost in scenario['allocation'].items():
            st.write(f"- **{item}:** {cost}")
    
        st.write("**Lịch trình hoạt động:**")
        for task in scenario['schedule']:
            st.write(f"- {task}")
    
        st.write("**Chương trình khuyến mãi:**")
        st.markdown(scenario['promotion'])
    
        st.write("**Kỳ vọng hiệu quả:**")
        if isinstance(scenario['expected'], dict):
            for key, value in scenario['expected'].items():
                st.write(f"- **{key}:** {value}")
        else:
            st.markdown(scenario['expected'])
    
        # Nút chuyển kịch bản
        if st.button("Gen kịch bản khác"):
            st.session_state["current_scenario_index"] = (
                st.session_state["current_scenario_index"] + 1
            ) % len(scenarios)
    
        
elif page == "Báo Cáo Tự Động Về Doanh Số":
    st.title("Báo Cáo Tự Động Về Doanh Số")
    st.write("Trang này hiển thị các biểu đồ và số liệu tự động cập nhật.")

    # Step 1: KPI placeholders
    kpi_placeholder = st.empty()

    # Step 2: Biểu đồ kết hợp cột và đường
    st.header("Biểu Đồ Kết Hợp Cột và Đường: Tổng Bán Theo Sản Phẩm")

    # Group data by product and date
    grouped_data = daily_sales.groupby(['Product', 'Date'])['Daily Sales'].sum().reset_index()

    # Create plots for each product
    products = daily_sales['Product'].unique()
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
            title=f"Sales for {product} (Last 30 Days)",
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

    # Step 3: Biểu đồ miền cập nhật theo thời gian
    st.header("Phân Phối Doanh Số Theo Thời Gian (Cập Nhật Liên Tục)")

    # Initialize real-time simulation variables
    sales_by_platform = {platform: 100 / len(daily_sales['Platform'].unique()) for platform in daily_sales['Platform'].unique()}
    sales_by_product = {product: 100 / len(daily_sales['Product'].unique()) for product in daily_sales['Product'].unique()}
    area_placeholder1 = st.empty()
    area_placeholder2 = st.empty()

    # Normalize function to ensure total percentage is 100%
    def normalize_data(data_dict):
        total = sum(data_dict.values())
        if total > 0:
            data_dict = {k: (v / total) * 100 for k, v in data_dict.items()}
        return data_dict

    # Function to simulate new data every 5 seconds
    def update_kpis_and_areas():
        global sales_by_platform, sales_by_product

        # Simulate sales updates
        for platform in sales_by_platform:
            sales_by_platform[platform] += np.random.uniform(-2, 5)
        sales_by_platform = normalize_data(sales_by_platform)

        for product in sales_by_product:
            sales_by_product[product] += np.random.uniform(-2, 5)
        sales_by_product = normalize_data(sales_by_product)

        # Prepare data for platform area chart
        platform_df = pd.DataFrame({
            "Platform": list(sales_by_platform.keys()),
            "Sales Percentage": list(sales_by_platform.values()),
            "Time": [pd.Timestamp.now()] * len(sales_by_platform)
        })

        # Prepare data for product area chart
        product_df = pd.DataFrame({
            "Product": list(sales_by_product.keys()),
            "Sales Percentage": list(sales_by_product.values()),
            "Time": [pd.Timestamp.now()] * len(sales_by_product)
        })

        # Create and update area chart for platform
        fig_area1 = px.area(
            platform_df,
            x="Time",
            y="Sales Percentage",
            color="Platform",
            title="Phân Phối Doanh Số Theo Sàn (Cập Nhật Liên Tục)"
        )

        # Create and update area chart for product
        fig_area2 = px.area(
            product_df,
            x="Time",
            y="Sales Percentage",
            color="Product",
            title="Phân Phối Doanh Số Theo Loại Sản Phẩm (Cập Nhật Liên Tục)"
        )

        # Display updated charts
        with area_placeholder1.container():
            st.plotly_chart(fig_area1, use_container_width=True)

        with area_placeholder2.container():
            st.plotly_chart(fig_area2, use_container_width=True)

        # Update KPIs
        current_revenue = sum(sales_by_platform.values()) * 1000  # Dummy revenue value
        current_cost = current_revenue * 0.6
        profit = current_revenue - current_cost

        with kpi_placeholder.container():
            st.metric("Tổng Doanh Thu", f"${current_revenue:,.0f}", delta=f"+{np.random.randint(1000, 5000):,.0f}")
            st.metric("Tổng Lợi Nhuận", f"${profit:,.0f}", delta=f"+{np.random.randint(100, 500):,.0f}")

    # Real-time updates
    while True:
        update_kpis_and_areas()
        time.sleep(5)
