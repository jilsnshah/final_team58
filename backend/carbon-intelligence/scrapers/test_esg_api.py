"""
Test script to verify all APIs used in finance_scraper.py
Tests both price data APIs and ESG rating API
"""

import requests
import json

# Test tickers (same as finance_scraper.py)
TEST_TICKERS = ['TSLA', 'MSFT', 'AAPL']

def test_yahoo_price_api(ticker):
    """Test Yahoo Finance price API (main data source)"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        print(f"\n{'='*60}")
        print(f"Testing Yahoo Price API for: {ticker}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print FULL response
            print(f"\n📄 FULL API RESPONSE:")
            print(json.dumps(data, indent=2))
            
            result = data.get('chart', {}).get('result', [])
            
            if result:
                meta = result[0].get('meta', {})
                price = meta.get('regularMarketPrice')
                prev_close = meta.get('previousClose')
                
                if price and prev_close:
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100
                    
                    print(f"\n✅ PRICE DATA EXTRACTED")
                    print(f"Current Price: ${price:.2f}")
                    print(f"Previous Close: ${prev_close:.2f}")
                    print(f"Change: ${change:+.2f} ({change_pct:+.2f}%)")
                    return True
        
        print(f"❌ Failed to get price data")
        return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_finnhub_api(ticker):
    """Test Finnhub API (backup price source)"""
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token=demo"
        
        print(f"\n{'='*60}")
        print(f"Testing Finnhub API for: {ticker}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print FULL response
            print(f"\n📄 FULL API RESPONSE:")
            print(json.dumps(data, indent=2))
            
            current = data.get('c')
            prev_close = data.get('pc')
            
            if current and prev_close and current > 0:
                change = current - prev_close
                change_pct = (change / prev_close) * 100
                
                print(f"\n✅ PRICE DATA EXTRACTED")
                print(f"Current Price: ${current:.2f}")
                print(f"Previous Close: ${prev_close:.2f}")
                print(f"Change: ${change:+.2f} ({change_pct:+.2f}%)")
                return True
        
        print(f"❌ Failed to get price data")
        return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_esg_api(ticker):
    """Test Yahoo Finance ESG API"""
    try:
        url = f'https://query2.finance.yahoo.com/v1/finance/esgChart?symbol={ticker}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        print(f"\n{'='*60}")
        print(f"Testing ESG API for: {ticker}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print FULL response
            print(f"\n📄 FULL API RESPONSE:")
            print(json.dumps(data, indent=2))
            
            esg_chart = data.get('esgChart', {})
            result = esg_chart.get('result', [])
            
            if result:
                symbol_data = result[0]
                esg_scores = symbol_data.get('esgScores', {})
                total_esg = esg_scores.get('totalEsg')
                
                if total_esg is not None:
                    # Calculate rating (same as finance_scraper.py)
                    if total_esg < 10:
                        rating = 'A+'
                    elif total_esg < 20:
                        rating = 'A'
                    elif total_esg < 30:
                        rating = 'B+'
                    elif total_esg < 40:
                        rating = 'B'
                    else:
                        rating = 'C'
                    
                    print(f"\n✅ ESG DATA EXTRACTED")
                    print(f"Total ESG Score: {total_esg}")
                    print(f"Environment: {esg_scores.get('environmentScore')}")
                    print(f"Social: {esg_scores.get('socialScore')}")
                    print(f"Governance: {esg_scores.get('governanceScore')}")
                    print(f"ESG Rating: {rating}")
                    return True
        
        print(f"❌ No ESG data available")
        return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_ticker(ticker):
    """Test all APIs for a single ticker"""
    print(f"\n{'#'*60}")
    print(f"# TESTING: {ticker}")
    print(f"{'#'*60}")
    
    results = {
        'yahoo_price': test_yahoo_price_api(ticker),
        'finnhub': test_finnhub_api(ticker),
        'esg': test_esg_api(ticker)
    }
    
    return results

def main():
    """Run complete API test suite"""
    print("="*60)
    print("FINANCE SCRAPER API TEST")
    print("Testing all APIs used in finance_scraper.py")
    print("="*60)
    
    all_results = {}
    
    for ticker in TEST_TICKERS:
        all_results[ticker] = test_ticker(ticker)
    
    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    
    for ticker, results in all_results.items():
        print(f"\n{ticker}:")
        print(f"  Yahoo Price API: {'✅ Working' if results['yahoo_price'] else '❌ Failed'}")
        print(f"  Finnhub API:     {'✅ Working' if results['finnhub'] else '❌ Failed'}")
        print(f"  ESG API:         {'✅ Working' if results['esg'] else '❌ Failed'}")
    
    # Overall stats
    print(f"\n{'='*60}")
    yahoo_count = sum(1 for r in all_results.values() if r['yahoo_price'])
    finnhub_count = sum(1 for r in all_results.values() if r['finnhub'])
    esg_count = sum(1 for r in all_results.values() if r['esg'])
    total = len(all_results)
    
    print(f"Yahoo Price API: {yahoo_count}/{total} tickers")
    print(f"Finnhub API:     {finnhub_count}/{total} tickers")
    print(f"ESG API:         {esg_count}/{total} tickers")

if __name__ == "__main__":
    main()
