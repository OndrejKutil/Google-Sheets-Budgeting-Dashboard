from .theme import COLORS, THEME

# Card styles
CARD_STYLE = {
    'backgroundColor': COLORS['surface'],
    'borderRadius': THEME['border_radius'],
    'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
    'border': f'1px solid {COLORS["border"]}',
    'transition': f'transform {THEME["transition_speed"]} ease-in-out',
    'height': '100%',
    'padding': THEME['spacing_unit']
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
    'borderRadius': THEME['border_radius'],
    'option': {
        'backgroundColor': COLORS['surface'],
        'color': COLORS['text']
    }
}

# Button styles
BUTTON_STYLE = {
    'borderRadius': THEME['border_radius'],
    'fontFamily': THEME['font_family'],
    'fontWeight': '500',
    'padding': '0.5rem 1rem',
    'transition': f'all {THEME["transition_speed"]} ease-in-out'
}

# Container styles
CONTAINER_STYLE = {
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'padding': THEME['spacing_unit']
}

# Table styles
TABLE_STYLE = {
    'backgroundColor': COLORS['surface'],
    'color': COLORS['text'],
    'borderRadius': THEME['border_radius'],
    'border': f'1px solid {COLORS["border"]}',
    'width': '100%'
}

# DataTable styles
DATATABLE_STYLE = {
    'table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'minWidth': '100%',
    },
    'cell': {
        'textAlign': 'left',
        'padding': '12px 15px',
        'backgroundColor': COLORS['surface'],
        'color': COLORS['text'],
        'fontSize': '14px',
        'fontFamily': THEME['font_family'],
        'minWidth': '100px',
        'whiteSpace': 'normal',
        'height': 'auto',
    },
    'header': {
        'backgroundColor': COLORS['background'],
        'fontWeight': '600',
        'textTransform': 'uppercase',
        'fontSize': '12px',
        'letterSpacing': '0.5px',
        'borderBottom': f'2px solid {COLORS["border"]}',
    },
    'filter': {
        'backgroundColor': COLORS['surface'],
        'padding': '8px',
    }
}

# Stat card styles
def create_stat_card_style(color='primary'):
    return {
        **CARD_STYLE,
        'title': {
            'color': COLORS['text_muted'],
            'fontSize': '0.9rem',
            'fontWeight': '500',
            'marginBottom': '0.5rem'
        },
        'value': {
            'color': COLORS[color],
            'fontSize': '1.8rem',
            'fontWeight': '600',
            'marginBottom': '0'
        }
    }
