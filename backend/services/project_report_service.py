"""
Project Report Service - AI-powered comprehensive project reports

Generates detailed reports for carbon credit projects using LLM
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    
logger = logging.getLogger(__name__)


class ProjectReportService:
    """Service for generating AI-powered project reports"""
    
    def __init__(self, pathway_reader):
        """
        Initialize Project Report Service
        
        Args:
            pathway_reader: PathwayDataReader instance
        """
        self.pathway_reader = pathway_reader
        self.llm = self._initialize_llm()
        logger.info("✅ Project Report Service initialized")
    
    def _initialize_llm(self):
        """Initialize Gemini model for report generation"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("⚠️ GOOGLE_API_KEY not found - LLM reports disabled")
            return None
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            logger.info(f"✅ LLM initialized with model: gemini-pro")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None
    
    def _create_prompt(self, project_data: Dict[str, Any]) -> str:
        """Create the prompt for report generation"""
        system_instructions = """
You are an expert carbon credit analyst and sustainability consultant. Generate comprehensive, 
professional reports about carbon offset projects based on the provided data.

Your report should include:

1. **Executive Summary** (2-3 sentences)
   - Project overview and main impact
   - Key achievement or unique selling point

2. **Project Description** (2-3 detailed paragraphs)
   - Methodology and technical approach
   - Location specifics and environmental context
   - Scale of operation and implementation details
   - Technology, practices, or conservation methods used

3. **Environmental Impact** (detailed section with bullet points)
   - Specific carbon reduction/sequestration metrics
   - Co-benefits: biodiversity, water quality, soil health, community benefits
   - Long-term sustainability and monitoring
   - Contribution to SDGs (Sustainable Development Goals)

4. **Key Metrics & Verification**
   - Available credits and vintage year
   - Registry status and certification
   - Methodology standards
   - Price analysis and market positioning

5. **Investment Analysis** (3-5 detailed points)
   - Why this project is attractive for carbon credit buyers
   - Risk factors and considerations
   - Market positioning and competitiveness
   - Quality indicators and additionality

6. **Technical Details**
   - Registry and verification standards
   - Monitoring and reporting protocols
   - Permanence and leakage considerations

Make the report:
- Professional, detailed, and data-driven
- At least 500-800 words
- Balanced (highlight both strengths and considerations)
- Informative for investors, companies, and sustainability managers
- Use proper markdown formatting with headers, bullet points, bold text
- Be specific using the provided data
- If description is limited, extrapolate based on category and methodology

DO NOT make up specific numbers not provided. Use the factual data given, and provide context based on the project category and methodology standards.
"""
        
        prompt = f"""{system_instructions}

Generate a comprehensive report for this carbon credit project:

Project ID: {project_data.get('project_id', 'N/A')}
Project Name: {project_data.get('project_name', 'Unknown Project')}
Country: {project_data.get('country', 'N/A')}
Category: {project_data.get('category', 'N/A')}
Methodology: {project_data.get('methodology', 'N/A')}
Vintage: {project_data.get('vintage', 'N/A')}
Available Credits: {project_data.get('available_credits', 0):,}
Price per Credit: ${project_data.get('price', 0):.2f}
Registry Status: {project_data.get('registry_status', 'N/A')}
Description: {project_data.get('description', 'No description available')}

Generate a detailed, professional report in markdown format."""
        
        return prompt
    
    def generate_project_report(self, project_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive AI-powered report for a project
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict with report data and AI-generated content
        """
        try:
            # Get project data
            project_result = self.pathway_reader.get_projects(limit=10000)
            project = next(
                (p for p in project_result if p.get('project_id') == project_id), 
                None
            )
            
            if not project:
                return {
                    'success': False, 
                    'error': f'Project {project_id} not found'
                }
            
            # Generate AI report if LLM is available
            ai_report = None
            if self.llm:
                try:
                    logger.info(f"🤖 Generating AI report for {project_id}...")
                    prompt = self._create_prompt({
                        'project_id': project.get('project_id', 'N/A'),
                        'project_name': project.get('project_name', 'Unknown Project'),
                        'country': project.get('country', 'N/A'),
                        'category': project.get('category', 'N/A'),
                        'methodology': project.get('methodology', 'N/A'),
                        'vintage': project.get('vintage', 'N/A'),
                        'available_credits': project.get('available_credits', 0),
                        'price': project.get('price', 0),
                        'registry_status': project.get('registry_status', 'N/A'),
                        'description': project.get('description', 'No description available')
                    })
                    response = self.llm.generate_content(prompt)
                    ai_report = response.text
                    logger.info(f"✅ AI report generated for {project_id}")
                except Exception as e:
                    logger.error(f"LLM error for {project_id}: {e}")
                    logger.info(f"⚠️ Using fallback report instead")
                    ai_report = self.get_fallback_report(project)
            else:
                # No LLM available, use fallback
                logger.info(f"⚠️ No LLM available, using fallback report for {project_id}")
                ai_report = self.get_fallback_report(project)
            
            # Generate fallback charts/metrics
            charts = self._generate_project_charts(project)
            
            return {
                'success': True,
                'data': {
                    **project,
                    'id': project.get('project_id', ''),
                    'name': project.get('project_name', ''),
                    'ai_report': ai_report,
                    'has_ai_report': ai_report is not None,
                    'charts': charts
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating report for {project_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_project_charts(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for project visualization"""
        
        # Carbon impact over time (estimated based on available credits)
        total_credits = project.get('available_credits', 0)
        vintage = project.get('vintage') or 2023
        if vintage is None or not isinstance(vintage, int):
            vintage = 2023
        current_year = 2025
        
        carbon_impact = []
        years_range = range(vintage, current_year + 1)
        for i, year in enumerate(years_range):
            credits = int(total_credits * (i + 1) / len(list(years_range)))
            carbon_impact.append({
                'year': str(year),
                'credits_issued': credits,
                'co2_offset': credits  # 1 credit = 1 tonne CO2
            })
        
        # Category breakdown (simplified)
        category = project.get('category', 'Other')
        category_data = [
            {'name': category, 'value': 100, 'color': '#34d399'}
        ]
        
        # Price trend (simulated)
        price = project.get('price', 10)
        price_trend = []
        months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i, month in enumerate(months):
            price_val = price * (0.9 + i * 0.035)
            price_trend.append({
                'month': month,
                'price': round(price_val, 2)
            })
        
        # Impact metrics
        total_credits = total_credits or 0
        impact_metrics = {
            'total_co2_offset': total_credits,
            'equivalent_cars': int(total_credits / 4.6) if total_credits > 0 else 0,  # Average car = 4.6 tonnes CO2/year
            'equivalent_trees': int(total_credits * 16) if total_credits > 0 else 0,   # 1 tree = ~0.06 tonnes CO2/year
            'households_powered': int(total_credits / 7.5) if total_credits > 0 else 0 # Average household = 7.5 tonnes CO2/year
        }
        
        return {
            'carbon_impact': carbon_impact,
            'category_breakdown': category_data,
            'price_trend': price_trend,
            'impact_metrics': impact_metrics
        }
    
    def get_fallback_report(self, project: Dict[str, Any]) -> str:
        """Generate a basic structured report when LLM is unavailable"""
        
        project_id = project.get('project_id', 'N/A')
        name = project.get('project_name', 'Unknown Project')
        country = project.get('country', 'N/A')
        category = project.get('category', 'N/A')
        methodology = project.get('methodology', 'N/A')
        vintage = project.get('vintage', 'N/A')
        credits = project.get('available_credits', 0)
        price = project.get('price', 0)
        description = project.get('description', 'No description available.')
        
        report = f"""# {name}

## Executive Summary

{name} is a {category.lower()} project located in {country}, verified under {methodology} standards. 
The project has {credits:,} carbon credits available from vintage {vintage}.

## Project Details

**Location:** {country}  
**Category:** {category}  
**Methodology:** {methodology}  
**Registry Status:** {project.get('registry_status', 'Active')}  
**Vintage Year:** {vintage}

## Description

{description}

## Key Metrics

- **Available Credits:** {credits:,} tCO2e
- **Price per Credit:** ${price:.2f}
- **Total Market Value:** ${credits * price:,.0f}
- **CO2 Equivalent:** {credits:,} tonnes of CO2 offset

## Environmental Impact

This project contributes to:
- Carbon sequestration and emissions reduction
- Supporting sustainable development in {country}
- Verified environmental benefits through {methodology}

## Investment Considerations

### Strengths
- Verified under recognized {methodology} standards
- Active registry status
- {category} projects typically offer strong co-benefits

### Considerations
- Market price subject to carbon credit market fluctuations
- Vintage year: {vintage}
- Available supply: {credits:,} credits

## Verification

This project is registered and verified through the Verra Registry under {methodology} methodology, 
ensuring transparent and credible carbon credit issuance.

---
*Report generated from Verra Registry data*
"""
        return report
