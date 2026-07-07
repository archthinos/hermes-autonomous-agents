---
name: github-trending-analyzer
description: Analyze GitHub trending repositories with context on why they're trending, quality assessment, and relevance to user interests
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, dev-tools, trending, analysis]
    related_skills: [software-development, code-review]
---

# GitHub Trending Analyzer Skill

## Purpose
Go beyond just listing trending repos - analyze WHY they're trending, assess quality, and determine relevance to the user's tech stack and interests.

## Sources

### 1. GitHub Trending Page
**URLs to check:**
- https://github.com/trending (all languages, today)
- https://github.com/trending/javascript (if user interested in JS)
- https://github.com/trending/python (if user interested in Python)
- https://github.com/trending/typescript
- https://github.com/trending/rust
- https://github.com/trending/go

**Time periods:**
- Today: For breaking developments
- This week: For rising stars
- This month: For sustained interest

### 2. Data to Extract per Repository

**Basic Info:**
- Repository name and URL
- Description (official)
- Stars gained today/week
- Total stars, forks, watchers
- Primary language
- License
- Last commit date

**Quality Indicators:**
- Has comprehensive README?
- Has tests?
- Has CI/CD?
- Has contributing guidelines?
- Active maintenance (recent commits)?
- Issue response rate
- Documentation quality

**Relevance Signals:**
- Problem it solves
- Target audience (beginners, pros, enterprises)
- Maturity level (prototype, beta, production-ready)
- Similar/competing projects
- Unique value proposition

## Analysis Framework

### For Each Trending Repo, Answer:

1. **What is it?**
   - One-sentence description
   - Category (framework, library, tool, app, etc.)

2. **Why is it trending NOW?**
   - Recent launch/announcement?
   - Featured somewhere (HN, Reddit, Twitter)?
   - Solves timely problem?
   - Viral demo or use case?

3. **Quality Assessment (1-5 stars):**
   - ⭐ Prototype (experimental, use with caution)
   - ⭐⭐ Alpha (promising but rough edges)
   - ⭐⭐⭐ Beta (functional, some gaps)
   - ⭐⭐⭐⭐ Stable (production-ready)
   - ⭐⭐⭐⭐⭐ Mature (battle-tested, excellent docs)

4. **Relevance to User (High/Medium/Low):**
   - High: Directly applicable to user's stack/interests
   - Medium: Tangentially related or future interest
   - Low: Interesting but not immediately relevant

5. **Red Flags:**
   - No license
   - Suspicious activity (star buying)
   - Abandoned/unmaintained
   - Security concerns
   - Over-hyped claims

## Workflow

### Step 1: Bulk Collection (2-3 min)
```bash
# Use web_extract to scrape trending page
url = "https://github.com/trending"
extract trending repos: name, description, stars today, total stars, language
```

### Step 2: Parallel Deep Dives (5-7 min)
For top 5-10 repos:
```python
# Visit each repo page
for repo in top_repos:
    - Read README (first 500 words)
    - Check recent commits (last 7 days)
    - Scan issues (open vs closed ratio)
    - Look for tests/ or ci/ directories
    - Check if documentation site exists
    - Search for "[repo name] hacker news" (see if discussed)
```

### Step 3: Cross-Reference (2 min)
- Check if mentioned on Hacker News
- Look for Reddit discussions
- Search Twitter for reactions
- Find competing/similar projects

### Step 4: Ranking & Filtering (1-2 min)
Prioritize by:
```
Score = (Stars gained today * 2) + (Relevance * 3) + (Quality * 2)
```

Only report repos with:
- Score > threshold (e.g., 15)
- Quality >= 3 stars
- No major red flags

## Output Format

### For Daily Digest:
```markdown
💻 GitHub Trending - [Date]

## 🔥 Top Rising Stars

### 1. [Repo Name] ⭐ +[X] stars today
**What:** [One-sentence description]
**Why trending:** [Specific catalyst or reason]
**Quality:** ⭐⭐⭐⭐ (Production-ready)
**Relevance:** High - [Why it matters to you]
**Quick take:** [2-3 sentence analysis]
**Check it out:** [URL]

### 2. [Repo Name] ⭐ +[X] stars today
[Same structure]

## 📊 This Week's Momentum

- **[Repo]** - Sustained growth, [X]k stars
- **[Repo]** - [Notable achievement or milestone]

## ⚠️ Worth Watching (but not ready yet)

- **[Repo]** - Promising concept, early stage
- **[Repo]** - Wait for stability/docs

## 💡 Alternative Spotlight

If trending list is weak, highlight:
- Underrated gems (low stars, high quality)
- Recent releases from known projects
- Interesting forks or alternatives
```

### For Breaking Trends:
```markdown
🚨 GITHUB ALERT: [Repo Name] is VIRAL

**+[X] stars in 24h** (now [Y] total)

What it does: [Description]
Why everyone's talking about it: [Reason]

Key features:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Comparison to alternatives:
- vs [Competitor 1]: [Key diff]
- vs [Competitor 2]: [Key diff]

Should you try it? [Yes/No/Wait] - [Reasoning]

[URL]
```

## Quality Checks

### Automated Checks:
```python
def assess_quality(repo):
    score = 0

    # Has README > 1000 chars
    if len(readme) > 1000: score += 1

    # Has tests
    if has_directory('tests/') or has_directory('test/'): score += 1

    # Has CI
    if has_file('.github/workflows/'): score += 1

    # Active (commit in last 7 days)
    if days_since_last_commit < 7: score += 1

    # Good issue management (close rate > 50%)
    if issue_close_rate > 0.5: score += 1

    # Has docs site or comprehensive README
    if has_docs_site or readme_sections > 5: score += 1

    return min(score, 5)  # Cap at 5 stars
```

## Avoid These Mistakes

1. **Don't just list trending repos** - Add analysis
2. **Don't ignore context** - Explain why trending NOW
3. **Don't skip quality check** - Trending ≠ good
4. **Don't report everything** - Filter for relevance
5. **Don't miss the "why"** - Stars alone don't tell the story

## Integration with Other Agents

- **AI Researcher:** Flag AI/ML repos
- **Crypto Agent:** Flag Web3/blockchain repos
- **Orchestrator:** Report only High relevance items to user

## Success Criteria

- Discovered trending repos within 24h of going viral
- Provided meaningful analysis, not just links
- Filtered out low-quality or irrelevant items
- Explained WHY each repo matters
- Saved user from having to do their own research

---

This skill transforms GitHub trending from a raw list into curated, analyzed intelligence.
