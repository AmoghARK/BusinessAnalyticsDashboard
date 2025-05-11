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
        detect_anomalies
    )
    
    from utils.state_management import get_state, update_state
except ImportError:
    st.error("Failed to import utilities. Please make sure all required files exist.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Business Analytics - Sales",
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
st.markdown('<a href="/Sales_Analytics" class="tab active">Sales Analytics</a>', unsafe_allow_html=True)
st.markdown('<a href="/Customer_Insights" class="tab">Customer Insights</a>', unsafe_allow_html=True)
st.markdown('<a href="/Forecasting" class="tab">Forecasting</a>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Display loading animation
with st.spinner("Loading sales data..."):
    # Add small delay for visual effect
    time.sleep(0.5)
    
    # Load data
    sales_df, customer_df = load_data()
    
    # Get min and max dates
    min_date = sales_df['Date'].min().date()
    max_date = sales_df['Date'].max().date()

# Get state
state = get_state()
update_state({'active_tab': 'Sales Analytics'})

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

# Add info and reset button in sidebar
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
st.markdown("<h1 class='dashboard-header'>Sales Analytics</h1>", unsafe_allow_html=True)

# Filter the data
filtered_sales_df, filtered_customer_df = filter_data(
    sales_df, customer_df, 
    start_date, end_date, 
    selected_regions, selected_products, selected_segments
)

# Calculate KPIs with trends
kpis = calculate_kpis(filtered_sales_df, comparison_period=30)

# KPI Cards Section
st.markdown("<h3 style='margin-top:20px;'>Sales Performance Metrics</h3>", unsafe_allow_html=True)

# Render KPI cards with trend indicators
render_kpi_cards(kpis)

# Sales Analysis Tabs
sales_tab1, sales_tab2, sales_tab3 = st.tabs(["Sales Distribution", "Time Analysis", "Advanced Analytics"])

with sales_tab1:
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
    
    st.plotly_chart(fig_bar, use_container_width=True)
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
    
    # Sales Hierarchy Treemap
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
        hover_data={'Sales': ':.2f'},
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

with sales_tab2:
    # Sales Time Series Analysis
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Sales Trends Over Time</h3>", unsafe_allow_html=True)
    
    # Aggregate data by date
    daily_sales = filtered_sales_df.groupby(filtered_sales_df['Date'].dt.date)['Sales'].sum().reset_index()
    daily_sales = daily_sales.sort_values('Date')
    
    # Calculate moving average
    daily_sales['MA7'] = daily_sales['Sales'].rolling(window=7, min_periods=1).mean()
    daily_sales['MA30'] = daily_sales['Sales'].rolling(window=30, min_periods=1).mean()
    
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
    
    # Add 7-day moving average line
    fig_trends.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['MA7'],
        mode='lines',
        name='7-Day MA',
        line=dict(color=COLORS['highlight'], width=2.5, dash='dot'),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>7-Day MA: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add 30-day moving average line
    fig_trends.add_trace(go.Scatter(
        x=daily_sales['Date'], 
        y=daily_sales['MA30'],
        mode='lines',
        name='30-Day MA',
        line=dict(color=COLORS['positive'], width=2.5, dash='dash'),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>30-Day MA: $%{y:,.2f}<extra></extra>'
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
    
    # Heatmap of Sales by Day and Hour (if available)
    if 'Hour' in filtered_sales_df.columns:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("<h3>Sales Heatmap by Day and Hour</h3>", unsafe_allow_html=True)
        
        # Add day of week
        filtered_sales_df['DayOfWeek'] = filtered_sales_df['Date'].dt.day_name()
        
        # Pivot data for heatmap
        heatmap_data = filtered_sales_df.pivot_table(
            index='DayOfWeek', 
            columns='Hour', 
            values='Sales',
            aggfunc='sum'
        ).fillna(0)
        
        # Set correct day order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(day_order)
        
        # Create heatmap
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Hour of Day", y="Day of Week", color="Sales ($)"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        # Apply theme
        fig_heatmap = apply_theme_to_figure(fig_heatmap, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_heatmap.update_layout(
            height=350
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with sales_tab3:
    # Anomaly Detection
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Sales Anomaly Detection</h3>", unsafe_allow_html=True)
    
    # Anomaly detection controls
    col1, col2 = st.columns([1, 3])
    with col1:
        window_size = st.slider("Moving Average Window", min_value=3, max_value=30, value=7, step=1)
        threshold = st.slider("Anomaly Threshold (σ)", min_value=1, max_value=5, value=2, step=1)
    
    # Detect anomalies in sales data
    daily_sales = filtered_sales_df.groupby(filtered_sales_df['Date'].dt.date)['Sales'].sum().reset_index()
    anomalies = detect_anomalies(daily_sales, 'Sales', window=window_size, threshold=threshold)
    
    if not anomalies.empty:
        # Create line chart with anomalies highlighted
        fig_anomalies = go.Figure()
        
        # Add regular sales line
        fig_anomalies.add_trace(go.Scatter(
            x=daily_sales['Date'], 
            y=daily_sales['Sales'],
            mode='lines',
            name='Daily Sales',
            line=dict(color=COLORS['accent'], width=1),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Sales: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add anomalies as points
        fig_anomalies.add_trace(go.Scatter(
            x=anomalies['Date'],
            y=anomalies['Sales'],
            mode='markers',
            name='Anomalies',
            marker=dict(
                color='red',
                size=10,
                symbol='circle',
                line=dict(color='white', width=1)
            ),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Anomaly: $%{y:,.2f}<extra></extra>'
        ))
        
        # Apply theme
        fig_anomalies = apply_theme_to_figure(fig_anomalies, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_anomalies.update_layout(
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
        
        st.plotly_chart(fig_anomalies, use_container_width=True)
        
        # Show anomaly details
        st.markdown(f"<p>Detected {len(anomalies)} anomalies in the selected date range.</p>", unsafe_allow_html=True)
    else:
        st.info("No anomalies detected in the selected date range with the current settings.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Sales Correlation Analysis
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Correlation Analysis</h3>", unsafe_allow_html=True)
    
    # Filter for numeric columns only
    numeric_df = filtered_sales_df.select_dtypes(include=['number'])
    
    if numeric_df.shape[1] >= 3:  # Need at least 3 columns for meaningful correlations
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr().round(2)
        
        # Create heatmap
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale=px.colors.sequential.Blues,
            labels=dict(color="Correlation"),
            zmin=-1, zmax=1
        )
        
        # Apply theme
        fig_corr = apply_theme_to_figure(fig_corr, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_corr.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Key correlations insight
        st.markdown("<h4>Key Correlations</h4>", unsafe_allow_html=True)
        corr_insights = []
        
        # Find high positive and negative correlations
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:  # Only strong correlations
                    corr_insights.append({
                        'Variable 1': corr_matrix.columns[i],
                        'Variable 2': corr_matrix.columns[j],
                        'Correlation': corr_value,
                        'Relationship': 'Strong Positive' if corr_value > 0.7 else 
                                      'Moderate Positive' if corr_value > 0 else
                                      'Strong Negative' if corr_value < -0.7 else
                                      'Moderate Negative'
                    })
        
        if corr_insights:
            corr_df = pd.DataFrame(corr_insights)
            st.dataframe(corr_df, use_container_width=True)
        else:
            st.info("No significant correlations found in the data.")
    else:
        st.info("Not enough numeric variables for correlation analysis.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Scatter Plot Analysis
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("<h3>Relationship Analysis</h3>", unsafe_allow_html=True)
    
    if numeric_df.shape[1] >= 2:
        # Let user select variables
        col1, col2 = st.columns(2)
        with col1:
            x_var = st.selectbox("X Variable", options=numeric_df.columns, index=0)
        with col2:
            y_var = st.selectbox("Y Variable", options=numeric_df.columns, index=min(1, len(numeric_df.columns)-1))
        
        color_var = st.selectbox("Color By", options=['None'] + list(filtered_sales_df.select_dtypes(include=['object']).columns))
        
        # Create scatter plot
        if color_var != 'None':
            fig_scatter = px.scatter(
                filtered_sales_df,
                x=x_var,
                y=y_var,
                color=color_var,
                size=numeric_df.columns[0] if len(numeric_df.columns) > 0 else None,
                hover_data=filtered_sales_df.columns[:5],
                color_discrete_sequence=CHART_COLORS
            )
        else:
            fig_scatter = px.scatter(
                filtered_sales_df,
                x=x_var,
                y=y_var,
                size=numeric_df.columns[0] if len(numeric_df.columns) > 0 else None,
                hover_data=filtered_sales_df.columns[:5],
                color_discrete_sequence=[COLORS['accent']]
            )
        
        # Add trendline
        fig_scatter.update_layout(
            height=400,
            xaxis=dict(title=dict(text=x_var)),
            yaxis=dict(title=dict(text=y_var))
        )
        
        # Apply theme
        fig_scatter = apply_theme_to_figure(fig_scatter, is_dark=(selected_theme == 'Dark Theme'))
        
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Not enough numeric variables for scatter plot analysis.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
    <p>Business Analytics Dashboard | Created with Streamlit and Plotly</p>
    <p>© 2025 Business Analytics Inc. | Last updated: May 01, 2025</p>
</div>
""", unsafe_allow_html=True)