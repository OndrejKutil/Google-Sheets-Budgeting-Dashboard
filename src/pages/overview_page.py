from dash import html, dcc, clientside_callback, Input, Output
import dash_bootstrap_components as dbc
from pages.monthly_page import layout as monthly_layout
from pages.yearly_page import layout as yearly_layout
from pages.savings_page import layout as savings_layout

layout = dbc.Container([
    html.H1("Financial Overview", className="my-4"),
    dbc.Tabs([
        dbc.Tab(yearly_layout, label="Yearly Overview", tab_id="yearly-tab"),
        dbc.Tab(monthly_layout, label="Monthly Overview", tab_id="monthly-tab"),
        dbc.Tab(savings_layout, label="Savings & Investments", tab_id="savings-tab"),
    ], id="overview-tabs", active_tab="yearly-tab")
], fluid=True)

# Add clientside callback to trigger content updates when tabs change
clientside_callback(
    """
    function(tab_value) {
        return tab_value
    }
    """,
    Output("overview-tabs", "active_tab"),
    Input("overview-tabs", "active_tab"),
)
