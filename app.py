
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import openai

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

last_month_start = daily_sales['Date'].max() - pd.Timedelta(days=30)
last_month_data = daily_sales[daily_sales['Date'] >= last_month_start]
daily_sales_by_platform = last_month_data.groupby(['Date', 'Platform'])['Daily Sales'].sum().reset_index()

# Streamlit setup
st.set_page_config(page_title="Phân Tích Sản Phẩm và Báo Cáo Doanh Số", layout="wide")

# Sidebar navigation
page = st.sidebar.selectbox("Chọn trang", ["Phân Tích Sản Phẩm", "Báo Cáo Tự Động Về Doanh Số"])

if page == "Phân Tích Sản Phẩm":
    st.title("Phân Tích Sản Phẩm")

    default_platform = "Shopee"
    selected_platform = st.sidebar.selectbox("Chọn nền tảng", platforms, index=list(platforms).index(default_platform))
    show_all_platforms = st.sidebar.checkbox("Xem tất cả nền tảng trên biểu đồ cột", value=False)

    # --- Biểu đồ cột: Tổng số lượng bán theo tháng ---
    st.write("### Tổng số lượng bán theo tháng và nền tảng")
    daily_sales['Month'] = daily_sales['Date'].dt.to_period('M')
    sales_by_month = daily_sales.groupby(['Month', 'Platform'])['Daily Sales'].sum().reset_index()

    fig_bar_monthly = go.Figure()
    if show_all_platforms:
        for platform in sales_by_month['Platform'].unique():
            platform_data = sales_by_month[sales_by_month['Platform'] == platform]
            fig_bar_monthly.add_trace(go.Bar(
                x=platform_data['Month'].astype(str),
                y=platform_data['Daily Sales'],
                name=platform
            ))
    else:
        platform_data = sales_by_month[sales_by_month['Platform'] == selected_platform]
        fig_bar_monthly.add_trace(go.Bar(
            x=platform_data['Month'].astype(str),
            y=platform_data['Daily Sales'],
            name=selected_platform
        ))

    fig_bar_monthly.update_layout(
        title="Total Sales by Month and Platform",
        xaxis_title="Month",
        yaxis_title="Total Sales",
        barmode='group',
        xaxis=dict(tickangle=45),
        margin=dict(l=40, r=40, t=50, b=20),
        height=600,
        width=900
    )

    # --- Biểu đồ cột: Số lượng bán theo ngày ---
    st.write("### Tổng số lượng bán theo ngày trong 30 ngày gần nhất")
    fig_bar_daily = go.Figure()
    if show_all_platforms:
        for platform in daily_sales_by_platform['Platform'].unique():
            platform_data = daily_sales_by_platform[daily_sales_by_platform['Platform'] == platform]
            fig_bar_daily.add_trace(go.Bar(
                x=platform_data['Date'],
                y=platform_data['Daily Sales'],
                name=platform
            ))
    else:
        platform_data = daily_sales_by_platform[daily_sales_by_platform['Platform'] == selected_platform]
        fig_bar_daily.add_trace(go.Bar(
            x=platform_data['Date'],
            y=platform_data['Daily Sales'],
            name=selected_platform
        ))

    fig_bar_daily.update_layout(
        title="Sales by Day in the Last 30 Days (by Platform)",
        xaxis_title="Date",
        yaxis_title="Daily Sales",
        barmode='stack',
        xaxis=dict(tickformat="%b %d", tickangle=45),
        margin=dict(l=40, r=40, t=50, b=20),
        height=600,
        width=900
    )

    # Hiển thị hai biểu đồ cột trên cùng hàng ngang
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_bar_monthly, use_container_width=False, key="fig_bar_monthly")
    with col2:
        st.plotly_chart(fig_bar_daily, use_container_width=False, key="fig_bar_daily")

    # --- Biểu đồ cột và đường: Tổng số lượng bán theo sản phẩm ---
    st.write("### Tổng số lượng bán theo sản phẩm trong 30 ngày gần nhất")
    platform_data = daily_sales[daily_sales['Platform'] == selected_platform]
    last_30_days = platform_data[platform_data['Date'] >= platform_data['Date'].max() - pd.Timedelta(days=30)]
    grouped_data = last_30_days.groupby(['Product', 'Date'])['Daily Sales'].sum().reset_index()

    cols = st.columns(len(products))
    for i, product in enumerate(products):
        product_data = grouped_data[grouped_data['Product'] == product]
        if product_data.empty:
            with cols[i % len(cols)]:
                st.warning(f"Không có dữ liệu cho sản phẩm {product}")
            continue

        product_data['Rolling Sales'] = product_data['Daily Sales'].rolling(window=3).sum()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=product_data['Date'], y=product_data['Daily Sales'], name='Daily Sales', marker_color='blue'))
        fig.add_trace(go.Scatter(x=product_data['Date'], y=product_data['Rolling Sales'], mode='lines+markers',
                                 name='3-Day Rolling Sales', line=dict(color='red', width=2)))

        fig.update_layout(
            title=f"Sales for {product} (Last 30 Days - {selected_platform})",
            xaxis_title="Date",
            yaxis_title="Sales",
            xaxis=dict(tickformat="%b %d"),
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center")
        )
        with cols[i % len(cols)]:
            st.plotly_chart(fig, use_container_width=True, key=f"fig_{product}")

    # --- Biểu đồ tròn: Phân phối sản phẩm trong giỏ hàng ---
    st.write("### Phân phối sản phẩm trong giỏ hàng")
    fig_pie_row = []
    for platform in cart_data['Platform'].unique():
        platform_cart = cart_data[cart_data['Platform'] == platform]
        items_in_cart = platform_cart.groupby('Product')['Items in Cart'].sum().reset_index()

        fig_pie = go.Figure(data=[go.Pie(labels=items_in_cart['Product'], values=items_in_cart['Items in Cart'], hole=0.3)])
        fig_pie.update_layout(
            title=f"Cart Distribution on {platform}",
            margin=dict(l=10, r=10, t=50, b=10),
            height=350,
            width=350
        )
        fig_pie_row.append(fig_pie)

    cols = st.columns(len(fig_pie_row))
    for col, fig in zip(cols, fig_pie_row):
        with col:
            st.plotly_chart(fig, use_container_width=False)

    # --- Định hướng chiến dịch Affiliate ---
    st.title("Định Hướng Chiến Dịch Affiliate")
    if "current_scenario_index" not in st.session_state:
        st.session_state["current_scenario_index"] = 0

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

    if st.button("Gen kịch bản khác"):
        st.session_state["current_scenario_index"] = (st.session_state["current_scenario_index"] + 1) % len(scenarios)
    st.write("---")
    st.header("Hỏi đáp cùng ChatGPT")

