# Site Setup Documentation

This document covers the setup and configuration of the Budget Dashboard application.

## Table of Contents
1. [Application Structure](#application-structure)
2. [Initialization](#initialization)
3. [Dashboard Configuration](#dashboard-configuration)
4. [Routing](#routing)
5. [Navigation](#navigation)
6. [Logging](#logging)

## Application Structure

The Budget Dashboard follows a modular architecture:

```
src/
├── main.py               # Entry point
├── dashboard.py          # Dashboard configuration
├── routes.py             # URL routing
├── data_fetch.py         # Data retrieval and caching
├── analysis.py           # Data analysis functions
├── get_categories.py     # Category management
├── layouts/              # Layout components
│   ├── __init__.py
│   └── navbar.py         # Navigation bar
├── pages/                # Page definitions
│   ├── overview_page.py
│   ├── accounts_page.py
│   └── ...
└── styles/               # Styling components
```

## Initialization

The application initializes in `main.py`:

### Startup Process

1. Clear the log file for new session logging
2. Configure logging to write to `app_debug.log`
3. Display a startup banner with system information
4. Log detailed system information (OS, Python version, memory)
5. Prefetch common data if enabled
6. Start Dash server with debugging enabled

### Banner Display

The application maintains a `.banner_shown` flag file to ensure the banner displays only once per session. This flag is cleaned up on application exit.

### Environment Detection

The application detects whether it's running in the main Flask process or a reloader process using:

```python
def is_main_flask_process():
    """Determine if this is the main Flask process, not the reloader."""
    return os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
```

## Dashboard Configuration

The dashboard is configured in `dashboard.py`:

### App Initialization

```python
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://use.fontawesome.com/releases/v5.15.4/css/all.css'
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)
```

The application uses:
- **Theme**: Bootstrap Darkly theme for a dark mode interface
- **Icons**: Font Awesome 5 for UI elements
- **Viewport Configuration**: Responsive design for multiple devices

### Layout Structure

The main layout includes:
- URL location component for routing
- Navigation bar
- Content container

## Routing

The routing system in `routes.py` maps URL paths to page content:

```python
def render_page_content(pathname):
    """Render the appropriate page content based on URL pathname."""
    # Map paths to layouts
    if pathname == "/":
        return overview_page.layout
    elif pathname == "/setup":
        return setup_page.layout
    # ...other routes...
    else:
        # 404 error page
```

### Route Logging

The route module includes custom logging that:
- Tracks the last visited path to prevent duplicate log entries
- Logs only to the log file, not to console
- Includes the path being rendered

## Navigation

The navigation bar in `layouts/navbar.py` provides:

```python
navbar = dbc.Navbar(
    # Navigation configuration
)
```

Features:
- Responsive design with mobile hamburger menu
- Full-width styling
- Bootstrap-based styling with dark theme
- Links to all major sections

## Logging

The application implements a comprehensive logging system:

### Log Configuration

- **Target**: File-only logging to `app_debug.log`
- **Format**: Timestamp, logger name, level, and message
- **Levels**: INFO for normal operation, WARNING for issues

### Logger Hierarchy

- `budget_app`: Root logger for the application
- `budget_app.routes`: Logger for the routing module
- `budget_app.dashboard`: Logger for the dashboard module
- `cache`: Logger for the caching system

### Log File Management

The log file is cleared at the start of each session and begins with:
```
=== Log started at YYYY-MM-DD HH:MM:SS ===
```

This ensures logs remain manageable and focused on the current session.
