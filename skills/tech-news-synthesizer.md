---
name: tech-news-synthesizer
description: Synthesize tech news from Hacker News, Dev.to, and Reddit r/programming into coherent thematic digest with cross-source analysis
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tech-news, aggregation, analysis, synthesis]
    related_skills: [web-scraping, content-analysis]
---

# Tech News Synthesizer Skill

## Purpose
Go beyond simple news aggregation - synthesize multiple sources to identify themes, separate signal from noise, and provide context-rich tech news digests.

## Sources & Strategy

### 1. Hacker News
**URL:** https://news.ycombinator.com/
**What to check:**
- Front page (top 30 stories)
- "Show HN" (new projects/launches)
- "Ask HN" (community insights)

**Scoring criteria:**
- Points: Higher = more community interest
- Comments: More discussion = controversial or important
- Age: Adjust for time on front page

**Extract:**
- Story title and URL
- Points and comment count
- Domain (to identify sources)
- Top 2-3 comment insights (for context)

### 2. Dev.to
**URL:** https://dev.to/
**Sections:**
- Top/Week (weekly popular posts)
- Featured (editorial picks)
- Tags: #ai, #python, #javascript, #rust, #devops

**Quality indicators:**
- Reactions (hearts)
- Reading time (comprehensive vs. shallow)
- Author reputation
- Tag relevance

**Extract:**
- Post title and author
- Key tags
- Reaction count
- First few paragraphs (for summary)

### 3. Reddit r/programming
**URL:** https://www.reddit.com/r/programming/hot/
**Also check:**
- r/programming/top (today, this week)
- r/webdev (for web-specific)
- r/ExperiencedDevs (senior perspectives)

**Quality indicators:**
- Upvotes (community validation)
- Comments (engagement level)
- Reddit awards (exceptional content)
- Upvote ratio (controversial if low)

**Extract:**
- Post title and link
- Upvotes and comment count
- Top comment (community reaction)
- Submission domain

---

## Workflow

### Step 1: Parallel Collection (3-5 min)

```python
# Fetch all sources simultaneously
hacker_news_stories = fetch_hn_front_page(limit=30)
devto_posts = fetch_devto_top_week(limit=20)
reddit_posts = fetch_reddit_hot(subreddit='programming', limit=30)

# Optional: Also check
hn_show = fetch_hn_newest(prefix='Show HN', limit=10)
hn_ask = fetch_hn_newest(prefix='Ask HN', limit=10)
```

### Step 2: Deduplication & Cross-Referencing (2-3 min)

```python
# Identify same story across platforms
for story in hacker_news_stories:
    # Check if same URL on Reddit
    reddit_match = find_matching_url(reddit_posts, story.url)
    if reddit_match:
        story.cross_platform = True
        story.reddit_engagement = reddit_match.upvotes

    # Check if article about same topic on Dev.to
    devto_match = find_matching_topic(devto_posts, story.title)
    if devto_match:
        story.devto_perspective = devto_match.url

# Cross-platform stories = higher significance
cross_platform_stories = [s for s in all_stories if s.cross_platform]
```

### Step 3: Theme Extraction (2-3 min)

```python
# Identify recurring themes
themes = {
    'ai_ml': ['gpt', 'llm', 'ai', 'machine learning', 'neural', 'model'],
    'languages': ['rust', 'python', 'javascript', 'go', 'typescript'],
    'frameworks': ['react', 'vue', 'nextjs', 'django', 'fastapi'],
    'devops': ['kubernetes', 'docker', 'ci/cd', 'deployment'],
    'performance': ['optimization', 'speed', 'benchmark', 'faster'],
    'security': ['vulnerability', 'exploit', 'cve', 'security'],
    'web3': ['blockchain', 'crypto', 'web3', 'ethereum'],
    'databases': ['postgres', 'mongodb', 'redis', 'sqlite'],
}

# Categorize stories
for story in all_stories:
    story.themes = identify_themes(story.title + story.content, themes)

# Find trending themes
trending_themes = [theme for theme, stories in group_by_theme(all_stories)
                   if len(stories) >= 3]  # Theme appears in 3+ stories
```

### Step 4: Quality Filtering (1-2 min)

