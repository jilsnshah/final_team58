"""
AI Chatbot Service - LangChain Agent with Tool Calling

A LangChain agent that can call tools to perform frontend actions using Google Gemini.
Uses the modern create_agent API for production-ready agent implementation.
"""

from flask import Blueprint, request, jsonify
import logging
import os
from langchain.agents import create_agent
from langchain.agents.middleware import before_agent
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
import frontend_actions
from llm_manager import get_llm

# Import RAG and Service modules
try:
    from services.news_rag_service import search_news
    from services.projects_rag_service import search_projects
    NEWS_RAG_AVAILABLE = True
    PROJECTS_RAG_AVAILABLE = True
except ImportError:
    NEWS_RAG_AVAILABLE = False
    PROJECTS_RAG_AVAILABLE = False
    print("⚠️ RAG services not available")

# References to services (set by app.py)
_company_service = None
_project_service = None

def set_company_service(service):
    """Set the company service reference from app.py"""
    global _company_service
    _company_service = service
    logger.info("✅ Company service connected to aibot")

def set_project_service(service):
    """Set the project service reference from app.py"""
    global _project_service
    _project_service = service
    logger.info("✅ Project service connected to aibot")

# Set Google API Key
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")  # Use env variable or empty if not set

logger = logging.getLogger(__name__)

# Create Blueprint for chatbot routes
aibot_bp = Blueprint('aibot', __name__)

# Chat history storage
chat_histories = {}

# Reference to pathway_reader (set by app.py)
_pathway_reader = None

def set_pathway_reader(reader):
    """Set the pathway reader reference from app.py"""
    global _pathway_reader
    _pathway_reader = reader
    logger.info("✅ Pathway reader connected to aibot")

def resolve_ticker(company_input: str) -> tuple:
    """
    Resolve company name or ticker to (company_name, ticker).
    Searches the actual finance data from PathwayDataReader.
    
    Args:
        company_input: Either a company name (e.g., 'Tesla') or ticker (e.g., 'TSLA')
        
    Returns:
        Tuple of (company_name, ticker) or (input, input) if not found
    """
    if not _pathway_reader:
        logger.warning("⚠️ No pathway reader available for company lookup")
        return (company_input, company_input.upper())
    
    try:
        finance_data = _pathway_reader.get_finance()
        input_lower = company_input.lower().strip()
        
        # First, try exact ticker match
        for company in finance_data:
            ticker = company.get('ticker', '')
            if ticker.lower() == input_lower:
                name = company.get('company_name', ticker)
                logger.info(f"🔍 Resolved '{company_input}' to ticker: {ticker}")
                return (name, ticker)
        
        # Second, try exact company name match
        for company in finance_data:
            name = company.get('company_name', '')
            if name.lower() == input_lower:
                ticker = company.get('ticker', name)
                logger.info(f"🔍 Resolved '{company_input}' to ticker: {ticker}")
                return (name, ticker)
        
        # Third, try partial name match (company name contains input)
        for company in finance_data:
            name = company.get('company_name', '')
            if input_lower in name.lower():
                ticker = company.get('ticker', name)
                logger.info(f"🔍 Fuzzy matched '{company_input}' to {name} ({ticker})")
                return (name, ticker)
        
        # Fourth, try partial name match (input contains company name)
        for company in finance_data:
            name = company.get('company_name', '')
            if name.lower() and name.lower() in input_lower:
                ticker = company.get('ticker', name)
                logger.info(f"🔍 Fuzzy matched '{company_input}' to {name} ({ticker})")
                return (name, ticker)
        
        # Not found - return as-is with uppercased ticker
        logger.info(f"⚠️ Could not resolve '{company_input}', using as-is")
        return (company_input, company_input.upper())
        
    except Exception as e:
        logger.error(f"Error resolving company: {e}")
        return (company_input, company_input.upper())

# ============================================================================
# DEFINE TOOLS
# ============================================================================

