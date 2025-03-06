import logging
import sys
import time
import platform
import os
import atexit
import signal
from datetime import datetime
from dashboard import app
from data_fetch import prefetch_common_data, load_settings, get_cache_stats

# Clear the log file before initializing logging
LOG_FILE = "app_debug.log"
with open(LOG_FILE, 'w') as f:
    f.write(f"=== Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

# Disable root logger and reconfigure logging completely
logging.getLogger().handlers = []

# Create logger instance that writes to file only
logger = logging.getLogger("budget_app")
logger.setLevel(logging.INFO)
logger.propagate = False  # Don't propagate to parent loggers

# Set up file handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create a flag file to ensure we only print the banner once
BANNER_FLAG_FILE = '.banner_shown'

def print_startup_banner():
    """Print a fancy startup banner with useful system information."""
    # Check if banner has already been shown this session
    if os.path.exists(BANNER_FLAG_FILE):
        return
        
    # Create the flag file to indicate banner has been shown
    with open(BANNER_FLAG_FILE, 'w') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🌟 Google Sheets Budget Dashboard 🌟                    ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    
    # Application information
    app_info = f"""
    📊 Starting Budget Dashboard Application
    🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    🖥️ System: {platform.system()} {platform.release()} ({platform.architecture()[0]})
    🐍 Python: {platform.python_version()}
    """
    
    # Cache information
    settings = load_settings()
    cache_info = f"""
    🔧 Settings:
    ├─ Cache Enabled: {'✅' if settings.get('cache_enabled', True) else '❌'}
    ├─ Prefetch Enabled: {'✅' if settings.get('prefetch_enabled', True) else '❌'}
    ├─ Cache Duration: {settings.get('cache_duration', 300)} seconds
    └─ Debug Mode: {'✅' if settings.get('debug_mode', False) else '❌'}
    """

    print(banner)
    print(app_info)
    print(cache_info)
    print("    Starting server...")
    print("    " + "═" * 60)

def cleanup_banner_file():
    """Remove the banner flag file when the application exits."""
    try:
        if os.path.exists(BANNER_FLAG_FILE):
            os.remove(BANNER_FLAG_FILE)
            logger.info("Banner flag file cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up banner flag file: {e}")

# Register cleanup function to be called on normal program exit
atexit.register(cleanup_banner_file)

# Also handle SIGTERM for container environments
def sigterm_handler(signum, frame):
    """Handle SIGTERM signal by cleaning up and exiting."""
    logger.info("Received SIGTERM signal, cleaning up...")
    cleanup_banner_file()
    sys.exit(0)

# Register SIGTERM handler on POSIX systems
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, sigterm_handler)

def log_system_info():
    """Log detailed system information to the log file only (not console)."""
    logger.info("Application starting with configuration:")
    logger.info(f"OS: {platform.platform()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"CPU: {platform.processor()}")
    
    # Log memory information if available
    try:
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Memory: {memory.total / (1024**3):.2f} GB total, {memory.available / (1024**3):.2f} GB available")
    except ImportError:
        logger.info("Memory info: psutil not installed")

def is_main_flask_process():
    """Determine if this is the main Flask process, not the reloader."""
    # The reloader uses WERKZEUG_RUN_MAIN in the main process
    return os.environ.get('WERKZEUG_RUN_MAIN') == 'true'

# Configure all child loggers to use file only
for log_name in ['budget_app.routes', 'budget_app.dashboard', 'cache']:
    child_logger = logging.getLogger(log_name)
    child_logger.handlers = []
    child_logger.addHandler(file_handler)
    child_logger.propagate = False
    child_logger.setLevel(logging.INFO)

# Silence werkzeug logs to console by redirecting to file only
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = []
werkzeug_logger.addHandler(file_handler)
werkzeug_logger.propagate = False
werkzeug_logger.setLevel(logging.WARNING)  # Only log warnings and above

app.title = "Budget Dashboard"

if __name__ == "__main__":
    try:
        # Only show welcome banner and log system info once
        print_startup_banner()
        log_system_info()
        
        # Prefetch data (only log to file, don't print)
        try:
            settings = load_settings()
            if settings.get('prefetch_enabled', True):
                logger.info("Prefetching data...")
                start_time = time.time()
                prefetch_common_data()
                logger.info(f"Prefetch completed in {time.time() - start_time:.2f} seconds")
                
                # Log cache statistics after prefetch
                stats = get_cache_stats()
                logger.info(f"Cache status: {stats['current_size']} entries cached")
        except Exception as e:
            logger.error(f"Error during prefetch: {e}")
        
        # Log start message but don't print to console
        logger.info("Starting Dash server...")
        
        # Start the application
        import io
        from contextlib import redirect_stdout
        
        # Redirect stdout to suppress Flask's startup messages
        with redirect_stdout(io.StringIO()):
            app.run_server(debug=True)
    finally:
        # Ensure flag file is cleaned up even if app crashes
        cleanup_banner_file()