```python
def calculate_story_score(story):
    score = 0

    # Engagement
    score += story.hn_points * 0.5
    score += story.reddit_upvotes * 0.3
    score += story.devto_reactions * 0.2

    # Cross-platform boost
    if story.cross_platform:
        score *= 1.5

    # Recency (favor recent)
    if story.age_hours < 12:
        score *= 1.2

    # Quality indicators
    if story.has_indepth_discussion:  # >50 comments
        score *= 1.3
    if story.from_reputable_source:  # Known tech blog/company
        score *= 1.2

    return score

# Filter and rank
top_stories = sorted(all_stories, key=calculate_story_score, reverse=True)[:15]
```

### Step 5: Synthesis & Narrative (2-3 min)

```python
# Create narrative arc
synthesis = {
    'headline': identify_biggest_story(top_stories),
    'trending_themes': trending_themes,
    'cross_platform_highlights': cross_platform_stories,
    'show_hn_spotlight': most_interesting_show_hn,
    'community_debates': controversial_discussions,
    'quick_hits': other_notable_stories
}

# Add context and commentary
for story in synthesis.values():
    add_context(story)  # Why this matters
    add_community_reaction(story)  # What people are saying
```

---

## Output Format

### For Daily Tech News Digest:

```markdown
💻 Tech News Synthesizer - [Date]

## 🔥 Today's Headline
**[Biggest Story Title]**
[2-3 sentence summary with context]

**Discussion:** [Key points from HN/Reddit comments]
**Why it matters:** [Significance and implications]

Sources: [HN: X points | Reddit: Y upvotes | Dev.to: Z reactions]
[Primary URL]

---

## 📈 Trending Themes Today

### 🤖 AI/ML Wave
[Theme appears X times across sources]

**Stories:**
1. **[Story Title]** - [One sentence]
   - [HN: X pts] [Reddit: Y upvotes]
2. **[Story Title]** - [One sentence]

**Synthesis:** [What's the common thread? What's the trend?]

### 🦀 Rust Rising (or whatever theme)
[Similar structure]

---

## 🌐 Cross-Platform Highlights
These stories are trending on multiple platforms - high signal!

1. **[Story Title]**
   - 📰 HN: [X points, Y comments]
   - 🗨️ Reddit: [X upvotes] - Top comment: "[Quote]"
   - 💬 Dev.to: [X reactions]

   **Why everyone's talking about it:** [Explanation]
   [URL]

---

## 🚀 Show HN Spotlight
Cool projects launched on Hacker News today

1. **[Project Name]** - [Description]
   - [What it does in 1 sentence]
   - [Why interesting]
   - [HN: X points]
   - [URL]

2. [More Show HN items...]

---

## 🔥 Community Debates
Controversial or thought-provoking discussions

1. **[Topic]** ([Source])
   - **The question:** [What's being debated]
   - **Perspectives:**
     - Pro: [Argument]
     - Con: [Counter-argument]
   - **Worth reading if:** [You care about X]
   [URL]

---

## ⚡ Quick Hits
Other notable stories worth knowing

- **[Category]:** [Title] - [One sentence] [[Source]]
- **[Category]:** [Title] - [One sentence] [[Source]]
- **[Category]:** [Title] - [One sentence] [[Source]]

---

## 💡 What's Hot This Week
Based on past 7 days of data:
- [Trend 1]: [X stories, growing interest]
- [Trend 2]: [Y stories, sustained discussion]
- [Trend 3]: [Z stories, emerging topic]

---

## 🔮 Worth Watching
Stories that might become big:
- [Story with momentum but still early]
- [Interesting project/post with potential]
```

### For Breaking Tech News Alert:

```markdown
🚨 BREAKING: [Event/Announcement]

**What happened:** [2-3 sentence summary]

**Sources blowing up:**
- HN: [X points in Y hours] ([Z comments])
- Reddit: [X upvotes, top of r/programming]
- Dev.to: [Featured / Trending]

**Key Reactions:**
[Top comment from HN]: "[Quote]"
[Top comment from Reddit]: "[Quote]"

**Why this matters:**
[Significance, implications, what changes]

**What to read:**
- Official announcement: [URL]
- Technical analysis: [URL if available]
- Community discussion: [Best thread URL]

**Our take:** [Brief analysis]
```