@tool
def change_theme() -> str:
    """Toggle the theme between light and dark mode."""
    success = frontend_actions.change_theme()
    return "Theme changed successfully!" if success else "Failed to change theme."

@tool
def get_company_info(company_name: str) -> str:
    """Get detailed information about a company including stock price, ESG rating, and sustainability initiatives.
    
    Args:
        company_name: Name of the company (e.g., 'Tesla', 'Apple') or ticker (e.g., 'TSLA', 'AAPL')
    
    Returns:
        Detailed company information as a formatted string
    """
    if not _pathway_reader:
        return "Company data is currently unavailable."
    
    try:
        # Resolve company name to ticker
        name, ticker = resolve_ticker(company_name)
        finance_data = _pathway_reader.get_finance()
        
        # Find the company
        for company in finance_data:
            if company.get('ticker', '').upper() == ticker.upper():
                # Format the company info nicely
                price = company.get('price') or company.get('stock_price') or 'N/A'
                change = company.get('change_percent', 0)
                change_str = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
                
                info = f"""
Company: {company.get('company_name', ticker)}
Ticker: {company.get('ticker', 'N/A')}
Industry: {company.get('industry', 'N/A')}
Stock Price: ${price}
Change: {change_str}
Market Cap: {company.get('market_cap') or 'N/A'}
ESG Rating: {company.get('esg_rating', 'N/A')}
GII Score: {company.get('gii_score', 'N/A')}/100
Description: {company.get('description', 'N/A')}
Sustainability: {company.get('sustainability_update', 'N/A')}
Website: {company.get('website', 'N/A')}
"""
                return info.strip()
        
        return f"No information found for {company_name}. The company may not be in our database."
        
    except Exception as e:
        logger.error(f"Error getting company info: {e}")
        return f"Error retrieving company information: {str(e)}"

@tool
def list_available_companies() -> str:
    """List all companies available in the database with their tickers.
    
    Returns:
        A list of all available companies
    """
    if not _pathway_reader:
        return "Company data is currently unavailable."
    
    try:
        finance_data = _pathway_reader.get_finance()
        companies = []
        for company in finance_data:
            ticker = company.get('ticker', '')
            name = company.get('company_name', ticker)
            esg = company.get('esg_rating', 'N/A')
            companies.append(f"• {name} ({ticker}) - ESG: {esg}")
        
        if companies:
            return "Available companies:\n" + "\n".join(companies)
        return "No companies found in database."
        
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        return "Error retrieving company list."

@tool
def add_to_watchlist(company_name: str) -> str:
    """Add a company to the watchlist.
    
    Args:
        company_name: Name of the company (e.g., 'Tesla', 'Apple') or ticker (e.g., 'TSLA', 'AAPL')
    """
    # Resolve company name to ticker using actual finance data
    name, ticker = resolve_ticker(company_name)
    success = frontend_actions.add_company_to_watchlist(name, ticker)
    return f"Added {name} ({ticker}) to watchlist!" if success else f"Failed to add {company_name}."

@tool
def remove_from_watchlist(company_name: str) -> str:
    """Remove a company from the watchlist.
    
    Args:
        company_name: Name of the company or ticker to remove
    """
    # Resolve company name to ticker
    name, ticker = resolve_ticker(company_name)
    success = frontend_actions.remove_company_from_watchlist(ticker)
    return f"Removed {name} ({ticker}) from watchlist!" if success else f"Failed to remove {company_name}."

@tool
def go_to_company(company_name: str) -> str:
    """Navigate to a company's detail page.
    
    Args:
        company_name: Name of the company (e.g., 'Tesla') or ticker (e.g., 'TSLA')
    """
    # Resolve company name to ticker
    name, ticker = resolve_ticker(company_name)
    success = frontend_actions.go_to_company_page(name, ticker)
    return f"Navigating to {name} ({ticker})!" if success else f"Failed to navigate."

@tool
def go_to_projects() -> str:
    """Navigate to the carbon projects page."""
    success = frontend_actions.go_to_projects_page()
    return "Navigating to projects page!" if success else "Failed to navigate to projects."

