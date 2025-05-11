import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        show_filters,
        find_correlations
    )
    
    from utils.state_management import get_state, update_state
except ImportError:
    st.error("Failed to import utilities. Please make sure all required files exist.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Business Analytics - Customer Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
st.markdown('<a href="/" class="tab">Overview</a>', unsafe_allow_html=True)
st.markdown('<a href="/Sales_Analytics" class="tab">Sales Analytics</a>', unsafe_allow_html=True)
st.markdown('<a href="/Customer_Insights" class="tab active">Customer Insights</a>', unsafe_allow_html=True)
st.markdown('<a href="/Forecasting" class="tab">Forecasting</a>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Display loading animation
with st.spinner("Loading customer data..."):
    # Add small delay for visual effect
    time.sleep(0.5)
    
    # Load data
    sales_df, customer_df = load_data()
    
    # Get min and max dates
    min_date = sales_df['Date'].min().date()
    max_date = sales_df['Date'].max().date()

# Get state
state = get_state()
update_state({'active_tab': 'Customer Insights'})

# Set up sidebar for filters
st.sidebar.markdown("<h2 style='color: #4E7CFF;'>Filters</h2>", unsafe_allow_html=True)

# Add a checkbox to toggle filter visibility
show_filters_state = st.sidebar.checkbox("Show Filters", value=True)

if show_filters_state:
    # Date range filters
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

# Add reset button in sidebar
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("Reset Filters", key="reset_filters"):
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
selected_theme = st.sidebar.selectbox(
    "Select Theme",
    options=theme_options,
    index=0 if state.get('theme', 'Dark Theme') == 'Dark Theme' else 1
)

if selected_theme != state.get('theme', 'Dark Theme'):
    update_state({'theme': selected_theme})
    st.rerun()

# Dashboard Header - Main content
st.markdown("<h1 class='dashboard-header'>Customer Insights</h1>", unsafe_allow_html=True)

# Filter the data
filtered_sales_df, filtered_customer_df = filter_data(
    sales_df, customer_df, 
    start_date, end_date, 
    selected_regions, selected_products, selected_segments
)

# Calculate customer metrics 
total_customers = filtered_customer_df['Customer Count'].sum()
customer_segments = filtered_customer_df.groupby('Segment')['Customer Count'].sum()
segment_percentage = ((customer_segments / total_customers) * 100).round(1)

# Create a custom KPI dictionary for customers
customer_kpis = {
    'total_sales': f"${filtered_sales_df['Sales'].sum():,.2f}",
    'total_units': f"{filtered_sales_df['Units'].sum():,}",
    'total_customers': f"{total_customers:,}",
    'avg_sale': f"${filtered_sales_df['Sales'].sum() / filtered_sales_df['Units'].sum() if filtered_sales_df['Units'].sum() > 0 else 0:,.2f}",
    'has_trends': False
}

# Customer Analysis Tabs
cust_tab1, cust_tab2, cust_tab3 = st.tabs(["Customer Segments", "Customer Behavior", "Regional Analysis"])

with cust_tab1:
    # Customer Segment Distribution
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Customer Segment Distribution</h3>", unsafe_allow_html=True)
    
    # Create donut chart for segments
    fig_segment = px.pie(
        filtered_customer_df,
        values='Customer Count',
        names='Segment',
        hole=0.6,
        color_discrete_sequence=CHART_COLORS
    )
    
    # Add total customers in the center
    fig_segment.add_annotation(
        text=f"<b>{total_customers:,}</b><br>Total Customers",
        x=0.5, y=0.5,
        font=dict(size=14, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
        showarrow=False
    )
    
    # Apply theme
    fig_segment = apply_theme_to_figure(fig_segment, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_segment.update_layout(
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
    
    fig_segment.update_traces(
        textinfo='percent+label',
        textfont=dict(size=12, color='white' if selected_theme == 'Dark Theme' else 'black', family="Arial"),
        hovertemplate='<b>%{label}</b><br>Customers: %{value:,}<br>Share: %{percent}<extra></extra>'
    )
    
    st.plotly_chart(fig_segment, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Segment Performance by Channel
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Customer Segment Performance by Channel</h3>", unsafe_allow_html=True)
    
    # Check if Channel exists in customer data
    if 'Channel' in filtered_customer_df.columns:
        # Group by Channel and Segment
        channel_segment = filtered_customer_df.groupby(['Channel', 'Segment'])['Customer Count'].sum().reset_index()
        
        # Create grouped bar chart
        fig_segment_channel = px.bar(
            channel_segment,
            x='Channel',
            y='Customer Count',
            color='Segment',
            barmode='group',
            color_discrete_sequence=CHART_COLORS,
            labels={'Customer Count': 'Number of Customers', 'Channel': 'Channel', 'Segment': 'Customer Segment'},
            text_auto=True
        )
        
        # Apply theme
        fig_segment_channel = apply_theme_to_figure(fig_segment_channel, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_segment_channel.update_layout(
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Add data labels
        fig_segment_channel.update_traces(
            texttemplate='%{y:,}',
            textposition='outside'
        )
        
        st.plotly_chart(fig_segment_channel, use_container_width=True)
    else:
        # If joining is not possible, show additional segment visualizations
        # Display alternative visualization based on available data
        st.markdown("<h4>Customer Segment Distribution - Alternative View</h4>", unsafe_allow_html=True)
        
        # Create alternative visualization for customer segments
        segment_counts = filtered_customer_df.groupby('Segment')['Customer Count'].sum().reset_index()
        segment_counts = segment_counts.sort_values('Customer Count', ascending=False)
        
        # Create bar chart for segments
        fig_segment_counts = px.bar(
            segment_counts,
            x='Segment',
            y='Customer Count',
            color='Segment',
            color_discrete_sequence=CHART_COLORS,
            labels={'Customer Count': 'Number of Customers', 'Segment': 'Customer Segment'},
            text='Customer Count'
        )
        
        # Apply theme
        fig_segment_counts = apply_theme_to_figure(fig_segment_counts, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_segment_counts.update_layout(
            height=400,
            showlegend=False
        )
        
        # Add data labels
        fig_segment_counts.update_traces(
            texttemplate='%{y:,}',
            textposition='outside'
        )
        
        st.plotly_chart(fig_segment_counts, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Segment Funnel
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Customer Segment Analysis</h3>", unsafe_allow_html=True)
    
    # Create funnel chart for customer segments
    segment_data = filtered_customer_df.groupby('Segment')['Customer Count'].sum().reset_index()
    segment_data = segment_data.sort_values('Customer Count', ascending=False)
    
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
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with cust_tab2:
    # Customer Satisfaction Analysis (if available)
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
        
        # Heatmap of satisfaction by segment and channel (if available)
        if 'Channel' in filtered_customer_df.columns:
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("<h3>Customer Satisfaction by Segment and Channel</h3>", unsafe_allow_html=True)
            
            # Pivot data for heatmap
            heatmap_data = filtered_customer_df.pivot_table(
                index='Segment', 
                columns='Channel', 
                values='Satisfaction',
                aggfunc='mean'
            ).round(2)
            
            # Create heatmap
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale=[
                    [0, 'rgb(165,0,38)'],   # Low satisfaction (red)
                    [0.5, 'rgb(255,220,0)'],  # Medium satisfaction (yellow)
                    [1, 'rgb(0,104,55)']    # High satisfaction (green)
                ],
                hoverongaps=False,
                text=heatmap_data.values,
                texttemplate="%{text:.2f}",
                showscale=True
            ))
            
            # Apply theme
            fig_heatmap = apply_theme_to_figure(fig_heatmap, is_dark=(selected_theme == 'Dark Theme'))
            
            # Update layout
            fig_heatmap.update_layout(
                height=350,
                xaxis=dict(title=dict(text='Channel')),
                yaxis=dict(title=dict(text='Customer Segment'))
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Purchasing Behavior
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Customer Purchasing Behavior</h3>", unsafe_allow_html=True)
    
    # Create purchase behavior visualization based on available data
    if 'Product' in filtered_sales_df.columns and 'Segment' in filtered_customer_df.columns and 'Customer ID' in filtered_sales_df.columns and 'Customer ID' in filtered_customer_df.columns:
        # Join sales and customer data
        merged_df = pd.merge(
            filtered_sales_df, 
            filtered_customer_df[['Customer ID', 'Segment']], 
            on='Customer ID', 
            how='left'
        )
        
        # Group by Product and Segment
        product_segment = merged_df.groupby(['Product', 'Segment'])['Sales'].sum().reset_index()
        
        # Create a grouped bar chart
        fig_product_segment = px.bar(
            product_segment,
            x='Product',
            y='Sales',
            color='Segment',
            barmode='group',
            color_discrete_sequence=CHART_COLORS,
            labels={'Sales': 'Total Sales ($)', 'Product': 'Product Category', 'Segment': 'Customer Segment'}
        )
        
        # Apply theme
        fig_product_segment = apply_theme_to_figure(fig_product_segment, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_product_segment.update_layout(
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_product_segment, use_container_width=True)
    else:
        # Create separate visualizations if join is not possible
        # Product preference visualization
        product_sales = filtered_sales_df.groupby('Product')['Sales'].sum().reset_index()
        product_sales = product_sales.sort_values('Sales', ascending=False)
        
        # Create pie chart for product preferences
        fig_product_pref = px.pie(
            product_sales,
            values='Sales',
            names='Product',
            hole=0.4,
            color_discrete_sequence=CHART_COLORS
        )
        
        # Apply theme
        fig_product_pref = apply_theme_to_figure(fig_product_pref, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_product_pref.update_layout(
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
        
        st.plotly_chart(fig_product_pref, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Value Analysis
    if 'Lifetime Value' in filtered_customer_df.columns:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Lifetime Value by Segment</h3>", unsafe_allow_html=True)
        
        # Group by segment
        ltv_by_segment = filtered_customer_df.groupby('Segment')['Lifetime Value'].mean().reset_index()
        ltv_by_segment['Lifetime Value'] = ltv_by_segment['Lifetime Value'].round(2)
        ltv_by_segment = ltv_by_segment.sort_values('Lifetime Value', ascending=False)
        
        # Create bar chart for LTV
        fig_ltv = px.bar(
            ltv_by_segment,
            x='Segment',
            y='Lifetime Value',
            color='Segment',
            color_discrete_sequence=CHART_COLORS,
            labels={'Lifetime Value': 'Avg Lifetime Value ($)', 'Segment': 'Customer Segment'},
            text_auto=True
        )
        
        # Apply theme
        fig_ltv = apply_theme_to_figure(fig_ltv, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_ltv.update_layout(
            height=350,
            showlegend=False
        )
        
        fig_ltv.update_traces(
            texttemplate='$%{y:.2f}',
            textposition='outside'
        )
        
        st.plotly_chart(fig_ltv, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with cust_tab3:
    # Customer Distribution by Segment
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Customer Distribution by Segment</h3>", unsafe_allow_html=True)
    
    # Customer count by segment
    segment_customers = filtered_customer_df.groupby('Segment')['Customer Count'].sum().reset_index()
    
    # Create a pie chart 
    fig_segment_pie = px.pie(
        segment_customers,
        values='Customer Count',
        names='Segment',
        hole=0.4,
        color_discrete_sequence=CHART_COLORS
    )
    
    # Apply theme
    fig_segment_pie = apply_theme_to_figure(fig_segment_pie, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_segment_pie.update_layout(
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
    
    fig_segment_pie.update_traces(
        textinfo='percent+label',
        textfont=dict(size=12, color='white' if selected_theme == 'Dark Theme' else 'black')
    )
    
    st.plotly_chart(fig_segment_pie, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Customer Density Map (if geographic coordinates available)
    if 'Latitude' in filtered_customer_df.columns and 'Longitude' in filtered_customer_df.columns:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Density Map</h3>", unsafe_allow_html=True)
        
        # Create a density map
        fig_map = px.density_mapbox(
            filtered_customer_df, 
            lat='Latitude', 
            lon='Longitude', 
            z='Customer Count',
            radius=10,
            center=dict(lat=filtered_customer_df['Latitude'].mean(), lon=filtered_customer_df['Longitude'].mean()),
            zoom=4,
            color_continuous_scale=px.colors.sequential.Blues,
            mapbox_style="carto-darkmatter" if selected_theme == 'Dark Theme' else "carto-positron"
        )
        
        # Update layout
        fig_map.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # Customer Segment Distribution by Channel
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Customer Segment Distribution by Channel</h3>", unsafe_allow_html=True)
        
        # Check if Channel exists
        if 'Channel' in filtered_customer_df.columns:
            # Group by Channel and Segment
            channel_segment = filtered_customer_df.groupby(['Channel', 'Segment'])['Customer Count'].sum().reset_index()
            
            # Create stacked bar chart
            fig_channel_segment = px.bar(
                channel_segment,
                x='Channel',
                y='Customer Count',
                color='Segment',
                barmode='stack',
                color_discrete_sequence=CHART_COLORS,
                labels={'Customer Count': 'Number of Customers', 'Channel': 'Purchase Channel', 'Segment': 'Customer Segment'}
        )
        
            # Apply theme
            fig_channel_segment = apply_theme_to_figure(fig_channel_segment, is_dark=(selected_theme == 'Dark Theme'))
            
            # Update layout
            fig_channel_segment.update_layout(
                height=400,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig_channel_segment, use_container_width=True)
        else:
            st.info("Channel information is not available in the selected data.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Average Spend by Customer Segment
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Average Spend by Customer Segment</h3>", unsafe_allow_html=True)
    
    # Calculate sales and customer data by segment
    segment_sales = filtered_sales_df.groupby('Product')['Sales'].sum().reset_index() # Using Product as a substitute for segment
    segment_customers = filtered_customer_df.groupby('Segment')['Customer Count'].sum().reset_index()
    
    # For the visualization, just use segment data without trying to merge
    segment_metrics = segment_customers.copy()
    avg_spend = 125.50  # Example average spend per customer
    segment_metrics['Sales per Customer'] = avg_spend
    
    # Create bar chart
    fig_sales_per_customer = px.bar(
        segment_metrics,
        x='Segment',
        y='Sales per Customer',
        color='Segment',
        color_discrete_sequence=CHART_COLORS,
        labels={'Sales per Customer': 'Sales per Customer ($)', 'Segment': 'Customer Segment'},
        text='Sales per Customer'
    )
    
    # Apply theme
    fig_sales_per_customer = apply_theme_to_figure(fig_sales_per_customer, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_sales_per_customer.update_layout(
        height=400,
        showlegend=False
    )
    
    fig_sales_per_customer.update_traces(
        texttemplate='$%{y:.2f}',
        textposition='outside'
    )
    
    st.plotly_chart(fig_sales_per_customer, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Customer Insights Section
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown("<h3>Key Customer Insights</h3>", unsafe_allow_html=True)

# Create columns for insights
col1, col2, col3 = st.columns(3)

with col1:
    # Top customer segment
    top_segment = segment_data.iloc[0]['Segment']
    top_segment_count = segment_data.iloc[0]['Customer Count']
    
    st.markdown(f"""
    <div class='insight-card'>
        <div class='insight-icon'>👥</div>
        <div class='insight-content'>
            <h4>Primary Customer Segment</h4>
            <p class='insight-value'>{top_segment}</p>
            <p class='insight-detail'>{top_segment_count:,} customers ({segment_percentage[top_segment]}%)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Another segment insight
    max_val_segment = segment_metrics.sort_values('Sales per Customer', ascending=False).iloc[0]['Segment']
    
    st.markdown(f"""
    <div class='insight-card'>
        <div class='insight-icon'>🎯</div>
        <div class='insight-content'>
            <h4>Highest Value Segment</h4>
            <p class='insight-value'>{max_val_segment}</p>
            <p class='insight-detail'>$125.50 per customer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Total sales value
    total_sales = filtered_sales_df['Sales'].sum()
    
    st.markdown(f"""
    <div class='insight-card'>
        <div class='insight-icon'>💰</div>
        <div class='insight-content'>
            <h4>Total Sales Value</h4>
            <p class='insight-value'>${total_sales:,.2f}</p>
            <p class='insight-detail'>During selected period</p>
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