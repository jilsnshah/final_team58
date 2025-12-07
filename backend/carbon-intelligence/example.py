#!/usr/bin/env python3
"""
Carbon Intelligence Platform - Example Client
==============================================
This demonstrates how to use the Carbon Intelligence microservice APIs.

Usage:
    python example_client.py
"""

import grpc
import sys
import os
from datetime import datetime

# Add server directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

import carbon_service_pb2
import carbon_service_pb2_grpc


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_project(project, index):
    """Print a carbon project in a nicely formatted way"""
    print(f"\n📊 Project #{index}")
    print(f"   ID:              {project.project_id}")
    print(f"   Name:            {project.project_name}")
    print(f"   Country:         {project.country}")
    print(f"   Registry Status: {project.registry_status}")
    print(f"   Vintage:         {project.vintage}")
    print(f"   Supply:          {project.supply:,.2f} credits")


def print_news(news, index):
    """Print a news item in a nicely formatted way"""
    print(f"\n📰 News #{index}")
    print(f"   GUID:      {news.guid}")
    print(f"   Title:     {news.title}")
    print(f"   Source:    {news.source}")
    print(f"   Published: {news.published}")
    if news.link:
        print(f"   Link:      {news.link[:60]}...")
    if news.summary:
        summary = news.summary[:150].replace('\n', ' ')
        print(f"   Summary:   {summary}...")


def get_all_projects(stub):
    """Get all carbon projects without filters"""
    print_header("ALL CARBON PROJECTS")
    
    request = carbon_service_pb2.ProjectQuery()
    
    try:
        response = stub.GetProjects(request)
        
        if response.items:
            print(f"\n✅ Found {len(response.items)} projects")
            for i, project in enumerate(response.items[:5], 1):  # Show first 5
                print_project(project, i)
            
            if len(response.items) > 5:
                print(f"\n   ... and {len(response.items) - 5} more projects")
        else:
            print("\n⚠️  No projects found")
            
        return len(response.items)
    
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.code()} - {e.details()}")
        return 0


def get_projects_by_country(stub, country):
    """Get carbon projects filtered by country"""
    print_header(f"PROJECTS IN {country.upper()}")
    
    request = carbon_service_pb2.ProjectQuery(country=country)
    
    try:
        response = stub.GetProjects(request)
        
        if response.items:
            print(f"\n✅ Found {len(response.items)} projects in {country}")
            for i, project in enumerate(response.items[:3], 1):  # Show first 3
                print_project(project, i)
            
            if len(response.items) > 3:
                print(f"\n   ... and {len(response.items) - 3} more projects")
        else:
            print(f"\n⚠️  No projects found in {country}")
            
        return len(response.items)
    
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.code()} - {e.details()}")
        return 0


def get_all_news(stub):
    """Get all carbon news without filters"""
    print_header("ALL CARBON NEWS")
    
    request = carbon_service_pb2.NewsQuery()
    
    try:
        response = stub.GetNews(request)
        
        if response.items:
            print(f"\n✅ Found {len(response.items)} news items")
            for i, news in enumerate(response.items[:5], 1):  # Show first 5
                print_news(news, i)
            
            if len(response.items) > 5:
                print(f"\n   ... and {len(response.items) - 5} more news items")
        else:
            print("\n⚠️  No news found")
            
        return len(response.items)
    
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.code()} - {e.details()}")
        return 0


def get_news_by_source(stub, source):
    """Get news filtered by source"""
    print_header(f"NEWS FROM: {source.upper()}")
    
    request = carbon_service_pb2.NewsQuery(source=source)
    
    try:
        response = stub.GetNews(request)
        
        if response.items:
            print(f"\n✅ Found {len(response.items)} news items from {source}")
            for i, news in enumerate(response.items[:3], 1):
                print_news(news, i)
            
            if len(response.items) > 3:
                print(f"\n   ... and {len(response.items) - 3} more news items")
        else:
            print(f"\n⚠️  No news found from {source}")
            
        return len(response.items)
    
    except grpc.RpcError as e:
        print(f"\n❌ Error: {e.code()} - {e.details()}")
        return 0


