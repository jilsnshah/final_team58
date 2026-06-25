import json
import re
import random
import uuid
from datetime import datetime

import psycopg2
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_session_with_retries():
    """Create requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def extract_next_data(html):
    """Extract __NEXT_DATA__ JSON from Next.js page"""
    try:
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
            html,
            re.DOTALL,
        )
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
    except Exception as e:
        print(f"❌ Failed to extract NEXT_DATA: {e}")
    return None


def fetch_sanity_projects(session):
    """Fetch projects from Sanity CMS (Carbonmark's content backend)"""
    projects = []

    sanity_query = """
    *[_type == "project"] {
        _id,
        key,
        projectID,
        name,
        description,
        country,
        region,
        "price": pricing[0].price,
        registry,
        "methodologies": methodologies[]->{
            id,
            category,
            name,
            sector
        },
        "vintages": vintages,
        "stats": {
            "totalBridged": stats.totalBridged,
            "totalRetired": stats.totalRetired,
            "totalSupply": stats.totalSupply
        },
        "sdgs": sustainableDevelopmentGoals
    } | order(_createdAt desc)
    """

    try:
        encoded_query = " ".join(sanity_query.split())

        SANITY_API = "https://l6of5nwi.api.sanity.io/v2021-06-07/data/query/production"
        params = {"query": encoded_query}

        print("📡 Fetching from Sanity CMS...")
        response = session.get(SANITY_API, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            print(f"❌ Sanity query error: {data['error']['description']}")
            return []

        projects = data.get("result", [])
        print(f"✅ Got {len(projects)} projects from Sanity")

    except Exception as e:
        print(f"❌ Sanity fetch failed: {e}")

    return projects


def scrape_projects_page(session):
    """Fallback: Scrape projects from the Carbonmark website"""
    projects = []

    try:
        print("📡 Scraping Carbonmark website...")
        url = "https://app.carbonmark.com/projects"

        response = session.get(url, timeout=30)
        response.raise_for_status()

        next_data = extract_next_data(response.text)

        if next_data:
            page_props = next_data.get("props", {}).get("pageProps", {})
            page_projects = (
                page_props.get("projects", [])
                or page_props.get("data", {}).get("projects", [])
                or page_props.get("initialData", {}).get("projects", [])
            )
            projects.extend(page_projects)
            print(f"✅ Got {len(page_projects)} projects from website")

    except Exception as e:
        print(f"❌ Website scrape failed: {e}")

    return projects


def run_carbonmark_scraper(conn=None):
    """Scrape carbon credits from Carbonmark via Sanity CMS"""
    
    # Create connection if not provided
    own_conn = False
    if conn is None:
        conn = psycopg2.connect(
            dbname="carbon_intel",
            user="carbon",
            password="carbonpw",
            host="postgres",
            port=5432,
        )
        own_conn = True
    
    cur = conn.cursor()
    
    print("📡 Starting Carbonmark scraper (Sanity CMS)...")
    
    session = get_session_with_retries()
    
    # Try Sanity CMS first (primary source)
    projects = fetch_sanity_projects(session)
    
    # Fallback to website scraping if Sanity fails
    if not projects:
        print("⚠️  Sanity CMS failed, trying website scraping...")
        projects = scrape_projects_page(session)
    
    if not projects:
        print("❌ No projects found from any source - skipping this run")
        cur.close()
        if own_conn:
            conn.close()
        return
    
    print(f"📊 Processing {len(projects)} Carbonmark projects...")
    
    # Store projects in database
    stored = 0
    for project in projects:
        try:
            project_id = project.get('key') or project.get('projectID') or f'CM-{uuid.uuid4().hex[:8]}'
            project_name = project.get('name', 'Unknown Project')
            description = project.get('description', f'Tokenized carbon credit project: {project_name}')
            
            # Extract data with proper NULL handling
            vintage = None
            if 'vintages' in project and project['vintages'] and len(project['vintages']) > 0:
                try:
                    vintage = int(project['vintages'][0])
                except (ValueError, TypeError):
                    vintage = None
            
            amount = 0.0
            if 'stats' in project and project['stats']:
                stats = project['stats']
                total_supply = stats.get('totalSupply')
                if total_supply is not None:
                    try:
                        amount = float(total_supply)
                    except (ValueError, TypeError):
                        amount = 0.0
            
            project_summary = description[:500] if description else f'Carbon credit project {project_id}'
            project_link = f"https://www.carbonmark.com/projects/{project_id}"
            
            cur.execute('''
                INSERT INTO carbonmark (project_id, project_name, vintage, amount, project_summary, project_link)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id) DO UPDATE SET
                    project_name = EXCLUDED.project_name,
                    vintage = EXCLUDED.vintage,
                    amount = EXCLUDED.amount,
                    project_summary = EXCLUDED.project_summary,
                    updated_at = CURRENT_TIMESTAMP
            ''', (project_id, project_name, vintage, amount, project_summary, project_link))
            
            conn.commit()
            stored += 1
        except Exception as e:
            print(f"⚠️  Error storing project {project.get('name', 'unknown')}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cur.close()
    if own_conn:
        conn.close()
    
    print(f"✅ Carbonmark: Stored {stored}/{len(projects)} projects")


# OLD CODE - TheGraph API deprecated, keeping for reference
# def run_carbonmark_scraper_old():
#     """OLD: Scrape carbon credits from TheGraph API (DEPRECATED - API removed)"""
#     # Code removed - TheGraph endpoint no longer available
