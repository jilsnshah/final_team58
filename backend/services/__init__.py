"""
Backend Services - Modular functionality for frontend features
Each service file corresponds to a specific frontend feature
"""

from .live_news_service import LiveNewsService
from .watchlist_service import WatchlistService
from .projects_service import ProjectsService
from .analytics_service import AnalyticsService
from .company_service import CompanyService

__all__ = [
    'LiveNewsService',
    'WatchlistService', 
    'ProjectsService',
    'AnalyticsService',
    'CompanyService'
]
