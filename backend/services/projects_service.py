"""
Projects Service - Carbon credit projects marketplace functionality

Frontend Feature: ProjectsPage - Carbon Marketplace
Endpoints: GET /api/projects, POST /api/projects/search
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ProjectsService:
    """Service for carbon credit projects marketplace"""
    
    def __init__(self, pathway_reader):
        """
        Initialize Projects Service
        
        Args:
            pathway_reader: PathwayDataReader instance
        """
        self.pathway_reader = pathway_reader
        logger.info("✅ Projects Service initialized")
    
    def get_all_projects(self, limit: int = 500, country: str = None, category: str = None) -> Dict[str, Any]:
        """
        Get all carbon credit projects with filters
        
        Args:
            limit: Maximum number of projects
            country: Filter by country (optional)
            category: Filter by category (optional)
            
        Returns:
            Dict with projects data
        """
        try:
            projects = self.pathway_reader.get_projects(country=country, limit=limit)
            
            # Apply category filter if provided
            if category:
                projects = [p for p in projects if p.get('category') == category]
            
            # Ensure frontend compatibility - add 'id' and 'name' fields
            formatted_projects = []
            for p in projects:
                project_data = dict(p)
                project_data['id'] = p.get('project_id', '')
                project_data['name'] = p.get('project_name', '')
                formatted_projects.append(project_data)
            
            logger.info(f"🌍 Retrieved {len(formatted_projects)} projects")
            return {
                'success': True,
                'count': len(formatted_projects),
                'data': formatted_projects
            }
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return {'success': False, 'error': str(e), 'data': []}
    
    def search_projects(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """
        Semantic search for carbon projects
        
        Args:
            query: Search query string
            limit: Maximum results
            
        Returns:
            Dict with search results
        """
        try:
            results = self.pathway_reader.search_projects(query=query, limit=limit)
            
            # Ensure frontend compatibility
            formatted_results = []
            for p in results:
                project_data = dict(p)
                project_data['id'] = p.get('project_id', '')
                project_data['name'] = p.get('project_name', '')
                formatted_results.append(project_data)
            
            logger.info(f"🔍 Search '{query}': found {len(formatted_results)} projects")
            return {
                'success': True,
                'query': query,
                'count': len(formatted_results),
                'data': formatted_results
            }
        except Exception as e:
            logger.error(f"Error searching projects: {e}")
            return {'success': False, 'error': str(e), 'data': []}