# Initialize session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Display chat history
    for msg in st.session_state.messages:
            if msg['role'] == 'user':
                st.write(f"**Người dùng:** {msg['content']}")
            else:
                st.write(f"**ChatGPT:** {msg['content']}")

# User input
    user_input = st.text_input("Nhập câu hỏi của bạn:", key="user_input")
    if st.button("Gửi"):
            if user_input:
                # Add user message to session state
                st.session_state.messages.append({"role": "user", "content": user_input})
        
                # Get response from OpenAI API
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=st.session_state.messages
                    )
                    assistant_message = response["choices"][0]["message"]["content"]
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi: {e}")
        
                # Refresh the page to display the updated conversation
                st.experimental_rerun()
        
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
                sales_15_min = np.random.randint(1, 20)  # Random sales in 15 minutes
                new_data.append({'Time': latest_time, 'Platform': platform, 'Product': product, 'Sales (15 min)': sales_15_min})
        new_df = pd.DataFrame(new_data)
        return pd.concat([data, new_df], ignore_index=True)

    def format_box(name, value, time):
            """
            Tạo format cho box hiển thị (dựa theo thiết kế như trong hình).
            """
            return f"""
            <div style="display: flex; justify-content: space-between; align-items: center; background-color: #f9f9f9; padding: 10px; margin: 5px; border-radius: 8px;">
                <div style="flex: 1; font-weight: bold; font-size: 16px; text-align: left;">{name}</div>
                <div style="flex: 1; font-size: 14px; color: #333; text-align: center;">{value} sản phẩm</div>
                <div style="flex: 1; font-size: 12px; color: #666; text-align: right;">{time}</div>
            </div>
            """

    
