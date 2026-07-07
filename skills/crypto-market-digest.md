---
name: crypto-market-digest
description: Multi-source crypto market analysis combining price data, DeFi metrics, Polymarket predictions, and on-chain signals
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [crypto, defi, markets, polymarket, analysis]
    related_skills: [data-analysis, web-scraping]
---

# Crypto Market Digest Skill

## Purpose
Aggregate crypto market intelligence from multiple sources to provide a comprehensive, data-driven market snapshot without manual browsing of 10+ sites.

## Data Sources

### 1. Price & Market Data
**CoinGecko API (Free):**
- Endpoint: `https://api.coingecko.com/api/v3/simple/price`
- Get: BTC, ETH, SOL prices + 24h change
- Market caps and volumes
- Total market cap

**Alternative: CoinMarketCap**
- `https://coinmarketcap.com/`
- Top 100 movers (+ and -)

### 2. DeFi Metrics
**DeFiLlama API:**
- Endpoint: `https://api.llama.fi/protocols`
- Total Value Locked (TVL) across protocols
- 24h TVL change
- Top protocols by TVL

**Key Protocols to Track:**
- Uniswap (DEX)
- Aave (Lending)
- Lido (Liquid Staking)
- MakerDAO (Stablecoin)
- Curve (Stableswap)

### 3. Polymarket Predictions
**Polymarket API/Scraping:**
- URL: `https://polymarket.com/`
- Trending markets (volume, participants)
- AI-related predictions
- Crypto price predictions
- Tech industry bets

**Focus Areas:**
- AI development milestones
- Crypto adoption predictions
- Tech company outcomes
- Economic indicators

### 4. On-Chain Signals
**Glassnode / Blockchain Explorers:**
- Bitcoin hash rate
- Exchange inflows/outflows
- Whale transactions (>$1M)
- Stablecoin supply changes

**Free alternatives:**
- Etherscan gas prices
- Bitcoin mempool size
- Active addresses

### 5. Market Sentiment
**Fear & Greed Index:**
- URL: `https://alternative.me/crypto/fear-and-greed-index/`
- Current reading (0-100)
- Historical comparison

**Social Sentiment:**
- Crypto Twitter engagement
- Reddit r/cryptocurrency sentiment
- Google Trends for "buy bitcoin" etc.

## Workflow

### Step 1: Price Snapshot (1-2 min)
```python
# Parallel API calls
prices = {
    'BTC': get_price('bitcoin'),
    'ETH': get_price('ethereum'),
    'SOL': get_price('solana'),
    'Total Market Cap': get_total_mcap()
}

# Calculate changes
for asset in prices:
    prices[asset]['24h_change'] = calculate_change()
    prices[asset]['7d_change'] = calculate_change(period='7d')
```

### Step 2: DeFi Overview (1-2 min)
```python
# Get top protocols
protocols = fetch_defi_llama_protocols()
total_tvl = sum([p['tvl'] for p in protocols])
tvl_change_24h = calculate_total_tvl_change()

# Highlight significant movers
movers = [p for p in protocols if abs(p['change_24h']) > 5%]
```

### Step 3: Polymarket Scan (2-3 min)
```python
# Scrape or API call
markets = fetch_polymarket_trending()

# Filter for relevance
relevant = filter_markets(markets, categories=['AI', 'Crypto', 'Tech'])

# Extract probability shifts
for market in relevant:
    if abs(market['prob_change_24h']) > 10:
        flag_as_significant(market)
```

### Step 4: Sentiment & Signals (1-2 min)
```python
# Fear & Greed
fg_index = fetch_fear_greed_index()
fg_interpretation = interpret_fg(fg_index)

# On-chain (if available)
signals = {
    'btc_hashrate': fetch_hashrate(),
    'eth_gas': fetch_gas_price(),
    'stablecoin_supply': fetch_stablecoin_data()
}
```

### Step 5: Synthesis (1 min)
Combine all data into coherent narrative:
- What's the overall market direction?
- Any unusual movements or catalysts?
- DeFi trends matching price action?
- Polymarket predictions aligning with reality?
- Sentiment vs. price (bullish but prices down = contrarian signal)

## Output Format

