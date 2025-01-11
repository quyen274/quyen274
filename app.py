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
    st.title('Báo Cáo Tự Động Về Doanh Số')
    st.write("Hiển thị doanh số, lợi nhuận và thông tin liên quan.")

    # Sidebar for user selections
    selected_platforms = st.sidebar.multiselect("Chọn nền tảng:", platforms, default=platforms)
    selected_products = st.sidebar.multiselect("Chọn loại sản phẩm:", products, default=products)
    zoom_level = st.sidebar.slider("Chọn số lượng cột hiển thị:", 10, 50, 20)

    # Filter data based on user selection
    def filter_data(data, platforms, products):
        return data[(data['Platform'].isin(platforms)) & (data['Product'].isin(products))]

    # Simulate new data for live updates
    def simulate_new_data(data):
        latest_time = data['Time'].max() + pd.Timedelta(minutes=15)
        new_data = []
        for platform in platforms:
            for product in products:
                sales_15_min = np.random.randint(1, 20)
                new_data.append({'Time': latest_time, 'Platform': platform, 'Product': product, 'Sales (15 min)': sales_15_min})
        new_df = pd.DataFrame(new_data)
        return pd.concat([data, new_df], ignore_index=True)

    # Initialize variables for real-time simulation
    current_revenue = 100_000_000  # Starting revenue
    current_cost = 60_000_000  # Starting cost
    sales_by_platform = {platform: 100 / len(platforms) for platform in platforms}
    sales_by_product = {product: 100 / len(products) for product in products}

    # Placeholder for KPI and Pie charts
    # Placeholder for KPI and Area charts
kpi_placeholder = st.empty()
area_placeholder1 = st.empty()
area_placeholder2 = st.empty()

def update_kpis_and_area_charts():
    global current_revenue, current_cost, sales_by_platform, sales_by_product

    # Update revenue and cost
    current_revenue += 150_000  # Increase revenue every 5 seconds
    current_cost = current_revenue * 0.6  # Cost is 60% of revenue
    profit = current_revenue - current_cost

    # Display KPIs
    with kpi_placeholder.container():
        st.metric("Tổng Doanh Thu", f"${current_revenue / 1e6:.2f}M", delta=f"+0.15M")
        st.metric("Tổng Lợi Nhuận", f"${profit / 1e6:.2f}M", delta=f"+{(150_000 - 150_000 * 0.6) / 1e6:.2f}M")

    # Update sales distribution for platforms
    platform_total = sum(sales_by_platform.values())
    for platform in sales_by_platform:
        sales_by_platform[platform] += np.random.uniform(0.1, 2.0)
    platform_total_new = sum(sales_by_platform.values())
    for platform in sales_by_platform:
        sales_by_platform[platform] = (sales_by_platform[platform] / platform_total_new) * 100

    # Update sales distribution for products
    product_total = sum(sales_by_product.values())
    for product in sales_by_product:
        sales_by_product[product] += np.random.uniform(0.5, 1.0)
    product_total_new = sum(sales_by_product.values())
    for product in sales_by_product:
        sales_by_product[product] = (sales_by_product[product] / product_total_new) * 100

    # Create Area Chart: Sales by Platform
    platform_labels = list(sales_by_platform.keys())
    platform_values = list(sales_by_platform.values())
    platform_timestamps = [pd.Timestamp.now()] * len(platform_labels)

    platform_df = pd.DataFrame({
        "Time": platform_timestamps,
        "Platform": platform_labels,
        "Sales Percentage": platform_values
    })

    fig_area1 = px.area(
        platform_df,
        x="Time",
        y="Sales Percentage",
        color="Platform",
        title="Phân Phối Doanh Số Theo Sàn (Cập Nhật Liên Tục)",
    )
    fig_area1.update_layout(transition_duration=500)

    # Create Area Chart: Sales by Product
    product_labels = list(sales_by_product.keys())
    product_values = list(sales_by_product.values())
    product_timestamps = [pd.Timestamp.now()] * len(product_labels)

    product_df = pd.DataFrame({
        "Time": product_timestamps,
        "Product": product_labels,
        "Sales Percentage": product_values
    })

    fig_area2 = px.area(
        product_df,
        x="Time",
        y="Sales Percentage",
        color="Product",
        title="Phân Phối Doanh Số Theo Loại Sản Phẩm (Cập Nhật Liên Tục)",
    )
    fig_area2.update_layout(transition_duration=500)

    # Update the Area Charts directly
    with area_placeholder1.container():
        st.plotly_chart(fig_area1, use_container_width=True)
    with area_placeholder2.container():
        st.plotly_chart(fig_area2, use_container_width=True)

# Real-time Simulation Loop
data = current_day_sales.copy()
while True:
    # Update KPIs and Area Charts
    update_kpis_and_area_charts()

    # Simulate new data
    data = simulate_new_data(data)

    # Pause for real-time simulation
    time.sleep(5)