@tool
def search_carbon_news(query: str, k: int = 5) -> str:
    """Search carbon/ESG news articles using RAG. Returns relevant news about sustainability, carbon markets, ESG trends.
    
    Args:
        query: Search query (e.g., 'carbon credit trends', 'Tesla ESG news')
        k: Number of results (default 5)
    
    Returns:
        Relevant news with titles, sources, links, and content
    """
    if not NEWS_RAG_AVAILABLE:
        return "News RAG is unavailable."
    
    try:
        results = search_news(query, k=k)
        if not results:
            return "No news articles found."
        
        output = []
        for i, chunk in enumerate(results, 1):
            output.append(f"\n--- News {i} ---")
            output.append(f"Title: {chunk['title']}")
            output.append(f"Source: {chunk['source']}")
            output.append(f"Link: {chunk['link']}")
            output.append(f"Published: {chunk['published']}")
            output.append(f"Content: {chunk['content'][:300]}...")
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        return f"Error: {str(e)}"

@tool
def search_carbon_projects(query: str, k: int = 5) -> str:
    """Search carbon credit projects using RAG. Returns projects about renewable energy, REDD+, carbon offsets.
    
    Args:
        query: Search query (e.g., 'wind energy projects', 'REDD+ Brazil')
        k: Number of results (default 5)
    
    Returns:
        Relevant projects with names, registries, countries, types
    """
    if not PROJECTS_RAG_AVAILABLE:
        return "Projects RAG is unavailable."
    
    try:
        results = search_projects(query, k=k)
        if not results:
            return "No projects found."
        
        output = []
        for i, chunk in enumerate(results, 1):
            output.append(f"\n--- Project {i} ---")
            output.append(f"Name: {chunk['name']}")
            output.append(f"Registry: {chunk['registry']}")
            output.append(f"Country: {chunk['country']}")
            output.append(f"Type: {chunk['type']}")
            output.append(f"Link: {chunk['registry_link']}")
            output.append(f"Content: {chunk['content'][:300]}...")
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        return f"Error: {str(e)}"

@tool
def get_detailed_company_info(ticker: str) -> str:
    """Get comprehensive company details including stock price, ESG rating, GII score, industry, description.
    
    Args:
        ticker: Company ticker (e.g., 'TSLA', 'AAPL')
    
    Returns:
        Detailed company information
    """
    if not _company_service:
        return "Company service unavailable."
    
    try:
        result = _company_service.get_company_details(ticker)
        if not result.get('success'):
            return f"Company {ticker} not found."
        
        comp = result['data']
        info = f"""
Company: {comp.get('name', '')}
Ticker: {comp.get('ticker', '')}
Industry: {comp.get('industry', '')}
Stock Price: ${comp.get('stock_price', 0)}
Market Cap: {comp.get('market_cap', 'N/A')}
ESG Rating: {comp.get('esg_rating', 'N/A')}
Green Innovation Index: {comp.get('gii_score', 0)}/100
Description: {comp.get('description', '')}
Website: {comp.get('website', '')}
"""
        return info.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_company_insights(ticker: str) -> str:
    """Get AI-powered insights about a company's sustainability, ESG performance, and market position.
    
    Args:
        ticker: Company ticker (e.g., 'TSLA', 'AAPL')
    
    Returns:
        AI-generated insights and analysis
    """
    if not _company_service:
        return "Company service unavailable."
    
    try:
        result = _company_service.get_company_insights(ticker)
        if not result.get('success'):
            return f"Insights for {ticker} unavailable."
        
        data = result['data']
        insights = data.get('insights', 'No insights available')
        return f"Insights for {data.get('company_name')}:\n{insights}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_company_future_impact(ticker: str) -> str:
    """Get comprehensive future impact analysis using AI agent with news, projects, and internet search.
    
    Args:
        ticker: Company ticker (e.g., 'TSLA', 'AAPL')
    
    Returns:
        Detailed future impact analysis
    """
    if not _company_service:
        return "Company service unavailable."
    
    try:
        result = _company_service.get_future_impact_analysis(ticker)
        if not result.get('success'):
            return f"Future impact analysis for {ticker} unavailable."
        
        data = result['data']
        analysis = data.get('analysis', 'No analysis available')
        return f"Future Impact for {data.get('company_name')}:\n{analysis}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_project_details(project_id: str) -> str:
    """Get carbon project details including name, country, methodology, credits, price.
    
    Args:
        project_id: Project ID
    
    Returns:
        Project details
    """
    if not _project_service:
        return "Project service unavailable."
    
    try:
        result = _project_service.get_project_details(project_id)
        if not result.get('success'):
            return f"Project {project_id} not found."
        
        proj = result['data']
        info = f"""
Project: {proj.get('name', '')}
Country: {proj.get('country', 'N/A')}
Category: {proj.get('category', 'N/A')}
Methodology: {proj.get('methodology', 'N/A')}
Available Credits: {proj.get('available_credits', 0)}
Price: ${proj.get('price', 0)}
Status: {proj.get('registry_status', 'N/A')}
Description: {proj.get('description', 'N/A')}
"""
        return info.strip()
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_project_report(project_id: str) -> str:
    """Get AI-generated comprehensive report for a carbon project.
    
    Args:
        project_id: Project ID
    
    Returns:
        AI-generated project report
    """
    if not _project_service:
        return "Project service unavailable."
    
    try:
        result = _project_service.generate_project_report(project_id)
        if not result.get('success'):
            return f"Report for project {project_id} unavailable."
        
        data = result['data']
        report = data.get('report', 'No report available')
        return f"Project Report for {data.get('project_name')}:\n{report}"
    except Exception as e:
        return f"Error: {str(e)}"

