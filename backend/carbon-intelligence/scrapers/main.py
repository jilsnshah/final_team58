import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
from finance_scraper import run_finance_scraper
from news_scraper import run_news_scraper
from verra_scraper import run_verra_scraper

print("🔥 Scraper service started")

COMPANIES = [
    "KRBN",   
    "KCCA",   
    "GRN",    
    "CLNE",   
    "ENPH",   
    "PLUG",   
    "FCEL",   
    "BLNK",   
    "CHPT",   
    "CWEN",   
    "NEE",    
    "AY",     
    "RUN",    
    "SEDG",   
    "TSLA",   
    "MSFT",   
    "GOOGL",  
    "AAPL",   
    "AMZN",   
    "ORSTED", 
    "EQNR",   
    "IBE",    
    "DNNGY",  
    "VST",    
    "AES",    
    "D",      
    "DUK",    
    "SO",     
    "ICLN",   
    "TAN",    
    "QCLN",   
    "PBW",    
    "ALB",    
    "SQM",    
    "MP",     
    "LAC",    
    "WM",     
    "RSG",    
    "WCN",    
    "BEPC",   
    "BEP",    
    "HASI",   
]

CARBON_KEYWORDS = [
    "carbon credits",
    "carbon offset",
    "carbon trading",
    "carbon market",
    "emissions trading",
    "carbon neutral",
    "net zero",
    "carbon sequestration",
    "carbon capture",
    "CCUS",
    "renewable energy credits",
    "REC",
    "voluntary carbon market",
    "compliance carbon market",
    "carbon allowances",
    "cap and trade",
]

print(f"📊 Tracking {len(COMPANIES)} companies/tickers")
print(f"🔍 Monitoring {len(CARBON_KEYWORDS)} carbon-related keywords")


def get_connection():
    while True:
        try:
            conn = psycopg2.connect(
                dbname="carbon_intel",
                user="carbon",
                password="carbonpw",
                host="postgres",
                port=5432,
            )
            print("✅ Connected to PostgreSQL")
            return conn
        except psycopg2.OperationalError:
            print("⏳ Waiting for PostgreSQL...")
            time.sleep(2)


conn = get_connection()

def run_scraper_task(scraper_name, scraper_func, *args):
    """Run a scraper task with error handling"""
    try:
        print(f"📌 Running {scraper_name} scraper...")
        scraper_func(*args)
        print(f"✅ {scraper_name} scraper completed")
        return True
    except Exception as e:
        print(f"❌ {scraper_name} scraper error: {e}")
        return False

while True:
    try:
        print("\n" + "="*60)
        print("🚀 Starting parallel scraper run...")
        print("="*60)
        
        # Create separate connections for each thread to avoid conflicts
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(run_scraper_task, "Verra", run_verra_scraper, None),
                # Carbonmark scraper disabled - using only Verra for projects
                # executor.submit(run_scraper_task, "Carbonmark", run_carbonmark_scraper, None),
                executor.submit(run_scraper_task, "Finance", run_finance_scraper, None, COMPANIES),
                executor.submit(run_scraper_task, "News", run_news_scraper, CARBON_KEYWORDS, COMPANIES, None)
            ]
            
            # Wait for all to complete
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                if result:
                    completed += 1
        
        print("\n" + "="*60)
        print(f"✨ Scraper cycle complete: {completed}/3 successful")
        print("⏳ Sleeping for 120 seconds (2 minutes)...")
        print("="*60 + "\n")
        time.sleep(120)  # Run every 2 minutes instead of 5

    except Exception as e:
        print(f"❌ Main loop error: {e}")
        time.sleep(30)
