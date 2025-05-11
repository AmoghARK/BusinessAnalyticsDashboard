import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import time
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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
        show_filters
    )
    
    from utils.state_management import get_state, update_state
except ImportError:
    st.error("Failed to import utilities. Please make sure all required files exist.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Business Analytics - Forecasting",
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
st.markdown('<a href="/Customer_Insights" class="tab">Customer Insights</a>', unsafe_allow_html=True)
st.markdown('<a href="/Forecasting" class="tab active">Forecasting</a>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Display loading animation
with st.spinner("Loading forecasting data..."):
    # Add small delay for visual effect
    time.sleep(0.5)
    
    # Load data
    sales_df, customer_df = load_data()
    
    # Get min and max dates
    min_date = sales_df['Date'].min().date()
    max_date = sales_df['Date'].max().date()

# Get state
state = get_state()
update_state({'active_tab': 'Forecasting'})

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

# Forecasting options in sidebar
st.sidebar.markdown("<h2 style='color: #4E7CFF;'>Forecasting Options</h2>", unsafe_allow_html=True)

forecast_periods = st.sidebar.slider("Forecast Periods (Days)", min_value=7, max_value=90, value=30, step=7)
forecast_method = st.sidebar.selectbox(
    "Forecasting Method",
    options=["Linear Regression", "Exponential Smoothing", "Seasonal Decomposition"],
    index=0
)

# Dashboard Header - Main content
st.markdown("<h1 class='dashboard-header'>Sales Forecasting</h1>", unsafe_allow_html=True)

# Filter the data
filtered_sales_df, filtered_customer_df = filter_data(
    sales_df, customer_df, 
    start_date, end_date, 
    selected_regions, selected_products, selected_segments
)

# Aggregate the data by date for forecasting
daily_sales = filtered_sales_df.groupby(filtered_sales_df['Date'].dt.date)['Sales'].sum().reset_index()
daily_sales = daily_sales.sort_values('Date')

# Forecasting function using Linear Regression
def forecast_linear_regression(data, periods=30):
    if len(data) < 10:
        st.warning("Not enough data points for reliable forecasting. Please select a larger date range.")
        return None, None
    
    # Create features (X) as date index
    X = np.array(range(len(data))).reshape(-1, 1)
    y = data['Sales'].values
    
    # Fit linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make predictions for historical data
    y_pred = model.predict(X)
    
    # Generate future dates
    last_date = data['Date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
    
    # Generate forecasted values
    X_future = np.array(range(len(data), len(data) + periods)).reshape(-1, 1)
    y_future = model.predict(X_future)
    
    # Create forecast dataframe
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'Forecast': y_future
    })
    
    return forecast_df, y_pred

# Forecasting function using Exponential Smoothing
def forecast_exponential_smoothing(data, periods=30):
    if len(data) < 10:
        st.warning("Not enough data points for reliable forecasting. Please select a larger date range.")
        return None, None
    
    # Fit Exponential Smoothing model
    try:
        model = ExponentialSmoothing(
            data['Sales'],
            trend='add',
            seasonal=None
        ).fit()
        
        # Generate predictions for historical data
        y_pred = model.fittedvalues
        
        # Generate forecasts
        forecast_values = model.forecast(periods)
        
        # Generate future dates
        last_date = data['Date'].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
        
        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecast': forecast_values
        })
        
        return forecast_df, y_pred
    except:
        st.error("Error fitting exponential smoothing model. Try another forecasting method.")
        return None, None

# Forecasting function using Seasonal Decomposition
def forecast_seasonal_decomposition(data, periods=30):
    if len(data) < 30:
        st.warning("Not enough data points for reliable seasonal decomposition. Please select a larger date range.")
        return None, None
    
    try:
        # Set the date as index
        ts_data = data.set_index('Date')['Sales']
        
        # Perform seasonal decomposition
        result = seasonal_decompose(ts_data, model='additive', period=7)  # 7 for weekly seasonality
        
        # Get components
        trend = result.trend
        seasonal = result.seasonal
        residual = result.resid
        
        # Fit linear regression on trend for forecasting
        trend_data = trend.dropna()
        X = np.array(range(len(trend_data))).reshape(-1, 1)
        y = trend_data.values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate future dates
        last_date = data['Date'].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(periods)]
        
        # Forecast trend component
        X_future = np.array(range(len(trend_data), len(trend_data) + periods)).reshape(-1, 1)
        trend_forecast = model.predict(X_future)
        
        # Forecast seasonal component (reuse the last seasonal cycle)
        seasonal_values = seasonal.dropna()
        last_cycle = seasonal_values.values[-7:]
        # Repeat the seasonal cycle as needed
        repeated_cycles = np.tile(last_cycle, (periods // 7) + 1)
        seasonal_forecast = repeated_cycles[:periods]
        
        # Combine trend and seasonal components
        forecast_values = trend_forecast + seasonal_forecast
        
        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecast': forecast_values
        })
        
        # Historical fitted values for comparison
        y_pred = trend.dropna().values + seasonal.dropna().values
        
        return forecast_df, y_pred
    except:
        st.error("Error performing seasonal decomposition. Try another forecasting method.")
        return None, None

