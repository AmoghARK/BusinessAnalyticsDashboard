import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Define color theme - Modern Professional
COLORS = {
    'background': '#1A2038',  # Dark blue-grey
    'card_bg': '#2A3148',     # Slightly lighter blue-grey
    'accent': '#4E7CFF',      # Vibrant blue
    'text': '#FFFFFF',        # White text
    'highlight': '#6DB5FE',   # Light blue for highlights
    'positive': '#4ECDC4',    # Teal for positive trends
    'negative': '#E84855',    # Red for negative trends
    'neutral': '#95A5A6',     # Grey for neutral trends
    'warning': '#F1A208',     # Gold for warnings
    'light_bg': '#F5F7FA',    # Light background for light theme
    'light_card': '#FFFFFF',  # White card for light theme
    'light_text': '#2A3148',  # Dark text for light theme
    'light_accent': '#4E7CFF' # Same accent for light theme
}

# Define chart colors - Professional Color Palette
CHART_COLORS = [
    COLORS['accent'],         # Primary blue
    '#6DB5FE',                # Light blue
    '#62C0C7',                # Teal
    '#4ECDC4',                # Turquoise
    '#81B29A',                # Sage green
    '#95D7AE',                # Mint
    '#F1A208',                # Gold
    '#FF8C42',                # Orange
    '#E84855',                # Red
    '#7F5A83'                 # Purple
]

# Function to load data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data():
    """
    Load the dataset files with caching for performance
    """
    try:
        # Load sales data
        sales_df = pd.read_csv('attached_assets/sales_data.csv')
        
        # Load customer data
        customer_df = pd.read_csv('attached_assets/customer_data.csv')
        
        # Convert date column to datetime
        if not pd.api.types.is_datetime64_any_dtype(sales_df['Date']):
            sales_df['Date'] = pd.to_datetime(sales_df['Date'])
        
        return sales_df, customer_df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

# Function to filter data based on selections
def filter_data(sales_df, customer_df, start_date, end_date, selected_regions, selected_products, selected_segments):
    """
    Filter sales and customer data based on user selections
    """
    filtered_sales_df = sales_df.copy()
    
    # Apply date filter
    if start_date and end_date:
        filtered_sales_df = filtered_sales_df[
            (filtered_sales_df['Date'].dt.date >= start_date) & 
            (filtered_sales_df['Date'].dt.date <= end_date)
        ]
    
    # Apply region filter
    if selected_regions and len(selected_regions) > 0:
        filtered_sales_df = filtered_sales_df[filtered_sales_df['Region'].isin(selected_regions)]
    
    # Apply product filter
    if selected_products and len(selected_products) > 0:
        filtered_sales_df = filtered_sales_df[filtered_sales_df['Product'].isin(selected_products)]
    
    # Filter customer data based on segment selection
    filtered_customer_df = customer_df.copy()
    if selected_segments and len(selected_segments) > 0:
        filtered_customer_df = filtered_customer_df[filtered_customer_df['Segment'].isin(selected_segments)]
    
    return filtered_sales_df, filtered_customer_df

