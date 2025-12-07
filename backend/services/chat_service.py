"""
Chat Service - RAG-powered chat using LangChain and Gemini

Provides conversational AI capabilities with context awareness for:
- Company-specific questions (ESG, financials, sustainability)
- Project-specific questions (carbon credits, methodology)
- General sustainability and carbon market questions
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import LangChain and Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("⚠️ LangChain not installed. Install with: pip install langchain-google-genai langchain-core")


class ChatService:
    """Service for AI-powered chat using LangChain and Gemini"""
    
    def __init__(self, pathway_reader):
        """
        Initialize Chat Service
        
        Args:
            pathway_reader: PathwayDataReader instance for fetching context
        """
        self.pathway_reader = pathway_reader
        self.llm = None
        self.chat_chain = None
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_llm()
        else:
            logger.warning("⚠️ LangChain not available - chat will use fallback responses")
        
        logger.info("✅ Chat Service initialized")
    
    def _initialize_llm(self):
        """Initialize Gemini LLM with LangChain"""
        try:
            api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                logger.warning("⚠️ GOOGLE_API_KEY not found in environment variables")
                logger.info("💡 Set GOOGLE_API_KEY to enable AI chat features")
                return
            
            logger.info(f"🔑 API key found (length: {len(api_key)})")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0.7,
                max_tokens=1024,
                google_api_key=api_key
            )
            
            # Create the chat chain
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are EcoInvest AI, an expert assistant for carbon intelligence and sustainable investing.
                
You help users understand:
- ESG (Environmental, Social, Governance) ratings and metrics
- Carbon credit projects and markets
- Company sustainability performance and financials
- News and trends in sustainability and carbon markets

When provided with context about a company or project, use that information to give accurate, data-driven answers.
Be concise, professional, and helpful. Format numbers with appropriate units. Do not give financial advice. Return answer in normal text format that can be directly used by the user. Do not return markdown or code blocks.

Context: {context}"""),
                ("human", "{question}")
            ])
            
            self.chat_chain = prompt_template | self.llm | StrOutputParser()
            
            logger.info("✅ Gemini LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini LLM: {e}")
            self.llm = None
            self.chat_chain = None
    
    def _get_company_context(self, ticker: str) -> str:
        """Get context about a company"""
        try:
            finance_data = self.pathway_reader.get_finance(ticker=ticker)
            if finance_data and len(finance_data) > 0:
                company = finance_data[0]
                return f"""Company: {company.get('company_name', ticker)}
Industry: {company.get('industry', 'N/A')}
Stock Price: ${company.get('price', 0)}
Market Cap: {company.get('market_cap', 'N/A')}
ESG Rating: {company.get('esg_rating', 'N/A')}
GII Score: {company.get('gii_score', 'N/A')}
Description: {company.get('description', 'No description available')}
Sustainability Update: {company.get('sustainability_update', 'No recent updates')}"""
            return f"No data found for company {ticker}"
        except Exception as e:
            logger.error(f"Error getting company context: {e}")
            return "Unable to retrieve company data"
    
    def _get_project_context(self, project_id: str) -> str:
        """Get context about a carbon project"""
        try:
            projects = self.pathway_reader.get_projects(limit=10000)
            project = next(
                (p for p in projects if p.get('project_id') == project_id),
                None
            )
            
            if project:
                return f"""Project: {project.get('project_name', project_id)}
Category: {project.get('category', 'N/A')}
Country: {project.get('country', 'N/A')}
Methodology: {project.get('methodology', 'N/A')}
Price per Credit: ${project.get('price', 0)}
Available Credits: {project.get('available_credits', 0):,}
Vintage: {project.get('vintage', 'N/A')}
Description: {project.get('description', 'No description available')}"""
            return f"No data found for project {project_id}"
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return "Unable to retrieve project data"
    
    def _get_general_context(self) -> str:
        """Get general context about the platform"""
        try:
            # Get summary statistics
            projects = self.pathway_reader.get_projects(limit=10000)
            finance = self.pathway_reader.get_finance()
            news = self.pathway_reader.get_news(limit=100)
            
            return f"""Platform Overview:
- {len(projects)} carbon credit projects available
- {len(finance)} companies tracked
- {len(news)} recent sustainability news articles
- Focus on ESG investing and carbon markets"""
        except Exception as e:
            logger.error(f"Error getting general context: {e}")
            return "Carbon Intelligence Platform - ESG and Carbon Markets"
    
    def chat(self, message: str, context_type: Optional[str] = None, 
             context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a chat message with optional context
        
        Args:
            message: User's question/message
            context_type: Type of context ('company', 'project', or None for general)
            context_id: ID of the company ticker or project ID
            
        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"💬 Chat request: '{message[:50]}...' (type: {context_type}, id: {context_id})")
            
            # Build context based on type
            if context_type == 'company' and context_id:
                context = self._get_company_context(context_id)
            elif context_type == 'project' and context_id:
                context = self._get_project_context(context_id)
            else:
                context = self._get_general_context()
            
            logger.info(f"📊 Context length: {len(context)} characters")
            
            # Use LangChain if available
            if self.chat_chain:
                logger.info("🤖 Using Gemini AI for response...")
                try:
                    response = self.chat_chain.invoke({
                        "context": context,
                        "question": message
                    })
                    
                    logger.info(f"✅ AI response generated (length: {len(response)})")
                    
                    return {
                        'status': 'success',
                        'response': response,
                        'context_type': context_type,
                        'powered_by': 'Gemini AI'
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Gemini error: {e}")
                    return self._fallback_response(message, context)
            else:
                logger.warning("⚠️ Chat chain not available, using fallback")
                return self._fallback_response(message, context)
                
        except Exception as e:
            logger.error(f"Error in chat service: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'response': "I encountered an error processing your request. Please try again."
            }
    
    def _fallback_response(self, message: str, context: str) -> Dict[str, Any]:
        """Provide a fallback response when LLM is unavailable"""
        response = f"""I'm EcoInvest AI (currently in fallback mode).

Context available:
{context}

Your question: {message}

Note: For intelligent responses, please set up your GOOGLE_API_KEY environment variable and install:
pip install langchain-google-genai langchain-core

For now, I've provided the relevant context above. You can use this information to find your answer."""
        
        return {
            'status': 'success',
            'response': response,
            'powered_by': 'Fallback Mode',
            'note': 'Install LangChain and set GOOGLE_API_KEY for AI responses'
        }
