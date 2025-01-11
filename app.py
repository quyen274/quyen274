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

    selected_platforms = st.sidebar.multiselect("Chọn nền tảng:", platforms, default=platforms)
    selected_products = st.sidebar.multiselect("Chọn loại sản phẩm:", products, default=products)
    zoom_level = st.sidebar.slider("Chọn số lượng cột hiển thị:", 10, 50, 20)

    # Placeholder for KPI and charts
    kpi_placeholder = st.empty()
    area_placeholder1 = st.empty()
    area_placeholder2 = st.empty()
    chart_placeholder = st.empty()

    # Initialize simulation variables
    current_revenue = 100_000_000  # Starting revenue
    current_cost = 60_000_000  # Starting cost

    # Function to simulate new data
    def simulate_new_data(data):
        latest_time = data['Time'].max() + pd.Timedelta(minutes=15)
        new_data = []
        for platform in platforms:
            for product in products:
                sales_15_min = np.random.randint(1, 20)
                new_data.append({'Time': latest_time, 'Platform': platform, 'Product': product, 'Sales (15 min)': sales_15_min})
        new_df = pd.DataFrame(new_data)
        return pd.concat([data, new_df], ignore_index=True)

    # KPI update function
    def update_kpis():
        global current_revenue, current_cost
        current_revenue += 150_000
        current_cost = current_revenue * 0.6
        profit = current_revenue - current_cost

        with kpi_placeholder.container():
            st.metric("Tổng Doanh Thu", f"${current_revenue / 1e6:.2f}M", delta=f"+0.15M")
            st.metric("Tổng Lợi Nhuận", f"${profit / 1e6:.2f}M", delta=f"+{(150_000 - 150_000 * 0.6) / 1e6:.2f}M")

    # Area chart update function
    def normalize_data(grouped_data, group_by):
        total_sales_by_date = grouped_data.groupby('Date')['Daily Sales'].sum().reset_index()
        grouped_data = grouped_data.merge(total_sales_by_date, on='Date', suffixes=(None, '_Total'))
        grouped_data['Percentage'] = (grouped_data['Daily Sales'] / grouped_data['Daily Sales_Total']) * 100
        return grouped_data

    simulation_data_platform = normalize_data(daily_sales.groupby(['Date', 'Platform'])['Daily Sales'].sum().reset_index(), 'Platform')
    simulation_data_product = normalize_data(daily_sales.groupby(['Date', 'Product'])['Daily Sales'].sum().reset_index(), 'Product')

    def update_area_charts():
        fig_area_platform = go.Figure()
        for platform in selected_platforms:
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
        for product in selected_products:
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

        area_placeholder1.plotly_chart(fig_area_platform, use_container_width=True)
        area_placeholder2.plotly_chart(fig_area_product, use_container_width=True)

    # Stacked bar and line chart update function
    def prepare_data(data):
        pivot_data = data.pivot_table(
            index='Time', columns='Platform', values='Sales (15 min)', aggfunc='sum', fill_value=0
        )
        return pivot_data

    def update_stacked_chart():
        filtered_data = prepare_data(current_day_sales)

        if len(filtered_data) > zoom_level:
            visible_data = filtered_data.iloc[-zoom_level:]
        else:
            visible_data = filtered_data

        fig = go.Figure()

        for platform in selected_platforms:
            if platform in visible_data.columns:
                fig.add_trace(go.Bar(
                    x=visible_data.index,
                    y=visible_data[platform],
                    name=platform
                ))

        cumulative_data = visible_data.cumsum(axis=1)
        for platform in selected_platforms:
            if platform in cumulative_data.columns:
                fig.add_trace(go.Scatter(
                    x=visible_data.index,
                    y=cumulative_data[platform],
                    mode='lines+markers',
                    name=f"{platform} (Đường)"
                ))

        fig.update_layout(
            barmode='stack',
            title="Biểu Đồ Doanh Số Theo Thời Gian",
            xaxis_title="Thời Gian",
            yaxis_title="Doanh Số",
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            template="plotly_white"
        )

        chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Adjust data time to align with current time
    def adjust_time(data):
        min_time = data['Time'].min()
        current_time = pd.Timestamp.now().replace(second=0, microsecond=0)
        time_diff = current_time - min_time
        data['Time'] = data['Time'] + time_diff
        return data

    current_day_sales = adjust_time(current_day_sales)
    data = current_day_sales.copy()

    # Continuous updates
    while True:
        update_kpis()
        update_area_charts()
        update_stacked_chart()

        data = simulate_new_data(data)
        current_day_sales = simulate_new_data(current_day_sales)

        time.sleep(5)


