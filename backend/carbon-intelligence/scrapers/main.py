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
    "RELIANCE.NS",
    "TCS.NS",
    "TATAPOWER.NS",
    "ADANIGREEN.NS",
    "JSWENERGY.NS"
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

def run_continuous_scraper(scraper_name, scraper_func, interval_seconds, *args):
    """Run a scraper task continuously in its own isolated thread."""
    print(f"🚀 Starting continuous loop for {scraper_name} scraper (interval: {interval_seconds}s)")
    while True:
        try:
            print(f"📌 [START] {scraper_name} scraper...")
            scraper_func(*args)
            print(f"✅ [DONE] {scraper_name} scraper. Sleeping for {interval_seconds}s...")
        except Exception as e:
            print(f"❌ [ERROR] {scraper_name} scraper failed: {e}. Sleeping for {interval_seconds}s...")
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting independent scraper microservices...")
    print("="*60)
    
    threads = []
    
    # 1. News Scraper: Runs every 10 seconds (Extremely fast, highly concurrent)
    t_news = threading.Thread(
        target=run_continuous_scraper, 
        args=("News", run_news_scraper, 10, CARBON_KEYWORDS, COMPANIES, None),
        daemon=True
    )
    threads.append(t_news)
    
    # 2. Finance Scraper: Unpaused & Optimized
    t_finance = threading.Thread(
        target=run_continuous_scraper, 
        args=("Finance", run_finance_scraper, 10, None, COMPANIES),
        daemon=True
    )
    threads.append(t_finance)
    
    # 3. Verra Scraper: Temporarily Paused
    # t_verra = threading.Thread(
    #     target=run_continuous_scraper, 
    #     args=("Verra", run_verra_scraper, 60, None),
    #     daemon=True
    # )
    # threads.append(t_verra)
    
    # Start all independent threads
    for t in threads:
        t.start()
        
    # Keep the main process alive forever
    while True:
        time.sleep(3600)