### For Regular Market Digest:
```markdown
💰 Crypto Market Digest - [Date] [Time]

## 📊 Market Snapshot
**BTC:** $[X] ([±X%] 24h) | **ETH:** $[X] ([±X%] 24h) | **SOL:** $[X] ([±X%] 24h)
**Total Market Cap:** $[X]T ([±X%] 24h)
**Fear & Greed:** [X]/100 ([Sentiment])

## 🔝 Top Movers (24h)
🔼 **[Asset]** +[X%] - $[Price] ([Catalyst if known])
🔽 **[Asset]** -[X%] - $[Price] ([Reason if known])

## 💎 DeFi Snapshot
**Total TVL:** $[X]B ([±X%] 24h)

**Protocol Highlights:**
- **[Protocol]:** $[X]B TVL ([±X%]) - [Note if significant]
- **[Protocol]:** $[X]B TVL ([±X%]) - [Note if significant]

## 🎲 Polymarket Watch
**Trending Markets:**
1. **[Market Question]** - [X%] probability ([+/-X%] shift)
   - [Brief context or significance]
2. **[Market Question]** - [X%] probability
   - [Brief context]

## 🔗 On-Chain Signals
- [Signal 1]: [Value] ([Interpretation])
- [Signal 2]: [Value] ([Interpretation])

## 💭 Market Context
[2-3 sentence synthesis]
- Current trend: [Bullish/Bearish/Sideways]
- Key drivers: [What's moving the market]
- Watch for: [Upcoming events or levels]

## 📅 Upcoming Catalysts
- [Date]: [Event] - Potential impact: [High/Medium/Low]
```

### For Price Alerts:
```markdown
🚨 CRYPTO ALERT: [Asset] [±X%]

**Price:** $[X] ([Change])
**24h Volume:** $[X] ([vs. average: ±X%])
**Market Cap Rank:** #[X]

**Catalyst:** [If known, otherwise "Price discovery / Technical break"]

**Key Levels:**
- Support: $[X]
- Resistance: $[X]

**Context:** [1-2 sentences]

**Polymarket:** [Related prediction market if exists]
```

### For DeFi Events:
```markdown
⚡ DeFi UPDATE: [Protocol Name]

**Event:** TVL [+/-X%] in 24h (now $[X]B)

**What happened:**
[Explanation - new pool, governance change, exploit, etc.]

**Significance:** [Why it matters]

**Impact on market:** [If any]

**Action:** [If user should care / Any risk?]
```

## Analysis Framework

### Interpreting Signals

**Fear & Greed Index:**
- 0-25 (Extreme Fear): Potential buy opportunity / bottoming
- 25-45 (Fear): Cautious, might not be bottom yet
- 45-55 (Neutral): Market balanced
- 55-75 (Greed): Take profits, be cautious
- 75-100 (Extreme Greed): High risk, potential top

**TVL Movements:**
- Rising TVL + Rising prices = Healthy growth
- Rising TVL + Falling prices = Potential rebound
- Falling TVL + Rising prices = Weak foundation
- Falling TVL + Falling prices = Bear market

**Polymarket Probabilities:**
- >70%: Strong consensus (price likely)
- 40-60%: Uncertainty (opportunity?)
- <30%: Unlikely (contrarian bet)

## Error Handling & Fallbacks

1. **If API rate limited:**
   - Fall back to web scraping
   - Use cached data (note staleness)

2. **If data source down:**
   - Skip that source
   - Note in output
   - Continue with other sources

3. **If all sources fail:**
   - Return cached digest with warning
   - Suggest manual check

## Optimization Tips

1. **Cache API responses:**
   - 5-minute cache for prices (fast-moving)
   - 1-hour cache for TVL (slower-moving)
   - 4-hour cache for Polymarket (unless specific market alert)

2. **Parallel requests:**
   - Fetch all APIs simultaneously
   - Total time should be <10 seconds for all data

3. **Smart filtering:**
   - Don't report every <1% move
   - Focus on significant changes (>5%)
   - User cares about BTC/ETH/SOL most

## Risk Disclaimers

Always include:
```
⚠️ This is market information, not financial advice.
Crypto markets are highly volatile and speculative.
Always do your own research and never invest more than you can afford to lose.
```

## Success Criteria

- Comprehensive snapshot in <10 minutes
- Covered 4+ data sources
- Identified at least 1 actionable insight
- No stale data (all < 1 hour old)
- Clear, concise formatting

---

This skill turns 30 minutes of market research across 10+ sites into a single, comprehensive 5-minute digest.
