---
name: Get Latest News
description: Fetch breaking news and headlines for market analysis
---

# Get Latest News

Use these with WebFetch to get current news for market analysis.

## General Breaking News
```
URL: https://news.google.com/rss
Prompt: List the top 10 headlines with their sources
```

## Topic-Specific News (Google News)
Replace TOPIC with your search term:
```
URL: https://news.google.com/rss/search?q=TOPIC
Prompt: List all headlines related to TOPIC with sources and dates
```

### Common Topics for Polymarket:
- Iran conflict: `https://news.google.com/rss/search?q=iran+war+conflict`
- US politics: `https://news.google.com/rss/search?q=trump+policy+congress`
- Crude oil: `https://news.google.com/rss/search?q=crude+oil+price`
- Bitcoin/crypto: `https://news.google.com/rss/search?q=bitcoin+crypto`
- Federal Reserve: `https://news.google.com/rss/search?q=federal+reserve+interest+rate`
- Climate/weather: `https://news.google.com/rss/search?q=climate+weather+extreme`

## Reuters World News
```
URL: https://feeds.reuters.com/reuters/worldNews
Prompt: List the top 10 world news headlines
```

## BBC World News
```
URL: http://feeds.bbci.co.uk/news/world/rss.xml
Prompt: List the top 10 world news headlines
```

## AP News
```
URL: https://rsshub.app/apnews/topics/apf-topnews
Prompt: List the top 10 news headlines
```

## How to Use for Market Analysis
1. Identify what topic a Polymarket question relates to
2. Fetch news for that topic using Google News RSS search
3. Read the headlines and assess how they change the probability
4. Compare your estimate to the market price to find edge
