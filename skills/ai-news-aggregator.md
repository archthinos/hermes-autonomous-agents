---
name: ai-news-aggregator
description: Aggregate AI/ML news from multiple sources including Hugging Face, Papers with Code, AI company blogs, and research labs
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ai, research, news, aggregation]
    related_skills: [arxiv-search, web-scraping]
---

# AI News Aggregator Skill

## Purpose
This skill helps the AI Researcher Agent aggregate breaking AI/ML news from multiple high-quality sources in a single pass, reducing redundant searches and API calls.

## Sources to Check

### 1. Hugging Face Trending
**URL:** https://huggingface.co/models?sort=trending
**What to extract:**
- Top 5 trending models (last 24h)
- Model name, author, description
- Downloads and likes
- Release date if recent (<7 days)

### 2. Papers with Code
**URL:** https://paperswithcode.com/greatest
**What to extract:**
- Top papers from last 7 days
- Paper title, authors, venue
- GitHub stars if implementation available
- Key benchmark improvements

### 3. Major AI Labs (Blogs/Announcements)
Check these sources for new posts:
- **OpenAI Blog:** https://openai.com/news/
- **Anthropic News:** https://www.anthropic.com/news
- **Google DeepMind:** https://deepmind.google/discover/blog/
- **Meta AI:** https://ai.meta.com/blog/
- **Mistral AI:** https://mistral.ai/news/

**What to extract:**
- New blog posts (last 3 days)
- Post title and summary
- Key announcements or releases

### 4. AI Twitter Aggregation
**Suggested accounts to check (if Twitter API available):**
- @OpenAI, @AnthropicAI, @MetaAI, @GoogleDeepMind
- @karpathy, @fchollet, @ylecun, @goodfeli
- Look for posts with >1000 likes in last 24h

### 5. Hugging Face Daily Papers
**URL:** https://huggingface.co/papers
**What to extract:**
- Top 3 papers highlighted today
- Quick summary and significance

## Workflow

1. **Parallel Searches** (use web_search with multiple queries simultaneously):
   ```
   Query 1: "Hugging Face trending models today"
   Query 2: "Papers with Code latest AI research"
   Query 3: "OpenAI Anthropic Meta AI latest news"
   Query 4: "AI breakthrough announcement" site:openai.com OR site:anthropic.com OR site:deepmind.google
   ```

2. **Extract & Parse:**
   - Use web_extract on the most promising URLs
   - Parse structured data (JSON APIs if available)
   - Look for dates to filter recency

3. **Deduplicate:**
   - Check if same model/paper mentioned across sources
   - Combine information from multiple mentions
   - Prioritize primary sources

4. **Rank by Significance:**
   - Novel architecture/approach: High priority
   - Major performance improvement: High priority
   - Incremental improvement: Medium priority
   - Tool/demo release: Medium priority
   - Commentary/analysis: Low priority

5. **Format Output:**
   ```markdown
   🔬 AI News Aggregation - [Date]

   ## Trending Models (Hugging Face)
   1. [Model Name] by [Author] - [Description]
      - [Downloads/Stars] - Released [Date]

   ## Latest Research (Papers with Code)
   1. [Paper Title] - [Authors]
      - Improvement: [Metric]
      - Code: [GitHub link if available]

   ## Lab Announcements
   - **[Lab]:** [Title] - [1-sentence summary]

   ## Community Highlights
   - [Viral post or discussion]
   ```

## Optimization Tips

1. **Use browser tool for dynamic content:**
   - Hugging Face trending loads via JavaScript
   - Consider using `browser.goto()` then `browser.extract()`

2. **Cache results:**
   - Store in shared knowledge base to avoid re-fetching
   - Mark with timestamp for freshness checks

3. **Respect rate limits:**
   - Don't hammer same site repeatedly
   - Use exponential backoff on errors

4. **Focus on novelty:**
   - Cross-reference with past 7 days of reports
   - Only include if genuinely new or significant update

## Error Handling

- If a source is down, skip it gracefully
- If API rate limited, fall back to web scraping
- If extraction fails, note it but continue with other sources
- Always return something, even if just partial results

## Time Budget

- Total time: 5-10 minutes
- Parallel searches: 2-3 min
- Extraction & parsing: 3-5 min
- Ranking & formatting: 1-2 min

## Success Criteria

- Covered at least 3 of 5 source categories
- Found at least 2 novel items (not seen before)
- Completed within time budget
- Formatted clearly and concisely

---

This skill turns a 30-minute manual aggregation task into a 5-10 minute automated workflow.