# Function to calculate KPIs with trend indicators
def calculate_kpis(filtered_sales_df, comparison_period=30):
    """
    Calculate KPIs with trend indicators comparing current period to previous period
    """
    # Basic metrics
    total_sales = filtered_sales_df['Sales'].sum()
    total_units = filtered_sales_df['Units'].sum()
    
    # Use Customers column if it exists, otherwise calculate from Customer ID
    if 'Customers' in filtered_sales_df.columns:
        total_customers = filtered_sales_df['Customers'].sum()
    else:
        total_customers = len(filtered_sales_df['Customer ID'].unique()) if 'Customer ID' in filtered_sales_df.columns else 0
    
    # Calculate average sale
    avg_sale = total_sales / total_units if total_units > 0 else 0
    
    # Calculate trend data if enough data exists
    has_trends = False
    trends = {
        'sales_trend': 0,
        'units_trend': 0,
        'customers_trend': 0,
        'avg_sale_trend': 0
    }
    
    if len(filtered_sales_df) > 0:
        try:
            # Get date range
            date_range = (filtered_sales_df['Date'].max() - filtered_sales_df['Date'].min()).days
            
            if date_range >= comparison_period*2:  # Need enough data for comparison
                has_trends = True
                
                # Split data into current and previous periods
                midpoint = filtered_sales_df['Date'].max() - timedelta(days=comparison_period)
                current_period = filtered_sales_df[filtered_sales_df['Date'] >= midpoint]
                previous_period = filtered_sales_df[(filtered_sales_df['Date'] < midpoint) & 
                                                  (filtered_sales_df['Date'] >= midpoint - timedelta(days=comparison_period))]
                
                # Calculate metrics for each period
                current_sales = current_period['Sales'].sum()
                previous_sales = previous_period['Sales'].sum()
                
                current_units = current_period['Units'].sum()
                previous_units = previous_period['Units'].sum()
                
                if 'Customers' in filtered_sales_df.columns:
                    current_customers = current_period['Customers'].sum()
                    previous_customers = previous_period['Customers'].sum()
                else:
                    current_customers = len(current_period['Customer ID'].unique()) if 'Customer ID' in current_period.columns else 0
                    previous_customers = len(previous_period['Customer ID'].unique()) if 'Customer ID' in previous_period.columns else 0
                
                current_avg_sale = current_sales / current_units if current_units > 0 else 0
                previous_avg_sale = previous_sales / previous_units if previous_units > 0 else 0
                
                # Calculate percent changes
                if previous_sales > 0:
                    trends['sales_trend'] = int(((current_sales - previous_sales) / previous_sales) * 100)
                
                if previous_units > 0:
                    trends['units_trend'] = int(((current_units - previous_units) / previous_units) * 100)
                
                if previous_customers > 0:
                    trends['customers_trend'] = int(((current_customers - previous_customers) / previous_customers) * 100)
                
                if previous_avg_sale > 0:
                    trends['avg_sale_trend'] = int(((current_avg_sale - previous_avg_sale) / previous_avg_sale) * 100)
        except:
            # If there's an error in trend calculation, proceed without trends
            pass
    
    return {
        'total_sales': f"${total_sales:,.2f}",
        'total_sales_raw': total_sales,
        'total_units': f"{total_units:,}",
        'total_units_raw': total_units,
        'total_customers': f"{total_customers:,}",
        'total_customers_raw': total_customers,
        'avg_sale': f"${avg_sale:,.2f}",
        'avg_sale_raw': avg_sale,
        'has_trends': has_trends,
        'sales_trend': trends['sales_trend'],
        'units_trend': trends['units_trend'],
        'customers_trend': trends['customers_trend'],
        'avg_sale_trend': trends['avg_sale_trend']
    }

