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
    
    def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """
        Get specific project details
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with project data
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            project = next(
                (p for p in projects if p.get('project_id') == project_id), 
                None
            )
            
            if project:
                # Ensure frontend compatibility - map project_id to id as well
                project_data = dict(project)
                project_data['id'] = project_data.get('project_id', '')
                project_data['name'] = project_data.get('project_name', '')
                return {'success': True, 'data': project_data}
            else:
                return {'success': False, 'error': f'Project {project_id} not found'}
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_projects_by_category(self) -> Dict[str, Any]:
        """
        Get projects grouped by category
        
        Returns:
            Dict with categories and project counts
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            
            categories = {}
            for project in projects:
                cat = project.get('category', 'Other')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(project)
            
            return {
                'success': True,
                'categories': {
                    cat: {
                        'count': len(projects),
                        'projects': projects[:5]  # Top 5 per category
                    }
                    for cat, projects in categories.items()
                }
            }
        except Exception as e:
            logger.error(f"Error grouping projects by category: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_countries_list(self) -> List[str]:
        """
        Get list of all countries with projects
        
        Returns:
            List of country names
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            countries = sorted(set(p.get('country', 'Unknown') for p in projects))
            logger.info(f"🗺️ Found projects in {len(countries)} countries")
            return countries
        except Exception as e:
            logger.error(f"Error getting countries: {e}")
            return []
    
    def get_categories_list(self) -> List[str]:
        """
        Get list of all project categories
        
        Returns:
            List of category names
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            categories = sorted(set(p.get('category', 'Other') for p in projects))
            logger.info(f"📂 Found {len(categories)} project categories")
            return categories
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_featured_projects(self, limit: int = 6) -> Dict[str, Any]:
        """
        Get featured/recommended projects (highest rated)
        
        Args:
            limit: Number of featured projects
            
        Returns:
            Dict with featured projects
        """
        try:
            projects = self.pathway_reader.get_projects(limit=1000)
            
            # Sort by available credits and price (most impactful)
            featured = sorted(
                projects, 
                key=lambda x: (x.get('available_credits', 0), -x.get('price', 999)), 
                reverse=True
            )[:limit]
            
            # Ensure frontend compatibility
            formatted_featured = []
            for p in featured:
                project_data = dict(p)
                project_data['id'] = p.get('project_id', '')
                project_data['name'] = p.get('project_name', '')
                formatted_featured.append(project_data)
            
            return {
                'success': True,
                'count': len(formatted_featured),
                'data': formatted_featured
            }
        except Exception as e:
            logger.error(f"Error getting featured projects: {e}")
            return {'success': False, 'error': str(e), 'data': []}