def run_example_client():
    """Main function to demonstrate all API capabilities"""
    
    # Connect to the gRPC server
    SERVER_ADDRESS = 'localhost:50051'
    
    print("\n" + "🌱" * 35)
    print("  CARBON INTELLIGENCE PLATFORM - API CLIENT EXAMPLE")
    print("🌱" * 35)
    print(f"\n📡 Connecting to gRPC server at {SERVER_ADDRESS}...")
    
    try:
        # Create a gRPC channel
        channel = grpc.insecure_channel(SERVER_ADDRESS)
        stub = carbon_service_pb2_grpc.CarbonServiceStub(channel)
        
        print("✅ Connected successfully!\n")
        
        # Test connection
        try:
            stub.GetProjects(carbon_service_pb2.ProjectQuery(), timeout=5)
            print("✅ Server is responding\n")
        except grpc.RpcError as e:
            print(f"⚠️  Warning: {e.details()}\n")
        
        # Statistics
        stats = {
            'total_projects': 0,
            'total_news': 0,
            'projects_by_country': {},
            'news_by_source': {}
        }
        
        # ============================================================
        # DEMONSTRATION: GetProjects API
        # ============================================================
        
        # 1. Get all projects
        stats['total_projects'] = get_all_projects(stub)
        
        # 2. Get projects by country
        for country in ['Brazil', 'India', 'Kenya', 'USA']:
            count = get_projects_by_country(stub, country)
            if count > 0:
                stats['projects_by_country'][country] = count
        
        # ============================================================
        # DEMONSTRATION: GetNews API
        # ============================================================
        
        # 1. Get all news
        stats['total_news'] = get_all_news(stub)
        
        # 2. Get news by source
        for source in ['Reuters', 'Bloomberg', 'The Guardian', 'BBC']:
            count = get_news_by_source(stub, source)
            if count > 0:
                stats['news_by_source'][source] = count
        
        # ============================================================
        # SUMMARY STATISTICS
        # ============================================================
        
        print_header("SUMMARY STATISTICS")
        print(f"\n📊 Total Projects:     {stats['total_projects']}")
        print(f"📰 Total News Items:   {stats['total_news']}")
        
        if stats['projects_by_country']:
            print(f"\n🌍 Projects by Country:")
            for country, count in stats['projects_by_country'].items():
                print(f"   • {country:15} {count:3} projects")
        
        if stats['news_by_source']:
            print(f"\n📡 News by Source:")
            for source, count in stats['news_by_source'].items():
                print(f"   • {source:15} {count:3} articles")
        
        # ============================================================
        # USAGE EXAMPLES
        # ============================================================
        
        print_header("HOW TO USE THIS MICROSERVICE")
        
        print("""
🔧 INTEGRATION GUIDE:

1. **Import the gRPC client libraries:**
   ```python
   import grpc
   import carbon_service_pb2
   import carbon_service_pb2_grpc
   ```

2. **Connect to the server:**
   ```python
   channel = grpc.insecure_channel('localhost:50051')
   stub = carbon_service_pb2_grpc.CarbonServiceStub(channel)
   ```

3. **Query carbon projects:**
   ```python
   # Get all projects
   response = stub.GetProjects(carbon_service_pb2.ProjectQuery())
   
   # Filter by country
   response = stub.GetProjects(
       carbon_service_pb2.ProjectQuery(country="Brazil")
   )
   
   # Access project data
   for project in response.items:
       print(f"Project: {project.project_name}")
       print(f"Country: {project.country}")
       print(f"Supply: {project.supply} credits")
   ```

4. **Query carbon news:**
   ```python
   # Get all news
   response = stub.GetNews(carbon_service_pb2.NewsQuery())
   
   # Filter by source
   response = stub.GetNews(
       carbon_service_pb2.NewsQuery(source="Reuters")
   )
   
   # Access news data
   for news in response.items:
       print(f"Title: {news.title}")
       print(f"Source: {news.source}")
       print(f"Link: {news.link}")
   ```

5. **Error handling:**
   ```python
   try:
       response = stub.GetProjects(request, timeout=10)
   except grpc.RpcError as e:
       print(f"Error: {e.code()} - {e.details()}")
   ```

📦 AVAILABLE ENDPOINTS:
   • GetProjects - Query carbon offset projects
   • GetNews     - Query carbon-related news
   • GetFinanceData - Query carbon-related finance data

🔍 AVAILABLE FILTERS:
   Projects:
   • country       - Filter by country name
   
   News:
   • source        - Filter by news source

🚀 DEPLOYMENT OPTIONS:
   • Local:        localhost:50051
   • Docker:       carbon_pathway:50051 (internal)
   • Production:   <your-domain>:50051

💾 DATA SOURCES:
   • Verra Registry (carbon offset projects)
   • Carbonmark (project marketplace data)
   • Finance data (47 carbon-related stocks)
   • News feeds (16 carbon keywords tracked)
""")
        
        print("\n" + "=" * 70)
        print("✅ Example client completed successfully!")
        print("=" * 70 + "\n")
        
        # Close the channel
        channel.close()
        
    except grpc.RpcError as e:
        print(f"\n❌ gRPC Error: {e.code()} - {e.details()}")
        print("\n💡 Make sure the gRPC server is running:")
        print("   docker-compose up -d")
        print("   or")
        print("   cd server && python grpc_server.py")
        return 1
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def main():
    """Run the main example client with additional demonstrations"""
    result = run_example_client()
    
    if result != 0:
        return result
    
    # Connect to the gRPC server
    SERVER_ADDRESS = 'localhost:50051'
    
    try:
        channel = grpc.insecure_channel(SERVER_ADDRESS)
        stub = carbon_service_pb2_grpc.CarbonServiceStub(channel)
        
        # Example 3: Get Finance Data (Streaming)
        print("\n" + "="*50)
        print("Example 3: Get All Finance Data (STREAMING)")
        print("="*50)
        
        finance_response = stub.GetFinanceData(carbon_service_pb2.FinanceQuery())
        print(f"Found {finance_response.count} finance records")
        
        for item in finance_response.items[:5]:
            print(f"\nTicker: {item.ticker}")
            print(f"  Price: ${item.price:.2f}")
            print(f"  Volume: {item.volume:,}")
            print(f"  Market Cap: ${item.market_cap:,.0f}")
            print(f"  Change: {item.change_percent:+.2f}%")
        
        # Example 4: Get Finance Data for specific ticker (Streaming)
        print("\n" + "="*50)
        print("Example 4: Get Finance Data for KRBN (STREAMING)")
        print("="*50)
        
        krbn_response = stub.GetFinanceData(carbon_service_pb2.FinanceQuery(ticker="KRBN"))
        print(f"Found {krbn_response.count} records for KRBN")
        
        if krbn_response.items:
            item = krbn_response.items[0]
            print(f"\nKRBN Latest Data:")
            print(f"  Price: ${item.price:.2f}")
            print(f"  Change: {item.change_percent:+.2f}%")
        
        # Example 5: Get Project Detail
        print("\n" + "="*50)
        print("Example 5: Get Project Detail (STREAMING)")
        print("="*50)
        
        projects_response = stub.GetProjects(carbon_service_pb2.ProjectQuery())
        if projects_response.items:
            project_id = projects_response.items[0].project_id
            print(f"Getting details for project: {project_id}")
            
            detail_response = stub.GetProjectDetail(carbon_service_pb2.ProjectDetailQuery(project_id=project_id))
            if detail_response.project.project_id:
                proj = detail_response.project
                print(f"\nProject: {proj.project_name}")
                print(f"ID: {proj.project_id}")
                print(f"Status: {proj.registry_status}")
                print(f"Country: {proj.country}")
                print(f"Summary: {proj.project_summary[:100]}...")
                print(f"Link: {proj.project_link}")
                print(f"Source: {proj.source}")
        
        # ============================================================
        # NON-STREAMING ENDPOINTS - Direct SQL Queries
        # ============================================================
        
        # Example 6: Get Projects (Non-Streaming)
        print("\n" + "="*70)
        print("Example 6: Get All Projects (NON-STREAMING - Direct SQL)")
        print("="*70)
        
        ns_projects = stub.GetNonStreamingProjects(carbon_service_pb2.ProjectQuery())
        print(f"✅ Found {len(ns_projects.items)} projects from database")
        
        for i, project in enumerate(ns_projects.items[:3], 1):
            print(f"\n📊 Project #{i}")
            print(f"   ID:      {project.project_id}")
            print(f"   Name:    {project.project_name}")
            print(f"   Country: {project.country}")
            print(f"   Supply:  {project.supply:,.2f} credits")
        
        if len(ns_projects.items) > 3:
            print(f"\n   ... and {len(ns_projects.items) - 3} more projects")
        
        # Example 7: Get Projects by Country (Non-Streaming)
        print("\n" + "="*70)
        print("Example 7: Get Brazil Projects (NON-STREAMING - Direct SQL)")
        print("="*70)
        
        ns_brazil = stub.GetNonStreamingProjects(
            carbon_service_pb2.ProjectQuery(country="Brazil")
        )
        print(f"✅ Found {len(ns_brazil.items)} projects in Brazil")
        
        for i, project in enumerate(ns_brazil.items[:2], 1):
            print(f"\n📊 Project #{i}")
            print(f"   ID:      {project.project_id}")
            print(f"   Name:    {project.project_name}")
            print(f"   Vintage: {project.vintage}")
        
        # Example 8: Get News (Non-Streaming)
        print("\n" + "="*70)
        print("Example 8: Get All News (NON-STREAMING - Direct SQL)")
        print("="*70)
        
        ns_news = stub.GetNonStreamingNews(carbon_service_pb2.NewsQuery())
        print(f"✅ Found {len(ns_news.items)} news items from database")
        
        for i, news in enumerate(ns_news.items[:3], 1):
            print(f"\n📰 News #{i}")
            print(f"   Title:  {news.title[:60]}...")
            print(f"   Source: {news.source}")
        
        if len(ns_news.items) > 3:
            print(f"\n   ... and {len(ns_news.items) - 3} more news items")
        
        # Example 9: Get News by Source (Non-Streaming)
        print("\n" + "="*70)
        print("Example 9: Get Reuters News (NON-STREAMING - Direct SQL)")
        print("="*70)
        
        ns_reuters = stub.GetNonStreamingNews(
            carbon_service_pb2.NewsQuery(source="Reuters")
        )
        print(f"✅ Found {len(ns_reuters.items)} Reuters articles")
        
        for i, news in enumerate(ns_reuters.items[:2], 1):
            print(f"\n📰 Article #{i}")
            print(f"   Title: {news.title}")
        
        # Example 10: Get Finance Data (Non-Streaming)
        print("\n" + "="*70)
        print("Example 10: Get Finance Data (NON-STREAMING - Direct SQL)")
        print("="*70)
        
        ns_finance = stub.GetNonStreamingFinanceData(carbon_service_pb2.FinanceQuery())
        print(f"✅ Found {ns_finance.count} finance records from database")
        
        if ns_finance.items:
            for i, item in enumerate(ns_finance.items[:3], 1):
                print(f"\n💰 Record #{i}")
                print(f"   Ticker:     {item.ticker}")
                print(f"   Price:      ${item.price:.2f}")
                print(f"   Change:     {item.change_percent:+.2f}%")
        else:
            print("⚠️  No finance data yet - scrapers are still collecting")
        
        # Summary
        print("\n" + "="*70)
        print("COMPARISON: STREAMING vs NON-STREAMING")
        print("="*70)
        print("""
📊 STREAMING ENDPOINTS (via Pathway):
   • Real-time updates from Kafka CDC stream
   • 2-5 second latency from database changes
   • Optimized for live monitoring
   • Data processed through Pathway pipeline
   
💾 NON-STREAMING ENDPOINTS (Direct SQL):
   • Direct PostgreSQL database access
   • No Pathway processing layer
   • Full historical data available
   • Custom SQL queries possible
   • Lower latency for batch queries

🔧 WHEN TO USE EACH:
   Streaming:     Live dashboards, real-time alerts, event-driven apps
   Non-Streaming: Reports, analytics, batch processing, data exports
        """)
        
        # Close the channel
        channel.close()
        
    except Exception as e:
        print(f"\n⚠️  Additional examples skipped: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    exit(main())