# Function to render KPI cards with trend indicators
def render_kpi_cards(kpis):
    """
    Render KPI cards with trend indicators
    """
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<h4>Total Sales</h4>", unsafe_allow_html=True)
        st.markdown(f"<p class='kpi-value'>{kpis['total_sales']}</p>", unsafe_allow_html=True)
        
        # Add trend indicator if available
        if kpis['has_trends']:
            trend = kpis['sales_trend']
            trend_class = 'trend-up' if trend > 0 else 'trend-down' if trend < 0 else 'trend-neutral'
            trend_arrow = '↑' if trend > 0 else '↓' if trend < 0 else '→'
            st.markdown(f"<p class='kpi-trend {trend_class}'>{trend_arrow} {abs(trend):.1f}% vs previous period</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with kpi2:
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<h4>Units Sold</h4>", unsafe_allow_html=True)
        st.markdown(f"<p class='kpi-value'>{kpis['total_units']}</p>", unsafe_allow_html=True)
        
        # Add trend indicator if available
        if kpis['has_trends']:
            trend = kpis['units_trend']
            trend_class = 'trend-up' if trend > 0 else 'trend-down' if trend < 0 else 'trend-neutral'
            trend_arrow = '↑' if trend > 0 else '↓' if trend < 0 else '→'
            st.markdown(f"<p class='kpi-trend {trend_class}'>{trend_arrow} {abs(trend):.1f}% vs previous period</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with kpi3:
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<h4>Total Customers</h4>", unsafe_allow_html=True)
        st.markdown(f"<p class='kpi-value'>{kpis['total_customers']}</p>", unsafe_allow_html=True)
        
        # Add trend indicator if available
        if kpis['has_trends']:
            trend = kpis['customers_trend']
            trend_class = 'trend-up' if trend > 0 else 'trend-down' if trend < 0 else 'trend-neutral'
            trend_arrow = '↑' if trend > 0 else '↓' if trend < 0 else '→'
            st.markdown(f"<p class='kpi-trend {trend_class}'>{trend_arrow} {abs(trend):.1f}% vs previous period</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with kpi4:
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<h4>Average Sale</h4>", unsafe_allow_html=True)
        st.markdown(f"<p class='kpi-value'>{kpis['avg_sale']}</p>", unsafe_allow_html=True)
        
        # Add trend indicator if available
        if kpis['has_trends']:
            trend = kpis['avg_sale_trend']
            trend_class = 'trend-up' if trend > 0 else 'trend-down' if trend < 0 else 'trend-neutral'
            trend_arrow = '↑' if trend > 0 else '↓' if trend < 0 else '→'
            st.markdown(f"<p class='kpi-trend {trend_class}'>{trend_arrow} {abs(trend):.1f}% vs previous period</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Function to show filters in sidebar
def show_filters(sales_df, customer_df, state=None):
    """
    Display filter widgets in the sidebar and return selections
    """
    min_date = sales_df['Date'].min().date()
    max_date = sales_df['Date'].max().date()
    
    # Date range filters
    st.sidebar.markdown("<h3 style='color: #6DB5FE;'>Date Range</h3>", unsafe_allow_html=True)
    
    # Use state values if available or defaults
    start_date_default = state.get('start_date', min_date) if state else min_date
    end_date_default = state.get('end_date', max_date) if state else max_date
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=start_date_default,
        min_value=min_date,
        max_value=max_date,
        key="start_date"
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=end_date_default,
        min_value=min_date,
        max_value=max_date,
        key="end_date"
    )
    
    # Region filter
    st.sidebar.markdown("<h3 style='color: #6DB5FE;'>Regions</h3>", unsafe_allow_html=True)
    regions = sales_df['Region'].unique().tolist()
    
    # Use state values if available or defaults
    selected_regions_default = state.get('selected_regions', regions) if state else regions
    
    selected_regions = st.sidebar.multiselect(
        "Select Regions",
        options=regions,
        default=selected_regions_default,
        key="region_filter"
    )
    
    # Product filter
    st.sidebar.markdown("<h3 style='color: #6DB5FE;'>Products</h3>", unsafe_allow_html=True)
    products = sales_df['Product'].unique().tolist()
    
    # Use state values if available or defaults
    selected_products_default = state.get('selected_products', products) if state else products
    
    selected_products = st.sidebar.multiselect(
        "Select Products",
        options=products,
        default=selected_products_default,
        key="product_filter"
    )
    
    # Customer segment filter
    st.sidebar.markdown("<h3 style='color: #6DB5FE;'>Customer Segments</h3>", unsafe_allow_html=True)
    segments = customer_df['Segment'].unique().tolist()
    
    # Use state values if available or defaults
    selected_segments_default = state.get('selected_segments', segments) if state else segments
    
    selected_segments = st.sidebar.multiselect(
        "Select Segments",
        options=segments,
        default=selected_segments_default,
        key="segment_filter"
    )
    
    return start_date, end_date, selected_regions, selected_products, selected_segments

# Function to apply theme to figure
def apply_theme_to_figure(fig, is_dark=True):
    """
    Apply the appropriate theme to a plotly figure
    """
    if is_dark:
        bg_color = 'rgba(0,0,0,0)'
        text_color = 'white'
        grid_color = 'rgba(255,255,255,0.1)'
    else:
        bg_color = 'rgba(255,255,255,0)'
        text_color = COLORS['light_text']
        grid_color = 'rgba(0,0,0,0.1)'
    
    fig.update_layout(
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font=dict(family="Arial, 'Helvetica Neue', sans-serif", size=12, color=text_color),
        margin=dict(l=40, r=20, t=30, b=40),
    )
    
    fig.update_xaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    
    fig.update_yaxes(
        gridcolor=grid_color,
        zerolinecolor=grid_color
    )
    
    return fig

# Function to detect anomalies
def detect_anomalies(df, column, window=7, threshold=2):
    """
    Detect anomalies in time series data using z-score method
    
    Args:
        df: DataFrame containing the time series data
        column: Name of the column to analyze
        window: Rolling window size for calculating mean and std
        threshold: Z-score threshold for anomaly detection (integer)
    
    Returns:
        DataFrame containing only the anomalous rows
    """
    rolling_mean = df[column].rolling(window=window).mean()
    rolling_std = df[column].rolling(window=window).std()
    
    # Calculate z-score
    z_scores = (df[column] - rolling_mean) / rolling_std
    
    # Mark anomalies where absolute z-score exceeds threshold
    anomalies = df[abs(z_scores) > threshold].copy()
    
    return anomalies

# Function to find correlated columns
def find_correlations(df, threshold=0.7):
    """
    Find highly correlated numeric columns in a dataframe
    """
    # Filter for numeric columns
    numeric_df = df.select_dtypes(include=['number'])
    
    if numeric_df.empty or numeric_df.shape[1] < 2:
        return []
        
    # Calculate correlation matrix
    corr_matrix = numeric_df.corr()
    
    # Find correlations above threshold (and below 1.0 which is self-correlation)
    high_corrs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > threshold:
                high_corrs.append({
                    'col1': corr_matrix.columns[i],
                    'col2': corr_matrix.columns[j],
                    'corr': corr_matrix.iloc[i, j]
                })
    
    return high_corrs