import time
import random

import psycopg2
import yfinance as yf

conn = psycopg2.connect(
    dbname="carbon_intel",
    user="carbon",
    password="carbonpw",
    host="postgres",
    port=5432,
)
cur = conn.cursor()

# Company metadata matching frontend format
COMPANY_METADATA = {
    "TSLA": {
        "name": "Tesla, Inc.",
        "industry": "Automotive & Energy",
        "description": "Leading electric vehicle manufacturer and clean energy company producing EVs, battery energy storage systems, and solar products.",
        "gii_score": 89,
        "sustainability_update": "Announced plans to power all Gigafactories with 100% renewable energy by 2026.",
        "esg_rating": "A",
        "website": "https://www.tesla.com",
        "market_cap_fallback": 800000000000  # $800B
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "industry": "Technology",
        "description": "Global technology leader providing cloud computing, software, devices, and services.",
        "gii_score": 92,
        "sustainability_update": "Achieved 100% renewable energy in all data centers globally.",
        "esg_rating": "AAA",
        "website": "https://www.microsoft.com",
        "market_cap_fallback": 3000000000000  # $3T
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "industry": "Semiconductors",
        "description": "Pioneer in GPU technology and AI computing platforms.",
        "gii_score": 85,
        "sustainability_update": "Launched Earth-2 climate digital twin initiative.",
        "esg_rating": "A+",
        "website": "https://www.nvidia.com",
        "market_cap_fallback": 1200000000000  # $1.2T
    },
    "AAPL": {
        "name": "Apple Inc.",
        "industry": "Technology",
        "description": "Designer and manufacturer of consumer electronics, software, and online services.",
        "gii_score": 94,
        "sustainability_update": "Launched first carbon-neutral product line with Apple Watch Series 9.",
        "esg_rating": "AAA",
        "website": "https://www.apple.com",
        "market_cap_fallback": 3500000000000  # $3.5T
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "industry": "Technology",
        "description": "Technology conglomerate specializing in internet services and products.",
        "gii_score": 90,
        "sustainability_update": "Operating on 24/7 carbon-free energy in multiple data centers.",
        "esg_rating": "AA+",
        "website": "https://about.google",
        "market_cap_fallback": 2000000000000  # $2T
    },
    "AMZN": {
        "name": "Amazon.com, Inc.",
        "industry": "E-commerce & Cloud",
        "description": "Global e-commerce and cloud computing giant.",
        "gii_score": 82,
        "sustainability_update": "Committed to net-zero carbon by 2040 with 100,000+ electric delivery vehicles.",
        "esg_rating": "A",
        "website": "https://www.amazon.com",
        "market_cap_fallback": 1800000000000  # $1.8T
    },
    "ORCL": {
        "name": "Oracle Corporation",
        "industry": "Technology",
        "description": "Enterprise software and cloud infrastructure provider.",
        "gii_score": 81,
        "sustainability_update": "Surpassed 90% renewable energy across global operations.",
        "esg_rating": "A",
        "website": "https://www.oracle.com",
        "market_cap_fallback": 350000000000  # $350B
    }
}


def run_finance_scraper(tickers):
    """
    Scrape REAL financial data - will wait for proper delays
    
    Args:
        tickers: List of stock ticker symbols to track
    """
    print(f"💰 Fetching REAL data for tickers...")
    print(f"⏳ Using proper delays to get actual market data (2-3 min)")
    
    successful = 0
    failed = 0
    
    # Only important tickers
    priority_tickers = ["TSLA", "MSFT", "NVDA", "AAPL", "GOOGL", "AMZN", "ORCL"]
    
    for idx, ticker_symbol in enumerate(priority_tickers):
        metadata = COMPANY_METADATA.get(ticker_symbol)
        if not metadata:
            continue
        
        print(f"\n📊 [{idx+1}/{len(priority_tickers)}] {ticker_symbol}...")
        
        # CRITICAL: Proper delay to avoid rate limits
        if idx > 0:
            delay = random.uniform(18, 28)
            print(f"   ⏳ Wait {delay:.0f}s...")
            time.sleep(delay)
        
        # Try to get real data
        price = None
        volume = 0
        change_percent = 0.0
        market_cap_value = 0
        
        for attempt in range(2):
            try:
                print(f"   🔄 Try {attempt + 1}/2...")
                ticker = yf.Ticker(ticker_symbol)
                
                # Method 1: info
                try:
                    info = ticker.info
                    if 'regularMarketPrice' in info:
                        price = float(info['regularMarketPrice'])
                        volume = int(info.get('regularMarketVolume', 0))
                        market_cap_value = info.get('marketCap', 0)
                        change_percent = float(info.get('regularMarketChangePercent', 0))
                        print(f"   ✅ ${price:.2f}")
                        break
                except:
                    pass
                
                # Method 2: history
                hist = ticker.history(period="2d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
                    volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist else 0
                    if len(hist) > 1:
                        prev = float(hist["Close"].iloc[-2])
                        change_percent = ((price - prev) / prev) * 100
                    try:
                        if not info:
                            info = ticker.info
                        market_cap_value = info.get("marketCap", 0) if info else 0
                    except:
                        pass
                    print(f"   ✅ ${price:.2f}")
                    break
                    
                if attempt == 0:
                    time.sleep(10)
                    
            except Exception as e:
                print(f"   ⚠️  {str(e)[:50]}")
                if attempt == 0:
                    time.sleep(15)
        
        if price is None:
            print(f"   ❌ Failed")
            failed += 1
            continue
        
        # Use fallback market cap if API didn't provide it
        if not market_cap_value or market_cap_value == 0:
            market_cap_value = metadata.get("market_cap_fallback", 0)
        
        # Format market cap
        if market_cap_value >= 1e12:
            market_cap = f"{market_cap_value / 1e12:.1f}T"
        elif market_cap_value >= 1e9:
            market_cap = f"{market_cap_value / 1e9:.0f}B"
        else:
            market_cap = "N/A"
        
        # Save
        try:
            cur.execute(
                """
                INSERT INTO finance (
                    ticker, company_name, industry, description, gii_score,
                    stock_price, market_cap, sustainability_update, esg_rating,
                    website, price, volume, change_percent, timestamp
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticker) DO UPDATE SET
                    stock_price=EXCLUDED.stock_price,
                    price=EXCLUDED.price,
                    volume=EXCLUDED.volume,
                    market_cap=EXCLUDED.market_cap,
                    change_percent=EXCLUDED.change_percent,
                    timestamp=EXCLUDED.timestamp,
                    updated_at=NOW();
                """,
                (
                    ticker_symbol, metadata["name"], metadata["industry"],
                    metadata["description"], metadata["gii_score"],
                    float(price), market_cap, metadata["sustainability_update"],
                    metadata["esg_rating"], metadata["website"],
                    float(price), volume, float(change_percent), int(time.time())
                ),
            )
            conn.commit()
            successful += 1
            print(f"   ✅ Saved: ${price:.2f}, {change_percent:+.2f}%")
        except Exception as e:
            print(f"   ❌ DB: {e}")
            failed += 1
    
    print(f"\n✅ Done: {successful} OK, {failed} fail")
    return successful, failed