### For Weekly Tech Roundup:

```markdown
📅 Tech Week in Review - [Date Range]

## 🏆 Story of the Week
[Most impactful story with full context]

## 🔥 Top 5 Stories
1. [Story] - [Impact score: X]
2. [Story] - [Impact score: Y]
...

## 📊 Trending Topics
[Graph or list of most-discussed themes]

## 🚀 Notable Launches
[Show HN and product releases]

## 💬 Best Discussions
[Most insightful Ask HN / Reddit threads]

## 🔮 Emerging Trends
[What's gaining momentum]

## 📚 Must-Read Articles
[Best technical deep-dives from Dev.to]
```

---

## Advanced Features

### 1. Sentiment Analysis
```python
# Analyze comment sentiment
for story in stories:
    comments = fetch_comments(story)
    sentiment = analyze_sentiment(comments)
    story.community_sentiment = sentiment  # positive, negative, mixed, neutral
```

### 2. Topic Clustering
```python
# Use embeddings to cluster similar stories
from sklearn.cluster import DBSCAN

embeddings = [get_embedding(story.title) for story in stories]
clusters = DBSCAN(eps=0.3).fit(embeddings)

# Stories in same cluster = related topic
```

### 3. Source Quality Scoring
```python
# Track which sources consistently provide valuable content
reputable_sources = [
    'arstechnica.com',
    'blog.cloudflare.com',
    'engineering.fb.com',
    'github.blog',
    # etc.
]

if story.domain in reputable_sources:
    story.quality_boost = 1.3
```

### 4. Personalization
```python
# Learn user's interests from past engagement
user_interests = fetch_user_preferences()

for story in stories:
    if story.theme in user_interests['high_interest']:
        story.relevance_score *= 1.5
    elif story.theme in user_interests['low_interest']:
        story.relevance_score *= 0.5
```

---

## Quality Checks

### Red Flags (Downrank/Skip):
- Clickbait titles (all caps, sensational language)
- Low upvote/comment ratio (upvoted but no discussion = bot votes?)
- Known low-quality domains
- Duplicate submissions (same URL multiple times)
- Off-topic for tech audience

### Green Flags (Boost):
- Original research or data
- In-depth technical writeups (>10 min read)
- Company engineering blogs
- Cross-platform popularity
- High comment quality
- Author reputation (if trackable)

---

## Integration with Other Agents

### Handoffs to Specialists:
- AI story → Alert **AI Researcher** agent
- Crypto story → Alert **Crypto Agent**
- GitHub trending crossover → Share with **Software Dev** agent
- Controversial topic → Flag for **Web Researcher** deep dive

### Feedback Loop:
- Track which synthesized stories user engages with
- Learn user's preferred sources
- Adjust theme weights based on user reactions
- Improve story scoring algorithm

---

## Error Handling

**If source unavailable:**
- Skip gracefully, note in output
- Continue with other sources
- Don't fail entire digest

**If no stories meet threshold:**
- Lower quality bar slightly
- Include "slow news day" note
- Highlight best available stories with caveat

**If API rate limited:**
- Use cached data (mark staleness)
- Fall back to web scraping
- Reduce polling frequency

---

## Time & Resource Budget

- **Collection:** 3-5 minutes (parallel requests)
- **Processing:** 4-6 minutes (dedup, theme extraction, scoring)
- **Synthesis:** 2-3 minutes (narrative building)
- **Total:** 10-15 minutes per digest

**API Calls:**
- HN API: ~5 calls (paginated)
- Reddit API: ~3 calls (or use PRAW library)
- Dev.to: Web scraping (no official API)
- Total: <20 API requests per digest

---

## Success Criteria

- Identified recurring themes (not just listing links)
- Cross-platform validation (high-signal stories)
- Contextual commentary (not just summaries)
- Time-saving (15-min digest vs. 1h manual browsing)
- Actionable insights (user learns something useful)
- Personalized relevance (>80% of stories matter to user)

---

This skill transforms information overload into intelligence. Instead of drowning in hundreds of tech stories daily, the user gets a curated, synthesized, contextualized digest that actually teaches them something.
