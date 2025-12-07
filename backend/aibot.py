"""
AI Chatbot Service - LangChain Agent with Tool Calling

A LangChain agent that can call tools to perform frontend actions using Google Gemini.
"""

from flask import Blueprint, request, jsonify
import logging
import os
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import frontend_actions

# Import News RAG service
try:
    from services.news_rag_service import get_news_rag_service, search_news
    NEWS_RAG_AVAILABLE = True
except ImportError:
    NEWS_RAG_AVAILABLE = False
    print("⚠️ News RAG service not available")

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
def search_carbon_news(query: str) -> str:
    """Search for the latest carbon credit, ESG, and sustainability news articles.
    
    Use this tool when users ask about:
    - Recent news about carbon credits, ESG, or sustainability
    - What's happening in the carbon market
    - Latest developments in green investing
    - News about specific companies' ESG initiatives
    - Climate policy updates
    
    Args:
        query: The search query (e.g., 'carbon credit trends', 'Tesla ESG news', 'EU carbon market')
    
    Returns:
        Relevant news summaries with sources
    """
    if not NEWS_RAG_AVAILABLE:
        return "News search is currently unavailable. The RAG service is not initialized."
    
    try:
        results = search_news(query, k=5)
        
        if not results.get('found') or not results.get('sources'):
            return f"I couldn't find any recent news about '{query}'. Try a different search term."
        
        # Format the response
        response_parts = [f"Here's what I found about '{query}':\n"]
        
        for i, source in enumerate(results['sources'][:5], 1):
            title = source.get('title', 'Untitled')
            news_source = source.get('source', 'Unknown')
            published = source.get('published', '')
            sentiment = source.get('sentiment', 'Neutral')
            
            # Format date if available
            date_str = published[:16] if published else 'Recent'
            
            response_parts.append(f"{i}. **{title}**")
            response_parts.append(f"   Source: {news_source} | {date_str} | Sentiment: {sentiment}\n")
        
        # Add context summary
        if results.get('context'):
            context = results['context'][:800]  # Limit context length
            response_parts.append(f"\n📝 Summary:\n{context}")
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        return f"Error searching news: {str(e)}"

# List of all tools
tools = [change_theme, get_company_info, list_available_companies, add_to_watchlist, remove_from_watchlist, go_to_company, go_to_projects, search_carbon_news]

# ============================================================================
# INITIALIZE LLM AND AGENT
# ============================================================================

agent = None

# System prompt for the agent
SYSTEM_PROMPT = """You are EcoInvest AI, a friendly and knowledgeable assistant for EcoInvest - a Carbon Intelligence & ESG Investment Platform.

🌱 ABOUT THE PLATFORM:
EcoInvest helps users track sustainable investments, monitor ESG (Environmental, Social, Governance) ratings, and explore carbon credit projects. You're here to help users navigate the platform and answer questions about companies and sustainability.

🛠️ YOUR CAPABILITIES:
1. **Company Information** - Use get_company_info to answer questions about any company's stock price, ESG rating, sustainability initiatives, GII score, and more.
2. **List Companies** - Use list_available_companies to show what companies are in the database.
3. **News Search** - Use search_carbon_news to find the latest news about carbon credits, ESG, sustainability, and green investing. Always use this for news-related questions!
4. **Watchlist Management** - Add or remove companies from the user's watchlist.
5. **Navigation** - Help users navigate to company pages or the carbon projects page.
6. **Theme Toggle** - Switch between light and dark mode.

💬 HOW TO RESPOND:
- Be warm, helpful, and conversational - like a knowledgeable friend!
- When asked about a company, USE the get_company_info tool first, then summarize the key info naturally.
- When asked about news, trends, or recent developments, USE the search_carbon_news tool to get real information.
- Keep responses concise but informative.
- Use emojis sparingly to be friendly (1-2 per message max).
- If users ask about ESG, sustainability, or carbon credits, explain in simple terms.

🚫 NEVER DO:
- Show raw JSON, technical data, or tool outputs directly.
- Be robotic or overly formal.
- Make up information - if you don't have data, say so politely.

✨ EXAMPLE RESPONSES:
- "Tesla's doing great! Stock is at $248.50 with an A+ ESG rating. They're really leading in sustainability. Want me to add them to your watchlist?"
- "Done! I've switched to dark mode for you. 🌙"
- "Here are the companies I can tell you about: [list]. Which one interests you?"

Remember: You're the friendly guide to sustainable investing!"""

try:
    # Initialize LLM with Google Gemini
    # Using gemini-2.5-flash for better reasoning and tool calling
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        temperature=0.7,
        max_output_tokens=1024,
    )
    
    # Create prompt template for the agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent using the LangChain API
    agent_runnable = create_tool_calling_agent(llm, tools, prompt)
    agent = AgentExecutor(agent=agent_runnable, tools=tools, verbose=True)
    
    logger.info("✅ AI Chat agent initialized successfully (Gemini Pro)")
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
        
        # Get or create chat history
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        chat_history = chat_histories[session_id]
        
        # Build chat history for the agent
        history_messages = []
        for msg in chat_history[-6:]:  # Last 3 exchanges
            history_messages.append((msg["role"], msg["content"]))
        
        # Invoke the agent with the new format
        result = agent.invoke({
            "input": user_message,
            "chat_history": history_messages
        })
        
        # Get the response from the result
        bot_response = result.get("output", "I've processed your request.")
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_response})
        
        # Keep last 10 messages (5 exchanges)
        if len(chat_history) > 10:
            chat_histories[session_id] = chat_history[-10:]
        
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
