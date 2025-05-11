import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utilities
try:
    from utils.dashboard_utils import (
        load_data, 
        filter_data, 
        calculate_kpis,
        render_kpi_cards,
        apply_theme_to_figure,
        COLORS,
        CHART_COLORS,
        show_filters
    )
    
    from utils.state_management import get_state, update_state, init_state
except ImportError:
    st.error("Failed to import utilities. Please make sure all required files exist.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Business Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize state
init_state()

# Load data from files
sales_df, customer_df = load_data()

# Get min and max dates
if not sales_df.empty:
    min_date = sales_df['Date'].min().date()
    max_date = sales_df['Date'].max().date()
else:
    min_date = datetime.now().date()
    max_date = datetime.now().date()

# Load custom CSS from file
try:
    with open('assets/style.css', 'r') as f:
        custom_css = f.read()
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Custom styling not found. The dashboard will use default styling.")

# Add a version indicator
st.markdown('<div class="version-indicator">v1.1.0</div>', unsafe_allow_html=True)

# Add page navigation
st.markdown('<div class="tab-navigation">', unsafe_allow_html=True)
st.markdown('<a href="/" class="tab active">Overview</a>', unsafe_allow_html=True)
st.markdown('<a href="/Sales_Analytics" class="tab">Sales Analytics</a>', unsafe_allow_html=True)
st.markdown('<a href="/Customer_Insights" class="tab">Customer Insights</a>', unsafe_allow_html=True)
st.markdown('<a href="/Forecasting" class="tab">Forecasting</a>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Get state
state = get_state()
update_state({'active_tab': 'Overview'})

# Set up sidebar for filters
st.sidebar.markdown("<h2 style='color: #4E7CFF;'>Filters</h2>", unsafe_allow_html=True)

# Sidebar toggle
with st.sidebar:
    # Add a checkbox to toggle filter visibility
    show_filters_state = st.checkbox("Show Filters", value=True)
    
    if show_filters_state:
        # Date range filters and other filters
        start_date, end_date, selected_regions, selected_products, selected_segments = show_filters(
            sales_df, 
            customer_df, 
            state
        )
        
        # Save filter selections to state
        update_state({
            'start_date': start_date,
            'end_date': end_date,
            'selected_regions': selected_regions,
            'selected_products': selected_products,
            'selected_segments': selected_segments
        })
    else:
        # Use values from state or defaults
        start_date = state.get('start_date', min_date)
        end_date = state.get('end_date', max_date)
        selected_regions = state.get('selected_regions', sales_df['Region'].unique().tolist())
        selected_products = state.get('selected_products', sales_df['Product'].unique().tolist())
        selected_segments = state.get('selected_segments', customer_df['Segment'].unique().tolist())
    
    # Add info and reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Reset Filters", key="reset_filters"):
        update_state({
            'start_date': min_date,
            'end_date': max_date,
            'selected_regions': sales_df['Region'].unique().tolist(),
            'selected_products': sales_df['Product'].unique().tolist(),
            'selected_segments': customer_df['Segment'].unique().tolist()
        })
        st.rerun()
    
    # Theme toggle
    theme_options = ["Dark Theme", "Light Theme"]
    selected_theme = st.selectbox(
        "Select Theme",
        options=theme_options,
        index=0 if state.get('theme', 'Dark Theme') == 'Dark Theme' else 1
    )
    
    if selected_theme != state.get('theme', 'Dark Theme'):
        update_state({'theme': selected_theme})
        st.rerun()
    
    # Add dashboard features and help
    with st.expander("Dashboard Features"):
        st.write("""
        - Cross-filtering: Click on chart elements to filter data
        - Export functionality: Download data and visualizations
        - Saved views: Save and load your filtering configurations
        - Anomaly detection: Automatic highlighting of unusual patterns
        """)
    
    # Add option to save/load views
    with st.expander("Saved Views"):
        # Get saved views from state
        saved_views = state.get('saved_views', [])
        
        # Option to save current view
        if st.button("+ Save Current View"):
            view_name = st.text_input("View Name", value="My View")
            view_desc = st.text_area("Description", value="")
            
            if st.button("Save"):
                from utils.state_management import save_view
                save_view(view_name, view_desc)
                st.success(f"View '{view_name}' saved!")
                st.rerun()
        
        # Display saved views
        if saved_views:
            st.write("### Your Saved Views")
            for i, view in enumerate(saved_views):
                st.write(f"**{view.get('name')}**")
                if st.button(f"Load", key=f"load_view_{i}"):
                    from utils.state_management import load_view
                    load_view(view.get('name'))
                    st.success(f"View '{view.get('name')}' loaded!")
                    st.rerun()

# Dashboard Header - Main content
st.markdown("<h1 class='dashboard-header'>Business Analytics Dashboard</h1>", unsafe_allow_html=True)

# Display notification
st.markdown(
    """
    <div class='notification'>
        <div class='notification-icon'>ℹ️</div>
        <div class='notification-content'>
            <p><strong>Dashboard updated!</strong> Data is current as of May 01, 2025.</p>
        </div>
        <div class='notification-close'>×</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# Filter data based on selections
filtered_sales_df, filtered_customer_df = filter_data(
    sales_df, customer_df, 
    start_date, end_date, 
    selected_regions, selected_products, selected_segments
)

# Calculate KPIs with trends
kpis = calculate_kpis(filtered_sales_df, comparison_period=30)

# KPI Cards Section
st.markdown("<h3 style='margin-top:20px;'>Key Performance Indicators</h3>", unsafe_allow_html=True)

# Render KPI cards with trend indicators
render_kpi_cards(kpis)

# Create main dashboard tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Sales Analysis", "Customer Insights"])

with tab1:
    # Sales Overview
    import plotly.express as px
    import plotly.graph_objects as go
    
    # First row - Regional Distribution and Time Trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Regional Sales Distribution</h3>", unsafe_allow_html=True)
        
        # Aggregate data by region
        region_sales = filtered_sales_df.groupby('Region')['Sales'].sum().reset_index()
        
        # Calculate percentages
        total_sales = region_sales['Sales'].sum()
        region_sales['Percentage'] = (region_sales['Sales'] / total_sales * 100).round(1)
        region_sales['Label'] = region_sales['Region'] + ' (' + region_sales['Percentage'].astype(str) + '%)'
        
        # Create donut chart
        fig_donut_region = px.pie(
            region_sales,
            values='Sales',
            names='Region',
            hole=0.6,
            color_discrete_sequence=CHART_COLORS
        )
        
        # Add total sales in the center
        fig_donut_region.add_annotation(
            text=f"<b>${total_sales:,.0f}</b><br>Total Sales",
            x=0.5, y=0.5,
            font=dict(size=14, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
            showarrow=False
        )
        
        # Apply theme
        fig_donut_region = apply_theme_to_figure(fig_donut_region, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_donut_region.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        fig_donut_region.update_traces(
            textinfo='percent',
            textfont=dict(size=12, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
            marker=dict(line=dict(color=COLORS['background'] if selected_theme == 'Dark Theme' else COLORS['light_bg'], width=1)),
            hovertemplate='<b>%{label}</b><br>Sales: $%{value:,.2f}<br>Share: %{percent}<extra></extra>'
        )
        
        st.plotly_chart(fig_donut_region, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Sales Over Time</h3>", unsafe_allow_html=True)
        
        # Aggregate data by date
        daily_sales = filtered_sales_df.groupby(filtered_sales_df['Date'].dt.date)['Sales'].sum().reset_index()
        daily_sales = daily_sales.sort_values('Date')
        
        # Calculate moving average
        daily_sales['MA'] = daily_sales['Sales'].rolling(window=7, min_periods=1).mean()
        
        # Create line chart
        fig_trends = go.Figure()
        
        # Add sales line
        fig_trends.add_trace(go.Scatter(
            x=daily_sales['Date'], 
            y=daily_sales['Sales'],
            mode='lines',
            name='Daily Sales',
            line=dict(color=COLORS['accent'], width=1),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Sales: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add moving average line
        fig_trends.add_trace(go.Scatter(
            x=daily_sales['Date'], 
            y=daily_sales['MA'],
            mode='lines',
            name='7-Day MA',
            line=dict(color=COLORS['highlight'], width=2.5, dash='dot'),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>7-Day MA: $%{y:,.2f}<extra></extra>'
        ))
        
        # Apply theme
        fig_trends = apply_theme_to_figure(fig_trends, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_trends.update_layout(
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title=dict(text='Date')),
            yaxis=dict(title=dict(text='Sales ($)')),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_trends, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Sales by Product 
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Sales by Product</h3>", unsafe_allow_html=True)
    
    # Aggregate data by product
    product_sales = filtered_sales_df.groupby('Product')['Sales'].sum().reset_index()
    product_sales = product_sales.sort_values('Sales', ascending=False)
    
    # Create bar chart
    fig_bar = px.bar(
        product_sales, 
        x='Product', 
        y='Sales',
        color='Product',
        color_discrete_sequence=CHART_COLORS,
        labels={'Sales': 'Total Sales ($)', 'Product': 'Product Category'},
        template="plotly_white"
    )
    
    # Apply theme
    fig_bar = apply_theme_to_figure(fig_bar, is_dark=(selected_theme == 'Dark Theme'))
    
    # Add data labels
    for i, row in enumerate(product_sales.iterrows()):
        fig_bar.add_annotation(
            x=row[1]['Product'],
            y=row[1]['Sales'],
            text=f"${row[1]['Sales']:,.0f}",
            showarrow=False,
            yshift=10,
            font=dict(color="white" if selected_theme == 'Dark Theme' else "black", size=10)
        )
    
    # Update layout
    fig_bar.update_layout(
        height=400,
        legend_title_text=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    fig_bar.update_traces(
        marker_line_color='rgba(0,0,0,0)',
        marker_line_width=1.5,
        opacity=0.9,
        hovertemplate='<b>%{x}</b><br>Sales: $%{y:,.2f}<extra></extra>'
    )
    
    # Add download button for the chart
    col1, col2 = st.columns([6, 1])
    with col1:
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.download_button(
            label="📥",
            data=product_sales.to_csv(index=False),
            file_name="product_sales.csv",
            mime="text/csv",
            help="Download this chart data"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    # Sales Analysis Tab
    # Sales Hierarchy
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Sales Hierarchy by Region and Product</h3>", unsafe_allow_html=True)
    
    # Aggregate data for treemap
    treemap_data = filtered_sales_df.groupby(['Region', 'Product'])['Sales'].sum().reset_index()
    
    # Create treemap
    fig_treemap = px.treemap(
        treemap_data,
        path=['Region', 'Product'],
        values='Sales',
        color='Sales',
        color_continuous_scale=px.colors.sequential.Blues,
        labels={'Sales': 'Total Sales ($)'}
    )
    
    # Apply theme
    fig_treemap = apply_theme_to_figure(fig_treemap, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_treemap.update_layout(
        height=450,
        coloraxis_showscale=False
    )
    
    fig_treemap.update_traces(
        marker=dict(cornerradius=5),
        textfont=dict(size=12, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
        hovertemplate='<b>%{label}</b><br>Sales: $%{value:,.2f}<extra></extra>'
    )
    
    st.plotly_chart(fig_treemap, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Monthly Sales Analysis
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Monthly Sales Analysis</h3>", unsafe_allow_html=True)
    
    # Group by month and year
    filtered_sales_df['Year'] = filtered_sales_df['Date'].dt.year
    filtered_sales_df['Month'] = filtered_sales_df['Date'].dt.month_name()
    
    monthly_sales = filtered_sales_df.groupby(['Year', 'Month'])['Sales'].sum().reset_index()
    
    # Create bar chart for monthly trends
    fig_monthly = px.bar(
        monthly_sales,
        x='Month',
        y='Sales',
        color='Year',
        barmode='group',
        labels={'Sales': 'Total Sales ($)', 'Month': 'Month', 'Year': 'Year'},
        color_discrete_sequence=CHART_COLORS
    )
    
    # Apply theme  
    fig_monthly = apply_theme_to_figure(fig_monthly, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_monthly.update_layout(
        height=350,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            categoryorder='array',
            categoryarray=['January', 'February', 'March', 'April', 'May', 'June', 
                         'July', 'August', 'September', 'October', 'November', 'December']
        )
    )
    
    st.plotly_chart(fig_monthly, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Product Mix by Region
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Product Mix by Region</h3>", unsafe_allow_html=True)
    
    # Aggregate data by region and product
    product_mix = filtered_sales_df.groupby(['Region', 'Product'])['Sales'].sum().reset_index()
    
    # Create a grouped bar chart
    fig_product_mix = px.bar(
        product_mix,
        x='Region',
        y='Sales',
        color='Product',
        barmode='group',
        color_discrete_sequence=CHART_COLORS,
        labels={'Sales': 'Total Sales ($)', 'Region': 'Region', 'Product': 'Product Category'}
    )
    
    # Apply theme
    fig_product_mix = apply_theme_to_figure(fig_product_mix, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_product_mix.update_layout(
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        bargap=0.2,
        bargroupgap=0.1
    )
    
    fig_product_mix.update_traces(
        hovertemplate='<b>%{x} - %{fullData.name}</b><br>Sales: $%{y:,.2f}<extra></extra>'
    )
    
    st.plotly_chart(fig_product_mix, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    # Customer Insights Tab
    # Customer Segment Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Segment Distribution</h3>", unsafe_allow_html=True)
        
        # Aggregate data by segment
        segment_data = filtered_customer_df.groupby('Segment')['Customer Count'].sum().reset_index()
        segment_data = segment_data.sort_values('Customer Count', ascending=False)
        
        # Create donut chart
        fig_donut = px.pie(
            segment_data,
            values='Customer Count',
            names='Segment',
            hole=0.6,
            color_discrete_sequence=CHART_COLORS
        )
        
        # Apply theme
        fig_donut = apply_theme_to_figure(fig_donut, is_dark=(selected_theme == 'Dark Theme'))
        
        # Add total in the center
        total_customers = segment_data['Customer Count'].sum()
        fig_donut.add_annotation(
            text=f"<b>{total_customers:,}</b><br>Customers",
            x=0.5, y=0.5,
            font=dict(size=14, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
            showarrow=False
        )
        
        # Update layout
        fig_donut.update_layout(
            height=350,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Segment Funnel</h3>", unsafe_allow_html=True)
        
        # Create funnel chart
        fig_funnel = go.Figure(go.Funnel(
            y=segment_data['Segment'],
            x=segment_data['Customer Count'],
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(color=CHART_COLORS[:len(segment_data)]),
            hovertemplate='<b>%{y}</b><br>Customers: %{x:,}<extra></extra>'
        ))
        
        # Apply theme
        fig_funnel = apply_theme_to_figure(fig_funnel, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_funnel.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Satisfaction by Segment (if available)
    if 'Satisfaction' in filtered_customer_df.columns:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Satisfaction by Segment</h3>", unsafe_allow_html=True)
        
        # Calculate average satisfaction by segment
        satisfaction_by_segment = filtered_customer_df.groupby('Segment')['Satisfaction'].mean().reset_index()
        satisfaction_by_segment['Satisfaction'] = satisfaction_by_segment['Satisfaction'].round(2)
        satisfaction_by_segment = satisfaction_by_segment.sort_values('Satisfaction', ascending=False)
        
        # Create bar chart for satisfaction
        fig_satisfaction = px.bar(
            satisfaction_by_segment,
            x='Segment',
            y='Satisfaction',
            color='Satisfaction',
            color_continuous_scale=[
                [0, 'rgb(165,0,38)'],   # Low satisfaction (red)
                [0.5, 'rgb(255,220,0)'],  # Medium satisfaction (yellow)
                [1, 'rgb(0,104,55)']    # High satisfaction (green)
            ],
            labels={'Satisfaction': 'Satisfaction Score', 'Segment': 'Customer Segment'},
            text='Satisfaction'
        )
        
        # Apply theme
        fig_satisfaction = apply_theme_to_figure(fig_satisfaction, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_satisfaction.update_layout(
            height=350,
            coloraxis_showscale=False
        )
        
        fig_satisfaction.update_traces(
            textposition='outside',
            textfont=dict(size=12, color='white' if selected_theme == 'Dark Theme' else 'black')
        )
        
        st.plotly_chart(fig_satisfaction, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Key Insights Section
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown("<h3>Key Insights</h3>", unsafe_allow_html=True)

# Create columns for insights
col1, col2, col3 = st.columns(3)

with col1:
    # Top product by sales
    top_product = product_sales.iloc[0]['Product']
    top_product_sales = product_sales.iloc[0]['Sales']
    
    st.markdown(f"""
    <div class='insight-card'>
        <div class='insight-icon'>🏆</div>
        <div class='insight-content'>
            <h4>Top Performing Product</h4>
            <p class='insight-value'>{top_product}</p>
            <p class='insight-detail'>${top_product_sales:,.2f} in total sales</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Top region by sales
    top_region = region_sales.iloc[0]['Region']
    top_region_sales = region_sales.iloc[0]['Sales']
    
    st.markdown(f"""
    <div class='insight-card'>
        <div class='insight-icon'>📍</div>
        <div class='insight-content'>
            <h4>Leading Market Region</h4>
            <p class='insight-value'>{top_region}</p>
            <p class='insight-detail'>${top_region_sales:,.2f} in total sales</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Largest customer segment
    if 'Segment' in filtered_customer_df.columns:
        top_segment = segment_data.iloc[0]['Segment']
        top_segment_count = segment_data.iloc[0]['Customer Count']
        
        st.markdown(f"""
        <div class='insight-card'>
            <div class='insight-icon'>👥</div>
            <div class='insight-content'>
                <h4>Primary Customer Segment</h4>
                <p class='insight-value'>{top_segment}</p>
                <p class='insight-detail'>{top_segment_count:,} customers</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Alternative insight if segment data is not available
        st.markdown(f"""
        <div class='insight-card'>
            <div class='insight-icon'>📈</div>
            <div class='insight-content'>
                <h4>Average Sales Value</h4>
                <p class='insight-value'>${kpis['avg_sale_raw']:,.2f}</p>
                <p class='insight-detail'>Per unit sold</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
    <p>Business Analytics Dashboard | Created with Streamlit and Plotly</p>
    <p>© 2025 Business Analytics Inc. | Last updated: May 01, 2025</p>
</div>
""", unsafe_allow_html=True)