# Chia màn hình thành 2 phần: biểu đồ bên trái và bảng bên phải
    left_col, right_col = st.columns([3, 1])

# Hiển thị biểu đồ và KPI bên trái
    with left_col:
                  # KPI and Chart Placeholders
          kpi_placeholder = st.empty()
          chart_placeholder = st.empty()
          area_placeholder1 = st.empty()
          area_placeholder2 = st.empty()
        
            # Normalize data for area charts
          def normalize_data(grouped_data, group_by):
                total_sales_by_date = grouped_data.groupby('Date')['Daily Sales'].sum().reset_index()
                grouped_data = grouped_data.merge(total_sales_by_date, on='Date', suffixes=(None, '_Total'))
                grouped_data['Percentage'] = (grouped_data['Daily Sales'] / grouped_data['Daily Sales_Total']) * 100
                return grouped_data
        
          simulation_data_platform = daily_sales.groupby(['Date', 'Platform'])['Daily Sales'].sum().reset_index()
          simulation_data_product = daily_sales.groupby(['Date', 'Product'])['Daily Sales'].sum().reset_index()
          simulation_data_platform = normalize_data(simulation_data_platform, 'Platform')
          simulation_data_product = normalize_data(simulation_data_product, 'Product')
  
          def update_kpis_and_charts():
                global current_day_sales, simulation_data_platform, simulation_data_product
        
                # Filter data for the selected platforms and products
                filtered_data = filter_data(current_day_sales, selected_platforms, selected_products)
        
                # KPI Calculation
                total_sales = filtered_data['Sales (15 min)'].sum()
                total_revenue = total_sales * 200  # Giả định giá mỗi sản phẩm là 200
                total_cost = total_revenue * 0.6  # Chi phí là 60% doanh thu
                total_profit = total_revenue - total_cost
        
                # Display KPIs
                with kpi_placeholder.container():
                    st.metric("Tổng Doanh Thu", f"{total_revenue:,.0f}", delta=f"+{total_sales:,} sản phẩm")
                    st.metric("Tổng Lợi Nhuận", f"{total_profit:,.0f}", delta=f"+{(total_profit):,.0f}")
        
                # Prepare data for the bar and line chart
                pivot_data = filtered_data.pivot_table(
                    index='Time', columns='Platform', values='Sales (15 min)', aggfunc='sum', fill_value=0
                )
        
                # Select visible data based on zoom level
                if len(pivot_data) > zoom_level:
                    visible_data = pivot_data.iloc[-zoom_level:]
                else:
                    visible_data = pivot_data
        
                # Create bar and line chart
                fig = go.Figure()
                for platform in selected_platforms:
                    if platform in visible_data.columns:
                        platform_top = visible_data[selected_platforms[:selected_platforms.index(platform)+1]].sum(axis=1)
                        fig.add_trace(go.Bar(
                            x=visible_data.index,
                            y=visible_data[platform],
                            name=f"{platform} (Bar)",
                            marker=dict(color=px.colors.qualitative.Plotly[selected_platforms.index(platform) % len(px.colors.qualitative.Plotly)])
                        ))
                        fig.add_trace(go.Scatter(
                            x=visible_data.index,
                            y=platform_top,  # Values at the top of the bar
                            mode='lines+markers',
                            name=f"{platform} (Line)",
                            line=dict(width=2),
                            marker=dict(size=8)
                        ))
        
                fig.update_layout(
                    barmode='stack',
                    title="Biểu Đồ Doanh Số Theo Thời Gian (Bar + Line)",
                    xaxis_title="Thời Gian",
                    yaxis_title="Số Lượng Bán",
                    xaxis=dict(rangeslider=dict(visible=True), type="date"),
                    height=500,
                    width =800,
                    template="plotly_white",
                    margin=dict(l=40, r=40, t=50, b=40),
                    legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center")
                )
                chart_placeholder.plotly_chart(fig, use_container_width=True)
        
                # Update area charts
                latest_date = simulation_data_platform['Date'].max()
                new_date = latest_date + pd.Timedelta(days=1)
                for group, simulation_data in [('Platform', simulation_data_platform), ('Product', simulation_data_product)]:
                    for value in simulation_data[group].unique():
                        new_percentage = np.random.uniform(5, 25)
                        new_entry = {
                            'Date': new_date,
                            group: value,
                            'Daily Sales': 0,
                            'Daily Sales_Total': 0,
                            'Percentage': new_percentage
                        }
                        simulation_data = pd.concat([simulation_data, pd.DataFrame([new_entry])], ignore_index=True)
                    for date in simulation_data['Date'].unique():
                        date_mask = simulation_data['Date'] == date
                        simulation_data.loc[date_mask, 'Percentage'] = (
                            simulation_data.loc[date_mask, 'Percentage'] /
                            simulation_data.loc[date_mask, 'Percentage'].sum()
                        ) * 100
                    if len(simulation_data['Date'].unique()) > 10:
                        oldest_date = simulation_data['Date'].min()
                        simulation_data = simulation_data[simulation_data['Date'] > oldest_date]
                    if group == 'Platform':
                        simulation_data_platform = simulation_data
                    else:
                        simulation_data_product = simulation_data
        
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
                area_placeholder1.plotly_chart(fig_area_platform, use_container_width=True)
        
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
                area_placeholder2.plotly_chart(fig_area_product, use_container_width=True)
          def adjust_time(data):
                    """
                    Adjust the time of the dataset to match the current time.
                    """
                    min_time = data['Time'].min()
                    current_time = pd.Timestamp.now().replace(second=0, microsecond=0)
                    time_diff = current_time - min_time
                    data['Time'] = data['Time'] + time_diff
                    return data
    current_day_sales = adjust_time(current_day_sales)
     
    recent_sales_for_table = current_day_sales.copy()        