# List of all tools
tools = [
    # Navigation & UI
    change_theme, 
    go_to_company, 
    go_to_projects,
    # Watchlist
    add_to_watchlist, 
    remove_from_watchlist,
    # Basic Info
    list_available_companies,
    get_company_info,
    # Advanced Company Analysis
    get_detailed_company_info,
    get_company_insights,
    get_company_future_impact,
    # Project Tools
    get_project_details,
    get_project_report,
    # RAG Search
    search_carbon_news,
    search_carbon_projects
]

# ============================================================================
# INITIALIZE AGENT
# ============================================================================

agent = None

# System prompt for the agent
SYSTEM_PROMPT = """You are EcoInvest AI, a comprehensive assistant guiding users through EcoInvest - a Carbon Intelligence & ESG Investment Platform.

🌱 YOUR ROLE:
You're an expert guide helping users navigate sustainability investments, ESG analysis, carbon markets, and green projects. You have access to powerful tools for deep research and analysis.

🛠️ YOUR COMPREHENSIVE CAPABILITIES:

**Company Analysis (Multiple Levels):**
- get_company_info / get_detailed_company_info - Basic stock, ESG, GII data
- get_company_insights - AI-powered sustainability insights
- get_company_future_impact - Comprehensive future impact analysis using multi-tool AI agent
- list_available_companies - See all companies in database

**Carbon Projects:**
- get_project_details - Project info (country, methodology, credits, price)
- get_project_report - AI-generated comprehensive project reports

**RAG-Powered Search (Real Data):**
- search_carbon_news - Search latest ESG/carbon/sustainability news articles with sources
- search_carbon_projects - Search carbon offset projects (renewable energy, REDD+, etc.)

**Platform Navigation:**
- go_to_company - Navigate to company detail pages
- go_to_projects - Go to carbon projects page
- change_theme - Toggle light/dark mode

**Watchlist:**
- add_to_watchlist / remove_from_watchlist - Manage user's company watchlist

💡 HOW TO ASSIST:
- **Be proactive** - Guide users through the platform and suggest relevant tools
- **Use tools intelligently** - For company questions, start with basic info, then use insights/future impact for deeper analysis
- **Search first** - When asked about news/trends/projects, USE search_carbon_news and search_carbon_projects
- **Be conversational** - Friendly, helpful tone. Explain ESG/carbon concepts simply
- **Provide context** - Don't just dump tool output - interpret and summarize key points
- **Offer next steps** - Suggest relevant actions ("Want me to add them to your watchlist?" or "Should I pull up their future impact analysis?")

🎯 RESPONSE GUIDELINES:
- Keep responses clear and concise (2-4 paragraphs for complex topics)
- Use tools to get real data - don't make things up
- When using RAG tools, summarize the key findings naturally
- Explain technical terms (ESG, GII, carbon credits, REDD+) when needed
- Minimal emojis (1-2 max per response)

🚫 AVOID:
- Raw JSON or unformatted tool outputs
- Overly technical jargon without explanation
- Making up data when tools don't return results
- Being robotic or formal

You're the comprehensive guide to sustainable investing - help users discover, analyze, and understand green investments!"""

