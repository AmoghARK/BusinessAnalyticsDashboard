# Business Analytics Dashboard

![Dashboard Preview](assets/img/favicon.png)

## Overview

A professional business analytics dashboard that provides comprehensive sales insights through interactive and dynamic visualizations. The application transforms complex business data into easily digestible visual formats using advanced data presentation techniques.

### Key Features

- **Multi-page Interface**: Overview, Sales Analytics, Customer Insights, and Forecasting
- **Interactive Filters**: Date range, regions, products, and customer segments
- **Cross-filtering**: Click on chart elements to filter relevant data
- **Dark/Light Mode**: Toggle between visual themes for optimal viewing
- **Responsive Design**: Adapts to various screen sizes
- **State Management**: Save and load custom views and filter configurations
- **Advanced Visualizations**: Bar charts, donut charts, treemaps, funnel charts, line charts, sankey diagrams, and more
- **Predictive Analytics**: Sales forecasting with multiple algorithms

## Tech Stack

- **Streamlit**: Python-based web application framework
- **Plotly**: Interactive visualization library
- **Pandas**: Data manipulation and analysis
- **Prophet**: Time series forecasting 
- **Scikit-learn**: Machine learning for predictive analytics
- **NumPy**: Numerical computing
- **StatsModels**: Statistical models for time series analysis

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AmoghARK/BusinessAnalyticsDashboard.git
   cd business-analytics-dashboard
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   
   Install the required packages from the pyproject.toml file:
   ```bash
   pip install .
   ```
   
   Or install packages individually:
   ```bash
   pip install streamlit pandas numpy plotly prophet scikit-learn statsmodels
   ```

4. **Create the configuration folder**
   ```bash
   mkdir -p .streamlit
   ```

5. **Set up configuration**
   Create a file `.streamlit/config.toml` with the following content:
   ```toml
   [server]
   headless = true
   address = "0.0.0.0"
   port = 5000
   enableStaticServing = true

   [theme]
   primaryColor = "#4E7CFF"
   backgroundColor = "#1A2038"
   secondaryBackgroundColor = "#2A3148"
   textColor = "#FFFFFF"
   font = "sans serif"
   ```

## Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:5000` in your web browser.

## Project Structure

```
├── app.py                  # Main application file (Dashboard Overview)
├── pages/                  # Additional dashboard pages
│   ├── 2_Sales_Analytics.py      # Sales analytics page
│   ├── 3_Customer_Insights.py    # Customer insights page
│   └── 4_Forecasting.py          # Sales forecasting page
├── utils/                  # Utility functions
│   ├── dashboard_utils.py        # Dashboard helper functions
│   └── state_management.py       # State management utilities
├── assets/                 # Static assets
│   └── style.css                 # Custom CSS styling
├── attached_assets/        # Data files
│   ├── sales_data.csv            # Sales dataset
│   └── customer_data.csv         # Customer dataset
├── .streamlit/             # Streamlit configuration
│   └── config.toml               # Configuration settings
├── pyproject.toml          # Python project dependencies
├── README.md               # Project documentation
└── generated-icon.png      # Dashboard icon
```

## Data Description

The dashboard uses two primary datasets:

1. **Sales Data** (`attached_assets/sales_data.csv`):
   - Date, Region, Product, Sales, Units, Discount, etc.

2. **Customer Data** (`attached_assets/customer_data.csv`):
   - Segment, Channel, Satisfaction, Customer Count, etc.

## Customization

### Theme

You can customize the theme by modifying the `.streamlit/config.toml` file:

```toml
[theme]
primaryColor = "#4E7CFF"         # Change to your preferred primary color
backgroundColor = "#1A2038"      # Change to your preferred background color
secondaryBackgroundColor = "#2A3148"  # Change to your preferred secondary color
textColor = "#FFFFFF"            # Change to your preferred text color
font = "sans serif"              # Change to your preferred font
```

### Adding New Visualizations

To add new visualizations, you can extend the existing pages or create new ones in the `pages/` directory.

## Troubleshooting

- **Missing dependencies**: Run `pip install .` to ensure all required packages are installed from the pyproject.toml file.
- **Port conflicts**: If port 5000 is in use, change the port in `.streamlit/config.toml` and when running Streamlit with `--server.port <port_number>`.
- **Data loading issues**: Ensure the data files are in the correct location in the `attached_assets/` directory.
- **Static files not loading**: Make sure the `enableStaticServing` setting is enabled in `.streamlit/config.toml`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Data visualization best practices from Plotly and Streamlit documentation
- Dashboard design inspiration from modern analytics platforms