# Main forecasting section
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown("<h3>Sales Forecast</h3>", unsafe_allow_html=True)

# Generate forecast based on selected method
if forecast_method == "Linear Regression":
    forecast_df, historical_pred = forecast_linear_regression(daily_sales, periods=forecast_periods)
elif forecast_method == "Exponential Smoothing":
    forecast_df, historical_pred = forecast_exponential_smoothing(daily_sales, periods=forecast_periods)
else:  # Seasonal Decomposition
    forecast_df, historical_pred = forecast_seasonal_decomposition(daily_sales, periods=forecast_periods)

# Create forecast visualization
if forecast_df is not None:
    # Create figure
    fig_forecast = go.Figure()
    
    # Add historical data
    fig_forecast.add_trace(go.Scatter(
        x=daily_sales['Date'],
        y=daily_sales['Sales'],
        mode='lines',
        name='Historical Sales',
        line=dict(color=COLORS['accent'], width=2),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Sales: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add historical model fit if available
    if historical_pred is not None:
        # Trim to match length if needed (for seasonal decomposition)
        if len(historical_pred) < len(daily_sales):
            dates_for_pred = daily_sales['Date'].iloc[len(daily_sales) - len(historical_pred):]
        else:
            dates_for_pred = daily_sales['Date']
        
        fig_forecast.add_trace(go.Scatter(
            x=dates_for_pred,
            y=historical_pred,
            mode='lines',
            name='Model Fit',
            line=dict(color='rgba(100, 200, 255, 0.5)', width=1.5, dash='dash'),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Fitted Value: $%{y:,.2f}<extra></extra>'
        ))
    
    # Add forecast
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df['Date'],
        y=forecast_df['Forecast'],
        mode='lines',
        name='Forecast',
        line=dict(color=COLORS['positive'], width=2.5),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Forecast: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add shaded area for forecast uncertainty
    # Upper bound (simple 10% higher)
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df['Date'],
        y=forecast_df['Forecast'] * 1.1,
        mode='lines',
        name='Upper Bound',
        line=dict(width=0),
        fillcolor='rgba(100, 200, 255, 0.2)',
        fill='tonexty',
        hoverinfo='skip'
    ))
    
    # Lower bound (simple 10% lower)
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df['Date'],
        y=forecast_df['Forecast'] * 0.9,
        mode='lines',
        name='Lower Bound',
        line=dict(width=0),
        fillcolor='rgba(100, 200, 255, 0.2)',
        fill='tonexty',
        hoverinfo='skip'
    ))
    
    # Add vertical line to separate historical from forecast
    last_historical_date = daily_sales['Date'].max()
    
    # Use add_shape instead of add_vline for better compatibility
    fig_forecast.add_shape(
        type="line",
        x0=last_historical_date,
        y0=0,
        x1=last_historical_date,
        y1=daily_sales['Sales'].max() * 1.2,
        line=dict(color="red", width=1, dash="dash")
    )
    
    # Add annotation for forecast start
    fig_forecast.add_annotation(
        x=last_historical_date,
        y=daily_sales['Sales'].max() * 1.1,
        text="Forecast Start",
        showarrow=True,
        arrowhead=1,
        ax=40,
        ay=-30
    )
    
    # Apply theme
    fig_forecast = apply_theme_to_figure(fig_forecast, is_dark=(selected_theme == 'Dark Theme'))
    
    # Update layout
    fig_forecast.update_layout(
        height=500,
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
    
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # Calculate forecasting metrics
    total_historical = daily_sales['Sales'].sum()
    total_forecast = forecast_df['Forecast'].sum()
    avg_historical = daily_sales['Sales'].mean()
    avg_forecast = forecast_df['Forecast'].mean()
    growth_rate = ((avg_forecast - avg_historical) / avg_historical * 100) if avg_historical > 0 else 0
    
    # Display forecast metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Average Historical Sales",
            value=f"${avg_historical:,.2f}",
            delta=None
        )
    with col2:
        st.metric(
            label="Average Forecasted Sales",
            value=f"${avg_forecast:,.2f}",
            delta=f"{growth_rate:.1f}%" if growth_rate != 0 else None
        )
    with col3:
        st.metric(
            label="Total Forecasted Sales",
            value=f"${total_forecast:,.2f}",
            delta=None
        )
    
    # Display future sales data
    st.markdown("<h4>Forecasted Sales Data</h4>", unsafe_allow_html=True)
    
    # Format the forecast data for display
    display_forecast = forecast_df.copy()
    display_forecast['Date'] = display_forecast['Date'].astype(str)
    display_forecast['Forecast'] = display_forecast['Forecast'].apply(lambda x: f"${x:,.2f}")
    display_forecast = display_forecast.rename(columns={'Date': 'Date', 'Forecast': 'Forecasted Sales'})
    
    st.dataframe(display_forecast, use_container_width=True)
    
    # Add download button for forecast data
    csv = forecast_df.to_csv(index=False)
    st.download_button(
        label="Download Forecast Data",
        data=csv,
        file_name="sales_forecast.csv",
        mime="text/csv"
    )

