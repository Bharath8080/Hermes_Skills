import json, sys, yfinance as yf

def get_stock_price(symbol: str) -> dict:
    t = yf.Ticker(symbol.upper())
    info = t.fast_info
    return {
        "symbol": symbol.upper(),
        "price": round(info.last_price, 2),
        "currency": info.currency,
        "market_cap": info.market_cap,
        "day_high": round(info.day_high, 2) if info.day_high else None,
        "day_low": round(info.day_low, 2) if info.day_low else None,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools.py <TICKER>")
        sys.exit(1)
    sym = sys.argv[1].upper()
    data = get_stock_price(sym)
    print(f"Price: {data['price']} {data['currency']}")
    print(f"Market cap: {data['market_cap']}")
    print(f"Day high: {data['day_high']}")
    print(f"Day low: {data['day_low']}")