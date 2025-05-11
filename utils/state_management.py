import streamlit as st
from datetime import datetime, date

def init_state():
    """
    Initialize session state variables if they don't exist
    """
    if 'dashboard_state' not in st.session_state:
        st.session_state.dashboard_state = {
            'start_date': None,
            'end_date': None,
            'selected_regions': [],
            'selected_products': [],
            'selected_segments': [],
            'theme': 'Dark Theme',
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_tab': 'Overview',
            'show_filters': True,
            'cross_filtering_enabled': True,
            'selected_chart_point': None,
            'export_format': 'CSV',
            'annotations': [],
            'saved_views': []
        }

def get_state():
    """
    Get the current dashboard state
    """
    init_state()
    return st.session_state.dashboard_state

def update_state(updates):
    """
    Update the dashboard state with provided values
    
    Args:
        updates (dict): Dictionary of values to update in the state
    """
    init_state()
    
    # Handle date objects
    for key, value in updates.items():
        if isinstance(value, date) and not isinstance(value, datetime):
            updates[key] = value
    
    # Update state
    st.session_state.dashboard_state.update(updates)
    
    # Update last_updated timestamp
    st.session_state.dashboard_state['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return st.session_state.dashboard_state

def save_view(name, description=""):
    """
    Save the current view (filters, selections) as a named preset
    
    Args:
        name (str): Name of the saved view
        description (str, optional): Description of the view
    """
    init_state()
    
    # Get current state
    current_state = st.session_state.dashboard_state
    
    # Create a view object with current filters and settings
    view = {
        'name': name,
        'description': description,
        'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'filters': {
            'start_date': current_state.get('start_date'),
            'end_date': current_state.get('end_date'),
            'selected_regions': current_state.get('selected_regions', []),
            'selected_products': current_state.get('selected_products', []),
            'selected_segments': current_state.get('selected_segments', [])
        },
        'active_tab': current_state.get('active_tab')
    }
    
    # Add to saved views
    saved_views = current_state.get('saved_views', [])
    
    # Check if a view with this name already exists
    existing_index = next((i for i, v in enumerate(saved_views) if v.get('name') == name), None)
    
    if existing_index is not None:
        # Update existing view
        saved_views[existing_index] = view
    else:
        # Add new view
        saved_views.append(view)
    
    # Update state
    update_state({'saved_views': saved_views})
    
    return view

def load_view(name):
    """
    Load a saved view by name
    
    Args:
        name (str): Name of the saved view to load
    
    Returns:
        dict: The loaded view state or None if not found
    """
    init_state()
    
    # Find the named view
    saved_views = st.session_state.dashboard_state.get('saved_views', [])
    view = next((v for v in saved_views if v.get('name') == name), None)
    
    if view is not None:
        # Apply the view's filters to the current state
        filters = view.get('filters', {})
        update_state({
            'start_date': filters.get('start_date'),
            'end_date': filters.get('end_date'),
            'selected_regions': filters.get('selected_regions', []),
            'selected_products': filters.get('selected_products', []),
            'selected_segments': filters.get('selected_segments', []),
            'active_tab': view.get('active_tab')
        })
        
        return view
    
    return None

def delete_view(name):
    """
    Delete a saved view by name
    
    Args:
        name (str): Name of the saved view to delete
    
    Returns:
        bool: True if deleted, False if not found
    """
    init_state()
    
    # Get current saved views
    saved_views = st.session_state.dashboard_state.get('saved_views', [])
    
    # Find the index of the view with the given name
    index = next((i for i, v in enumerate(saved_views) if v.get('name') == name), None)
    
    if index is not None:
        # Remove the view
        saved_views.pop(index)
        
        # Update state
        update_state({'saved_views': saved_views})
        return True
    
    return False