st.markdown("</div>", unsafe_allow_html=True)

# Product-specific forecast
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown("<h3>Product Forecast Analysis</h3>", unsafe_allow_html=True)

# Let user select a product for specific forecast
product_options = filtered_sales_df['Product'].unique().tolist()
if product_options:
    selected_product_forecast = st.selectbox("Select Product for Forecast", options=product_options)
    
    # Filter data for selected product
    product_sales = filtered_sales_df[filtered_sales_df['Product'] == selected_product_forecast]
    daily_product_sales = product_sales.groupby(product_sales['Date'].dt.date)['Sales'].sum().reset_index()
    daily_product_sales = daily_product_sales.sort_values('Date')
    
    # Generate forecast for specific product
    if forecast_method == "Linear Regression":
        product_forecast_df, product_historical_pred = forecast_linear_regression(daily_product_sales, periods=forecast_periods)
    elif forecast_method == "Exponential Smoothing":
        product_forecast_df, product_historical_pred = forecast_exponential_smoothing(daily_product_sales, periods=forecast_periods)
    else:  # Seasonal Decomposition
        product_forecast_df, product_historical_pred = forecast_seasonal_decomposition(daily_product_sales, periods=forecast_periods)
    
    if product_forecast_df is not None:
        # Create figure
        fig_product_forecast = go.Figure()
        
        # Add historical data
        fig_product_forecast.add_trace(go.Scatter(
            x=daily_product_sales['Date'],
            y=daily_product_sales['Sales'],
            mode='lines',
            name='Historical Sales',
            line=dict(color=COLORS['accent'], width=2),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Sales: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add forecast
        fig_product_forecast.add_trace(go.Scatter(
            x=product_forecast_df['Date'],
            y=product_forecast_df['Forecast'],
            mode='lines',
            name='Forecast',
            line=dict(color=COLORS['highlight'], width=2.5),
            hovertemplate='<b>%{x|%b %d, %Y}</b><br>Forecast: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add shaded area for forecast uncertainty
        fig_product_forecast.add_trace(go.Scatter(
            x=product_forecast_df['Date'],
            y=product_forecast_df['Forecast'] * 1.1,
            mode='lines',
            name='Upper Bound',
            line=dict(width=0),
            fillcolor='rgba(100, 200, 255, 0.2)',
            fill='tonexty',
            hoverinfo='skip'
        ))
        
        fig_product_forecast.add_trace(go.Scatter(
            x=product_forecast_df['Date'],
            y=product_forecast_df['Forecast'] * 0.9,
            mode='lines',
            name='Lower Bound',
            line=dict(width=0),
            fillcolor='rgba(100, 200, 255, 0.2)',
            fill='tonexty',
            hoverinfo='skip'
        ))
        
        # Add vertical line to separate historical from forecast
        last_historical_date = daily_product_sales['Date'].max()
        
        # Use add_shape instead of add_vline for better compatibility
        fig_product_forecast.add_shape(
            type="line",
            x0=last_historical_date,
            y0=0,
            x1=last_historical_date,
            y1=daily_product_sales['Sales'].max() * 1.2,
            line=dict(color="red", width=1, dash="dash")
        )
        
        # Apply theme
        fig_product_forecast = apply_theme_to_figure(fig_product_forecast, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_product_forecast.update_layout(
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title=dict(text='Date')),
            yaxis=dict(title=dict(text=f'{selected_product_forecast} Sales ($)')),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_product_forecast, use_container_width=True)
        
        # Calculate product forecast metrics
        avg_product_historical = daily_product_sales['Sales'].mean()
        avg_product_forecast = product_forecast_df['Forecast'].mean()
        product_growth_rate = ((avg_product_forecast - avg_product_historical) / avg_product_historical * 100) if avg_product_historical > 0 else 0
        
        # Display product forecast metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label=f"Average Historical {selected_product_forecast} Sales",
                value=f"${avg_product_historical:,.2f}",
                delta=None
            )
        with col2:
            st.metric(
                label=f"Average Forecasted {selected_product_forecast} Sales",
                value=f"${avg_product_forecast:,.2f}",
                delta=f"{product_growth_rate:.1f}%" if product_growth_rate != 0 else None
            )
else:
    st.info("No product data available for forecasting.")

st.markdown("</div>", unsafe_allow_html=True)

# Comparative forecast by region or product
st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown("<h3>Comparative Forecast Analysis</h3>", unsafe_allow_html=True)

# Let user select dimension for comparison
comparison_dimension = st.radio("Compare Forecast By:", ["Region", "Product"])

if comparison_dimension == "Region":
    dimension_column = 'Region'
    dimension_options = filtered_sales_df['Region'].unique().tolist()
else:
    dimension_column = 'Product'
    dimension_options = filtered_sales_df['Product'].unique().tolist()

# Limit to top 5 for clarity
dimension_options = dimension_options[:5] if len(dimension_options) > 5 else dimension_options

if dimension_options:
    # Create figure for comparison
    fig_comparison = go.Figure()
    
    for i, dimension in enumerate(dimension_options):
        # Filter data for the dimension
        dimension_data = filtered_sales_df[filtered_sales_df[dimension_column] == dimension]
        daily_dimension_sales = dimension_data.groupby(dimension_data['Date'].dt.date)['Sales'].sum().reset_index()
        daily_dimension_sales = daily_dimension_sales.sort_values('Date')
        
        if len(daily_dimension_sales) > 10:  # Minimum data points for forecasting
            # Generate forecast
            if forecast_method == "Linear Regression":
                dimension_forecast_df, _ = forecast_linear_regression(daily_dimension_sales, periods=forecast_periods)
            elif forecast_method == "Exponential Smoothing":
                dimension_forecast_df, _ = forecast_exponential_smoothing(daily_dimension_sales, periods=forecast_periods)
            else:  # Seasonal Decomposition
                dimension_forecast_df, _ = forecast_seasonal_decomposition(daily_dimension_sales, periods=forecast_periods)
            
            if dimension_forecast_df is not None:
                # Add forecast line
                fig_comparison.add_trace(go.Scatter(
                    x=dimension_forecast_df['Date'],
                    y=dimension_forecast_df['Forecast'],
                    mode='lines',
                    name=dimension,
                    line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=2),
                    hovertemplate=f'<b>%{{x|%b %d, %Y}}</b><br>{dimension}: $%{{y:,.2f}}<extra></extra>'
                ))
    
    if hasattr(fig_comparison, 'data') and fig_comparison.data:
        # Apply theme
        fig_comparison = apply_theme_to_figure(fig_comparison, is_dark=(selected_theme == 'Dark Theme'))
        
        # Update layout
        fig_comparison.update_layout(
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title=dict(text='Date')),
            yaxis=dict(title=dict(text='Forecasted Sales ($)')),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Add explanation
        st.markdown(f"""
        <p>This chart shows the sales forecast for the next {forecast_periods} days for each {comparison_dimension.lower()}. 
        The forecasts are based on historical sales patterns and the selected forecasting method.</p>
        """, unsafe_allow_html=True)
    else:
        st.warning("Could not generate comparative forecasts. Try a different forecasting method or dimension.")
else:
    st.info(f"No {comparison_dimension.lower()} data available for comparison.")

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class='footer'>
    <p>Business Analytics Dashboard | Created with Streamlit and Plotly</p>
    <p>© 2025 Business Analytics Inc. | Last updated: May 01, 2025</p>
</div>
""", unsafe_allow_html=True)