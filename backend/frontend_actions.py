"""
Frontend Actions - Simple functions to control frontend behavior

Simple functions that can be called to trigger actions on the frontend.
Uses WebSocket to send commands to the frontend.
Can be called via HTTP requests when running in separate process.
"""

import logging
import requests

logger = logging.getLogger(__name__)

# Global socketio instance - will be set from app.py
_socketio = None
_api_mode = False  # Use HTTP API when True, socketio when False
_api_url = "http://localhost:5001"

# Store current watchlist state (updated via WebSocket from frontend)
_current_watchlist = []

def set_socketio(socketio_instance):
    """Set the socketio instance to use for emitting events"""
    global _socketio, _api_mode
    _socketio = socketio_instance
    _api_mode = False
    logger.info("✅ SocketIO instance set for frontend actions")

def use_api_mode(api_url="http://localhost:5001"):
    """Enable API mode for calling actions via HTTP"""
    global _api_mode, _api_url
    _api_mode = True
    _api_url = api_url
    logger.info(f"✅ API mode enabled: {api_url}")

def update_watchlist_state(watchlist_data):
    """Update the current watchlist state from frontend"""
    global _current_watchlist
    _current_watchlist = watchlist_data
    logger.info(f"📋 Watchlist state updated: {len(watchlist_data)} companies")

def get_current_watchlist():
    """Get the current watchlist state"""
    return _current_watchlist


def change_theme():
    """
    Toggle the theme between light and dark mode
    """
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/change_theme")
            logger.info("🎨 Theme change command sent to frontend")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error changing theme: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        logger.info("🎨 About to emit change_theme event...")
        _socketio.emit('change_theme', {
            'action': 'toggle'
        })
        logger.info("🎨 Theme change command sent to frontend")
        return True
    except Exception as e:
        logger.error(f"❌ Error changing theme: {str(e)}")
        return False


def add_company_to_watchlist(company_name, company_symbol=None):
    """
    Add a company to the watchlist
    
    Args:
        company_name: Name of the company to add
        company_symbol: Optional stock symbol
    """
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/add_to_watchlist", 
                                    json={'company_name': company_name, 'company_symbol': company_symbol})
            logger.info(f"➕ Added {company_name} to watchlist")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error adding company to watchlist: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        _socketio.emit('add_to_watchlist', {
            'company_name': company_name,
            'company_symbol': company_symbol or company_name
        })
        logger.info(f"➕ Added {company_name} to watchlist")
        return True
    except Exception as e:
        logger.error(f"❌ Error adding company to watchlist: {str(e)}")
        return False


def remove_company_from_watchlist(company_name):
    """
    Remove a company from the watchlist
    
    Args:
        company_name: Name of the company to remove
    """
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/remove_from_watchlist", 
                                    json={'company_name': company_name})
            logger.info(f"➖ Removed {company_name} from watchlist")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error removing company from watchlist: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        _socketio.emit('remove_from_watchlist', {
            'company_name': company_name
        })
        logger.info(f"➖ Removed {company_name} from watchlist")
        return True
    except Exception as e:
        logger.error(f"❌ Error removing company from watchlist: {str(e)}")
        return False


def go_to_company_page(company_name, ticker=None):
    """
    Navigate to a specific company's detail page
    
    Args:
        company_name: Name of the company to navigate to
        ticker: Stock ticker symbol (e.g., 'TSLA'). If provided, uses this for the URL.
    """
    # Use ticker for URL if provided, otherwise use company_name
    url_id = ticker or company_name
    
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/navigate", 
                                    json={'action': 'company', 'company_name': company_name, 'ticker': url_id})
            logger.info(f"🧭 Navigating to company page: {company_name} (ticker: {url_id})")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error navigating to company page: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        _socketio.emit('navigate', {
            'action': 'company',
            'company_name': company_name,
            'ticker': url_id
        })
        logger.info(f"🧭 Navigating to company page: {company_name} (ticker: {url_id})")
        return True
    except Exception as e:
        logger.error(f"❌ Error navigating to company page: {str(e)}")
        return False


def go_to_projects_page():
    """
    Navigate to the projects page
    """
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/navigate", 
                                    json={'action': 'projects'})
            logger.info("🧭 Navigating to projects page")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error navigating to projects page: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        _socketio.emit('navigate', {
            'action': 'projects'
        })
        logger.info("🧭 Navigating to projects page")
        return True
    except Exception as e:
        logger.error(f"❌ Error navigating to projects page: {str(e)}")
        return False


def go_to_project_page(project_id):
    """
    Navigate to a specific project's detail/report page
    
    Args:
        project_id: Project ID or code (e.g., 'VCS191', '3519')
    """
    if _api_mode:
        try:
            response = requests.post(f"{_api_url}/api/frontend/navigate", 
                                    json={'action': 'project', 'project_id': project_id})
            logger.info(f"🧭 Navigating to project page: {project_id}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Error navigating to project page: {str(e)}")
            return False
    
    if _socketio is None:
        logger.error("❌ SocketIO not initialized. Call set_socketio() or use_api_mode() first.")
        return False
    
    try:
        _socketio.emit('navigate', {
            'action': 'project',
            'project_id': project_id
        })
        logger.info(f"🧭 Navigating to project page: {project_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Error navigating to project page: {str(e)}")
        return False
