"""
Analytics Service - Dashboard analytics and metrics

Frontend Feature: Dashboard - Analytics Overview
Endpoints: GET /api/analytics, GET /api/analytics/esg, GET /api/analytics/carbon-trends
"""

import logging
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for dashboard analytics and metrics"""
    
    def __init__(self, pathway_reader):
        """
        Initialize Analytics Service
        
        Args:
            pathway_reader: PathwayDataReader instance
        """
        self.pathway_reader = pathway_reader
        logger.info("✅ Analytics Service initialized")
    
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics for dashboard overview
        
        Returns:
            Dict with all analytics metrics
        """
        try:
            analytics = self.pathway_reader.get_analytics()
            
            return {
                'success': True,
                'analytics': analytics.get('analytics', {}),
                'projects': analytics.get('projects', {}),
                'finance': analytics.get('finance', {}),
                'news': analytics.get('news', {}),
                'timestamp': analytics.get('timestamp', '')
            }
        except Exception as e:
            logger.error(f"Error getting dashboard analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_esg_analysis(self, tickers: List[str] = None) -> Dict[str, Any]:
        """
        Analyze ESG scores across companies
        
        Args:
            tickers: Optional list of specific tickers to analyze
            
        Returns:
            Dict with ESG analysis results
        """
        try:
            if tickers:
                finance_data = []
                for ticker in tickers:
                    data = self.pathway_reader.get_finance(ticker=ticker)
                    finance_data.extend(data)
            else:
                finance_data = self.pathway_reader.get_finance()
            
            if not finance_data:
                return {'success': False, 'error': 'No finance data available'}
            
            # Calculate ESG metrics
            esg_scores = defaultdict(list)
            for company in finance_data:
                rating = company.get('esg_rating', 'N/A')
                gii_score = company.get('gii_score', 0)
                if rating != 'N/A' and gii_score > 0:
                    esg_scores[rating].append(gii_score)
            
            # Average GII score per ESG rating
            esg_summary = {}
            for rating, scores in esg_scores.items():
                esg_summary[rating] = {
                    'avg_gii_score': round(sum(scores) / len(scores), 2),
                    'company_count': len(scores)
                }
            
            return {
                'success': True,
                'total_companies': len(finance_data),
                'esg_distribution': esg_summary,
                'avg_gii_score': round(sum(c.get('gii_score', 0) for c in finance_data) / len(finance_data), 2)
            }
        except Exception as e:
            logger.error(f"Error analyzing ESG scores: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_carbon_trends(self) -> Dict[str, Any]:
        """
        Analyze carbon credit market trends
        
        Returns:
            Dict with carbon market trends
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            
            if not projects:
                return {'success': False, 'error': 'No projects data available'}
            
            # Price trends by category
            category_stats = defaultdict(lambda: {'total_credits': 0, 'total_value': 0, 'count': 0, 'prices': []})
            
            for project in projects:
                cat = project.get('category', 'Other')
                credits = project.get('available_credits', 0)
                price = project.get('price', 0)
                
                category_stats[cat]['total_credits'] += credits
                category_stats[cat]['total_value'] += credits * price
                category_stats[cat]['count'] += 1
                category_stats[cat]['prices'].append(price)
            
            # Calculate averages
            trends = {}
            for cat, stats in category_stats.items():
                avg_price = sum(stats['prices']) / len(stats['prices']) if stats['prices'] else 0
                trends[cat] = {
                    'total_credits': stats['total_credits'],
                    'total_value': round(stats['total_value'], 2),
                    'project_count': stats['count'],
                    'avg_price': round(avg_price, 2)
                }
            
            return {
                'success': True,
                'total_supply': sum(p.get('available_credits', 0) for p in projects),
                'avg_price': round(sum(p.get('price', 0) for p in projects) / len(projects), 2),
                'category_trends': trends
            }
        except Exception as e:
            logger.error(f"Error analyzing carbon trends: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_news_sentiment_analysis(self) -> Dict[str, Any]:
        """
        Analyze sentiment distribution in news
        
        Returns:
            Dict with sentiment analysis
        """
        try:
            news = self.pathway_reader.get_news(limit=1000)
            
            if not news:
                return {'success': False, 'error': 'No news data available'}
            
            # Count sentiments
            sentiment_counts = defaultdict(int)
            for article in news:
                sentiment = article.get('sentiment', 'Neutral')
                sentiment_counts[sentiment] += 1
            
            total = len(news)
            sentiment_distribution = {
                sentiment: {
                    'count': count,
                    'percentage': round((count / total) * 100, 1)
                }
                for sentiment, count in sentiment_counts.items()
            }
            
            return {
                'success': True,
                'total_articles': total,
                'sentiment_distribution': sentiment_distribution,
                'dominant_sentiment': max(sentiment_counts.items(), key=lambda x: x[1])[0]
            }
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        Get overall market summary statistics
        
        Returns:
            Dict with market summary
        """
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            finance = self.pathway_reader.get_finance()
            news = self.pathway_reader.get_news(limit=100)
            
            # Calculate key metrics
            total_carbon_supply = sum(p.get('available_credits', 0) for p in projects)
            avg_carbon_price = sum(p.get('price', 0) for p in projects) / len(projects) if projects else 0
            
            # Stock market performance
            avg_stock_change = sum(c.get('change_percent', 0) for c in finance) / len(finance) if finance else 0
            
            # Recent news sentiment
            recent_positive = sum(1 for n in news[:20] if n.get('sentiment') == 'Positive')
            sentiment_score = (recent_positive / 20) * 100 if len(news) >= 20 else 50
            
            return {
                'success': True,
                'market_summary': {
                    'carbon_market': {
                        'total_supply': total_carbon_supply,
                        'avg_price': round(avg_carbon_price, 2),
                        'active_projects': len(projects)
                    },
                    'stock_market': {
                        'tracked_companies': len(finance),
                        'avg_change_percent': round(avg_stock_change, 2)
                    },
                    'sentiment_score': round(sentiment_score, 1),
                    'recent_news_count': len(news)
                }
            }
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {'success': False, 'error': str(e)}
