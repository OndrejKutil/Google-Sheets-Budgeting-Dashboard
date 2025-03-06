# Budget Dashboard Documentation

Welcome to the Budget Dashboard documentation. This documentation provides a comprehensive overview of the application's architecture, components, and functionality.

## Documentation Sections

### [Data Fetching and Analysis](data_fetch_analyze.md)
- Google Sheets integration
- Caching system
- Financial analysis functions
- Category management

### [Site Setup](site_setup.md)
- Application structure
- Initialization process
- Dashboard configuration
- Routing system
- Navigation
- Logging system

### [Pages and Components](pages_components.md)
- Overview Page
- Monthly Analysis Page
- Transactions Page
- Accounts Page
- Savings Page
- Setup Page
- Common UI Components

## Quick Start

To run the application:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python src/main.py
```

The application will be available at http://127.0.0.1:8050/

## Architecture Overview

The Budget Dashboard follows a modular architecture with:

1. **Data Layer**: Google Sheets integration and caching (`data_fetch.py`, `get_categories.py`)
2. **Analysis Layer**: Financial calculations and data processing (`analysis.py`)
3. **Application Layer**: Dash application setup (`dashboard.py`, `routes.py`) 
4. **Presentation Layer**:
   - Page layouts and UI components (`pages/`)
   - Layout components (`layouts/`)
   - Styling definitions (`styles/`)

### Directory Structure

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
    ├── theme.py          # Color schemes and theme variables
    └── common_styles.py  # Reusable style definitions
```

## Development Guidelines

When modifying the codebase:

1. **Caching**: Use the `@cached` decorator for functions that retrieve data
2. **Error Handling**: Always include appropriate error handling for API calls
3. **Logging**: Use the appropriate logger for each module
4. **Styling**: Follow the established style patterns in the `styles` directory
5. **Documentation**: Update this documentation when adding new features

## Return to Main README

For high-level project overview and features, see the [Main README](../README.md).
