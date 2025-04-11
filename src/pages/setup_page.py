import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State, dcc
from dash.exceptions import PreventUpdate
from data_fetch import save_settings, load_settings, get_cache_stats, clear_cache, prefetch_common_data
from get_categories import get_all_categories_api

# Define help text for settings
HELP_TEXTS = {
    'cache_enabled': "Enable storing data fetched from Google Sheets in memory to reduce API calls and speed up page loads.",
    'prefetch_enabled': "Preload commonly accessed data when the application starts to improve initial response times.",
    'cache_duration': "How long (in seconds) cached data remains valid before being refreshed from the source.",
    'clear_cache': "Immediately remove all cached data from memory, forcing fresh data to be retrieved on next request.",
    'use_fundamental_expenses': "When enabled, emergency fund targets are based only on essential expenses marked as 'Fundamental'. When disabled, all expenses are used."
}

layout = dbc.Container([
    dcc.Location(id='setup-url', refresh=True),
    html.H1("Setup", className="my-4"),
    dbc.Card([
        dbc.CardBody([
            html.H4("Cache Settings"),
            
            # Cache toggle with explanation
            dbc.Row([
                dbc.Col([
                    dbc.Form([
                        dbc.Label("Enable Data Caching"),
                        dbc.Switch(
                            id='cache-toggle',
                            value=load_settings().get('cache_enabled', True),
                            className="mb-2",
                            persistence=True,
                            persistence_type='session'
                        ),
                        dbc.FormText(HELP_TEXTS['cache_enabled'], color="muted"),
                    ]),
                ], width=6),
                
                # Prefetch toggle with explanation
                dbc.Col([
                    dbc.Form([
                        dbc.Label("Enable Data Prefetching"),
                        dbc.Switch(
                            id='prefetch-toggle',
                            value=load_settings().get('prefetch_enabled', False),
                            className="mb-2",
                            persistence=True,
                            persistence_type='session'
                        ),
                        dbc.FormText(HELP_TEXTS['prefetch_enabled'], color="muted"),
                    ]),
                ], width=6)
            ], className="mb-3"),
            
            # Cache duration and clear cache button in the same row with proper alignment
            dbc.Row([
                dbc.Col([
                    dbc.Form([
                        dbc.Label("Cache Duration (seconds):", html_for="cache-duration"),
                        dbc.Input(
                            id='cache-duration',
                            type='number',
                            min=30,
                            max=3600,
                            step=30,
                            value=load_settings().get('cache_duration', 300),
                            className="mb-2"
                        ),
                        dbc.FormText(HELP_TEXTS['cache_duration'], color="muted"),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Form([
                        dbc.Label("Clear Current Cache:"),
                        dbc.Button(
                            "Clear Cache", 
                            id="clear-cache-button", 
                            color="warning", 
                            className="mb-2 d-block"
                        ),
                        dbc.FormText(HELP_TEXTS['clear_cache'], color="muted"),
                    ]),
                ], width=6)
            ], className="mb-3"),
            
            html.Div(id="cache-status", className="text-success mb-3"),
            html.Hr(),
            
            # Cache statistics with heading
            html.H5("Cache Statistics", className="mt-3"),
            html.Div(id="cache-stats", className="text-muted"),
            
            html.Hr(),
            html.H4("Emergency Fund Settings"),
            dbc.Row([
                dbc.Col([
                    dbc.Form([
                        dbc.Label("Use Only Fundamental Expenses for Targets"),
                        dbc.Switch(
                            id='fundamental-expenses-toggle',
                            value=load_settings().get('use_fundamental_expenses', True),
                            className="mb-2",
                            persistence=True,
                            persistence_type='session'
                        ),
                        dbc.FormText(HELP_TEXTS['use_fundamental_expenses'], color="muted"),
                    ]),
                ], width=12),
            ], className="mb-3"),
            
            html.Hr(),
            html.H4("API Connection Test"),
            dbc.Button(
                "Test Connection", 
                id="test-connection", 
                color="primary", 
                className="mb-2"
            ),
            html.Div(
                id="connection-status",
                className="mt-2"
            )
        ])
    ])
], fluid=True, className="px-4")

@callback(
    [Output("cache-toggle", "checked"),
     Output("prefetch-toggle", "checked"),
     Output("cache-duration", "value"),
     Output("cache-status", "children"),
     Output("setup-url", "refresh"),
     Output("fundamental-expenses-toggle", "checked")],  # Added new output
    [Input("cache-toggle", "value"),
     Input("prefetch-toggle", "value"),
     Input("cache-duration", "value"),
     Input("fundamental-expenses-toggle", "value")],  # Added new input
    prevent_initial_call=True
)
def update_settings(cache_enabled, prefetch_enabled, cache_duration, use_fundamental_expenses):
    if cache_enabled is None or prefetch_enabled is None or cache_duration is None or use_fundamental_expenses is None:
        raise PreventUpdate
    
    # Load current settings
    settings = load_settings()
    
    # Update settings
    settings['cache_enabled'] = cache_enabled
    settings['prefetch_enabled'] = prefetch_enabled
    settings['cache_duration'] = cache_duration
    settings['use_fundamental_expenses'] = use_fundamental_expenses  # Add new setting
    
    # Save the updated settings to file
    save_settings(settings)
    
    # Create status message
    status_message = html.Div([
        html.I(className="fas fa-check-circle me-2"),
        f"Settings saved. Cache {'enabled' if cache_enabled else 'disabled'}. " +
        f"Prefetching {'enabled' if prefetch_enabled else 'disabled'}. " +
        f"Emergency fund calculation using {'fundamental' if use_fundamental_expenses else 'all'} expenses."
    ])

    # If prefetching is enabled, trigger prefetch on next load
    if prefetch_enabled:
        prefetch_common_data()

    # Return all values including the new toggle state
    return cache_enabled, prefetch_enabled, cache_duration, status_message, True, use_fundamental_expenses

@callback(
    Output("cache-stats", "children"),
    [Input("setup-url", "pathname")]
)
def update_cache_stats(_):
    """Display cache statistics."""
    stats = get_cache_stats()
    
    return html.Div([
        dbc.Table([
            html.Tbody([
                html.Tr([html.Td("Cache Size:"), html.Td(f"{stats['current_size']} entries")]),
                html.Tr([html.Td("Cache Hits:"), html.Td(f"{stats['hits']}")]),
                html.Tr([html.Td("Cache Misses:"), html.Td(f"{stats['misses']}")]),
                html.Tr([html.Td("Hit Rate:"), html.Td(f"{stats['hit_rate']:.2%}")]),
                html.Tr([html.Td("API Calls Saved:"), html.Td(f"{stats['saved_api_calls']}")]),
                html.Tr([html.Td("Cache Age:"), html.Td(f"{stats['cache_age_seconds']:.1f} seconds")]),
            ])
        ], bordered=False, className="text-muted table-sm")
    ])

@callback(
    Output("connection-status", "children"),
    Input("test-connection", "n_clicks"),
    prevent_initial_call=True
)
def test_connection(n_clicks):
    if n_clicks is None:
        return ""
    
    try:
        SPREADSHEET_NAME = "Budget tracker 2025"
        get_all_categories_api(SPREADSHEET_NAME)
        return html.Div([
            html.I(className="fas fa-check-circle me-2"),
            "Connection successful!"
        ], className="text-success")
    except Exception as e:
        return html.Div([
            html.I(className="fas fa-exclamation-circle me-2"),
            f"Connection failed: {str(e)}"
        ], className="text-danger")

@callback(
    Output("cache-status", "children", allow_duplicate=True),
    Input("clear-cache-button", "n_clicks"),
    prevent_initial_call=True
)
def clear_cache_handler(n_clicks):
    """Handle cache clearing."""
    if n_clicks is None:
        raise PreventUpdate
    
    # Clear the cache
    clear_cache()
    
    return html.Div([
        html.I(className="fas fa-check-circle me-2"),
        "Cache cleared successfully!"
    ], className="text-success")
