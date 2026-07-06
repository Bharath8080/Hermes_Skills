---
name: stock-price
description: "Use when the user asks for current stock price, stock quote, ticker price, or market data (e.g., 'what is NVDA price', 'current price of Apple', 'TSLA quote'). Fetches live USD quotes via yfinance."
priority: 100
triggers_regex:
  - ".*stock price.*"
  - ".*current (?:price|quote).*"
  - "what (?:is|'s).*price.*(?:stock|ticker)"
metadata:
  hermes:
    tags: [finance, stocks, yfinance, market-data]
    config:
      - key: stock_price.enabled
        description: "Enable stock price lookup via yfinance"
        default: true
        prompt: "Enable stock price skill?"
      - key: stock_price.description
        description: "Display label for the skill"
        default: "Stock price lookup via yfinance"
        prompt: "Short description for the skill"
---

# Stock Price Skill

- Install once: `pip install yfinance`
- Helper lives at `skills/stock-price/scripts/tools.py`

## Usage
```python
from skills.stock_price.scripts.tools import get_stock_price
get_stock_price("AAPL")  # {"price": 214.37, "currency": "USD"}
```

Or run the script directly (clean formatted output):
```bash
python ${HERMES_SKILL_DIR}/scripts/tools.py AAPL
```

The script returns price, market cap, day high, and day low:
```bash
python ${HERMES_SKILL_DIR}/scripts/tools.py AAPL
```

## Config Settings

The skill declares two config settings in `config.yaml` under `skills.config.stock_price`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Enable stock price lookups |
| `description` | string | `"Stock price lookup via yfinance"` | Display label |

Set via `hermes config set skills.config.stock_price.<key> <value>` or edit config.yaml directly.

## Pitfalls
- **Markets closed (weekend/holiday)** — `fast_info.last_price` returns the last traded price from the most recent trading session, not real-time. On weekends or US market holidays (e.g. July 4th Independence Day), the price shown is from the previous trading day. Mention this to the user when it's relevant (e.g. "US markets are closed today; this reflects Thursday's close").
- **yfinance not installed** — If `import yfinance` fails, run `pip install yfinance` first.
- **Non-USD tickers** — yfinance returns prices in the stock's native currency. Indian stocks (e.g. `RELIANCE.NS`) return INR. Always include the currency in the output.
- **Delayed quotes** — yfinance quotes are typically 15-20 minute delayed, not real-time. Don't claim prices are "live" or "real-time".