try:
    # Get shared LLM instance from centralized manager
    model = get_llm()
    
    if not model:
        logger.error("❌ LLM not available - agent cannot be created")
        raise Exception("LLM initialization failed")
    
    # Message limit middleware - trim to most recent 10 messages
    @before_agent
    def message_limit_middleware(state, config):
        messages = state.get("messages", [])
        # Keep only the most recent 10 messages
        if len(messages) > 10:
            state["messages"] = messages[-10:]
            logger.info(f"🔄 Trimmed conversation to 10 most recent messages")
        return state
    
    # Create agent using modern create_agent API with memory support
    # MemorySaver provides conversation persistence across requests
    # This provides a production-ready agent implementation with ReAct loop
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
        middleware=[message_limit_middleware]
    )
    
    logger.info("✅ AI Chat agent initialized with 10-message limit and comprehensive tools (Gemini 2.5 Flash)")
except Exception as e:
    logger.error(f"❌ Failed to initialize AI chat agent: {e}")
    import traceback
    traceback.print_exc()
    agent = None

# ============================================================================
# API ENDPOINT
# ============================================================================

@aibot_bp.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint using LangChain agent with Gemini and tool calling."""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        logger.info(f"💬 Received message: {user_message}")
        
        # Check if agent is available
        if agent is None:
            logger.warning("⚠️ AI agent not initialized")
            return jsonify({
                'success': False,
                'error': 'AI service not available. Check Gemini API configuration.',
                'response': "Sorry, the AI service is currently unavailable. Please check the Gemini API configuration."
            }), 503
        
        # Invoke the agent using the modern API with memory support
        # The checkpointer automatically handles conversation history per thread_id
        # The agent follows the ReAct pattern and uses tools as needed
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            {"configurable": {"thread_id": session_id}}
        )
        
        # Extract the final response from the agent's message sequence
        # The last message in the result should be the agent's final response
        final_messages = result.get("messages", [])
        if final_messages:
            # Get the last message content
            last_message = final_messages[-1]
            if hasattr(last_message, 'content'):
                bot_response = last_message.content
            elif isinstance(last_message, dict):
                bot_response = last_message.get('content', "I've processed your request.")
            else:
                bot_response = str(last_message)
        else:
            bot_response = "I've processed your request."
        
        # Keep chat history for client-side display (memory is handled by checkpointer)
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        chat_histories[session_id].append({"role": "user", "content": user_message})
        chat_histories[session_id].append({"role": "assistant", "content": bot_response})
        
        # Keep last 20 messages (10 exchanges) for display purposes
        if len(chat_histories[session_id]) > 20:
            chat_histories[session_id] = chat_histories[session_id][-20:]
        
        logger.info(f"🤖 Responding: {bot_response}")
        
        return jsonify({
            'success': True,
            'response': bot_response
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        quota_hit = "quota" in error_msg.lower()
        friendly = "Gemini quota exceeded. Please add billing or try again in a minute." if quota_hit else "Sorry, I encountered an error. Please try again."
        status_code = 429 if quota_hit else 500
        return jsonify({
            'success': False,
            'error': friendly,
            'response': friendly
        }), status_code
