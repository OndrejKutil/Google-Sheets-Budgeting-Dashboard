# Color palette
COLORS = {
    # Background colors
    'background': '#1a1a1a',
    'surface': '#2d2d2d',
    'border': '#404040',
    
    # Text colors
    'text': '#ffffff',
    'text_muted': '#adb5bd',
    
    # Semantic colors
    'primary': '#5dade2',  # Changed from #3498DB to a lighter blue
    'success': '#2ECC71',
    'danger': '#E74C3C',
    'info': '#5dade2',    # Changed to match primary
    'purple': '#af7ac5',  # Changed from #9B59B6 to a lighter purple
    
    # Specific use colors
    'income': '#2ECC71',     # Green - same as success
    'expenses': '#E74C3C',   # Red - same as danger
    'savings': '#5dade2',    # Blue - updated to lighter shade
    'investments': '#af7ac5', # Purple - updated to lighter shade
}

# Base theme configuration
THEME = {
    'font_family': 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial',
    'font_size_base': '16px',
    'line_height_base': '1.5',
    'border_radius': '8px',
    'transition_speed': '0.2s',
    'spacing_unit': '1rem',
}

# Text styles configuration
TEXT_STYLES = {
    'h1': {
        'color': COLORS['text'],
        'fontSize': '2.5rem',
        'fontWeight': '600',
        'marginBottom': '1.5rem',
        'fontFamily': THEME['font_family']
    },
    'h2': {
        'color': COLORS['text'],
        'fontSize': '2rem',
        'fontWeight': '600',
        'marginBottom': '1rem',
        'fontFamily': THEME['font_family']
    },
    'h3': {
        'color': COLORS['text'],
        'fontSize': '1.75rem',
        'fontWeight': '600',
        'marginBottom': '1rem',
        'fontFamily': THEME['font_family']
    },
    'h4': {
        'color': COLORS['text'],
        'fontSize': '1.5rem',
        'fontWeight': '500',
        'marginBottom': '0.75rem',
        'fontFamily': THEME['font_family']
    },
    'card_title': {
        'color': COLORS['text'],
        'fontSize': '1.1rem',
        'fontWeight': '500',
        'marginBottom': '1rem',
        'fontFamily': THEME['font_family']
    },
    'body': {
        'color': COLORS['text'],
        'fontSize': '1rem',
        'fontWeight': '400',
        'fontFamily': THEME['font_family']
    },
    'caption': {
        'color': COLORS['text_muted'],
        'fontSize': '0.875rem',
        'fontWeight': '400',
        'fontFamily': THEME['font_family']
    }
}

# Chart theme
CHART_THEME = {
    'bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'font_color': '#ffffff',  # Changed from COLORS['text'] to explicit white
    'grid_color': 'rgba(255,255,255,0.1)',
    'title_font_size': 18,
    'height': 400,
    'axis': {
        'color': '#ffffff',  # Added explicit axis color
        'gridcolor': 'rgba(255,255,255,0.1)',
        'linecolor': 'rgba(255,255,255,0.3)'
    }
}

# Component styles
CARD_STYLE = {
    'backgroundColor': COLORS['surface'],
    'borderRadius': '12px',
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'border': f'1px solid {COLORS["border"]}',
    'transition': 'transform 0.2s ease-in-out',
    'height': '100%'
}

CARD_HOVER_STYLE = {
    'transform': 'translateY(-2px)',
    'boxShadow': '0 6px 12px rgba(0, 0, 0, 0.15)'
}

# Dropdown styles
DROPDOWN_STYLE = {
    'backgroundColor': COLORS['surface'],
    'color': COLORS['text'],
    'border': f'1px solid {COLORS["border"]}',
    'borderRadius': '8px',
    'option': {
        'backgroundColor': COLORS['surface'],
        'color': COLORS['text']
    }
}
