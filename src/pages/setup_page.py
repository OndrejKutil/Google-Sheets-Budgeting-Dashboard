import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, State, dcc
from dash.exceptions import PreventUpdate
from data_fetch import save_settings, get_cache_enabled
from get_categories import get_all_categories_api

layout = dbc.Container([
    dcc.Location(id='setup-url', refresh=True),  # Keep only this URL component for setup page reload functionality
    html.H1("Setup", className="my-4"),
    dbc.Card([
        dbc.CardBody([
            html.H4("Cache Settings"),
            dbc.Switch(
                id='cache-toggle',
                label="Enable Data Caching",
                value=get_cache_enabled(),  # Use get_cache_enabled() instead of ENABLE_CACHE
                className="mb-3",
                persistence=True,  # Add persistence
                persistence_type='session'  # Store in session
            ),
            html.Div(id="cache-status", className="text-success mb-3"),
            html.Div([
                html.P(
                    "Cache status: Data will be cached for 5 minutes when enabled.",
                    className="text-muted mt-3"
                ),
                html.P(
                    "Note: Changes to cache settings will take effect after page reload.",
                    className="text-muted small"
                )
            ]),
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
])

@callback(
    [Output("cache-toggle", "checked"),
     Output("cache-status", "children"),
     Output("setup-url", "refresh")],  # Change to setup-url
    Input("cache-toggle", "value"),
    prevent_initial_call=True
)
def update_cache_setting(value):
    if value is None:
        raise PreventUpdate
        
    # Save the setting to file
    save_settings(value)
    status_message = html.Div([
        html.I(className="fas fa-check-circle me-2"),
        f"Cache {'enabled' if value else 'disabled'} - Settings saved."
    ])

    # Reload the page using JavaScript instead
    return value, status_message, True

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