# Hiển thị bảng cập nhật doanh số bên phải
    with right_col:
          st.markdown("<h3 style='text-align: center;'>Bảng Cập Nhật Doanh Số</h3>", unsafe_allow_html=True)

          def display_table(data, platform_name):
                """
                Hiển thị bảng cập nhật doanh số cho từng nền tảng.
                """
                if data.empty:
                    st.write("Không có dữ liệu.")
                else:
                    latest_data = data.tail(8)  # Chỉ lấy dữ liệu mới nhất
                    html_content = """
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                    """
                    for _, row in latest_data.iterrows():
                        html_content += format_box(
                            row['Product'],
                            row['Sales (15 min)'],
                            row['Time'].strftime('%H:%M')
                        )
                    html_content += "</div>"
                    st.markdown(html_content, unsafe_allow_html=True)

          shopee_placeholder = st.empty()
          tiktok_placeholder = st.empty()
          lazada_placeholder = st.empty()
            
            # Lấy dữ liệu bán hàng trong 15 phút gần nhất
          def update_recent_table_data():
                global recent_sales_for_table
                recent_sales_for_table = simulate_new_data(recent_sales_for_table)
        
         
        
          def refresh_tables():
                # Tách dữ liệu theo từng nền tảng
                shopee_data = recent_sales_for_table[recent_sales_for_table['Platform'] == "Shopee"]
                tiktok_data = recent_sales_for_table[recent_sales_for_table['Platform'] == "TikTok"]
                lazada_data = recent_sales_for_table[recent_sales_for_table['Platform'] == "Lazada"]
        
                # Hiển thị từng bảng
                 
                with shopee_placeholder.container():
                        st.markdown("<h4 style='text-align: left; color: black;'>Shopee</h4>", unsafe_allow_html=True)
                        display_table(shopee_data, "Shopee")

                with tiktok_placeholder.container():
                        st.markdown("<h4 style='text-align: left; color: black;'>TikTok</h4>", unsafe_allow_html=True)
                        display_table(tiktok_data, "TikTok")
                
                with lazada_placeholder.container():
                        st.markdown("<h4 style='text-align: left; color: black;'>Lazada</h4>", unsafe_allow_html=True)
                        display_table(lazada_data, "Lazada")
                          

# Continuous updates
    while True:
            current_day_sales = simulate_new_data(current_day_sales)  # Cập nhật dữ liệu
            update_kpis_and_charts()  # Cập nhật biểu đồ và KPI
            update_recent_table_data()
            refresh_tables()
            time.sleep(5)
