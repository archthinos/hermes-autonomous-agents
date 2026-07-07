---
name: productivity-daily-review
description: Structured morning briefing and evening review for task management, calendar overview, and productivity insights
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [productivity, tasks, calendar, review, planning]
    related_skills: [google-workspace, linear, note-taking]
---

# Productivity Daily Review Skill

## Purpose
Provide structured morning briefings and evening reviews that help the user start and end their day with clarity, focus, and a sense of progress.

## Two Core Functions

### 1. Morning Briefing (7:00 AM)
**Goal:** Set clear priorities for the day ahead

### 2. Evening Review (7:00 PM)
**Goal:** Reflect on progress, prepare for tomorrow

---

## Morning Briefing Workflow

### Step 1: Gather Data (2-3 min)

**Tasks (if integrated):**
```python
# From Google Tasks, Linear, Todoist, or file-based system
tasks = fetch_all_tasks()
today_tasks = filter_by_date(tasks, date=today)
overdue_tasks = filter_by_date(tasks, date<today, status='open')
high_priority = filter_by_priority(tasks, priority=['P0', 'P1'])
```

**Calendar (if integrated):**
```python
# From Google Calendar or calendar.ics files
events = fetch_calendar_events(date=today)
conflicts = detect_conflicts(events)
free_blocks = calculate_free_time(events)
```

**Context:**
```python
# From previous evening review or memory
yesterday_progress = load_from_memory('yesterday_review')
this_week_goals = load_from_memory('week_goals')
```

### Step 2: Analyze & Prioritize (1-2 min)

**Priority Framework:**
```python
def calculate_priority(task):
    score = 0

    # Urgency
    if task.due_date == today: score += 10
    if task.due_date == today + 1: score += 5
    if task.is_blocking_others: score += 8

    # Importance
    if task.priority == 'P0': score += 10
    if task.priority == 'P1': score += 7
    if task.aligns_with_weekly_goal: score += 5

    # Effort
    if task.estimated_time < 30_min: score += 3  # Quick win bonus

    return score

# Sort by priority score
prioritized = sorted(tasks, key=calculate_priority, reverse=True)
top_3 = prioritized[:3]
```

**Calendar Analysis:**
```python
# Identify focus time
focus_blocks = [block for block in free_blocks if block.duration > 90_min]

# Check meeting load
meeting_minutes = sum([event.duration for event in events if event.is_meeting])
meeting_load = 'heavy' if meeting_minutes > 240 else 'moderate' if meeting_minutes > 120 else 'light'
```

### Step 3: Format Morning Briefing (1 min)

```markdown
☀️ Good morning! [Day of Week], [Date]

## 🎯 Today's Top 3 Priorities
1. **[Task Name]** [P0/P1] - Due: [Today/This Week]
   - Estimated: [X hours]
   - Blocks: [Suggested time blocks]

2. **[Task Name]** [P1]
   - Estimated: [X hours]

3. **[Task Name]** [P2]
   - Quick win - [X min]

## 📅 Calendar Overview ([Meeting Load])
- **[Time]**: [Event Name] ([Duration])
- **[Time]**: [Event Name]
- **[Time]**: FOCUS BLOCK ([Duration]) ⭐
  - Suggestion: Work on [Priority Task]

[If conflicts exist:]
⚠️ **Schedule Conflict:** [Time] - [Event A] overlaps [Event B]

## ⏰ Reminders
[If overdue tasks:]
- ⏰ **Overdue:** [Task Name] - Due [Date]

[If upcoming deadlines:]
- 📌 **Due Tomorrow:** [Task Name]
- 📌 **Due [Day]:** [Task Name]

## 💡 Suggestions
[Context-aware suggestions:]
- Your longest focus block is [Time-Time]. Perfect for [Complex Task].
- Light meeting day - great for deep work!
- OR: Heavy meeting day - schedule admin tasks between meetings.
- You've been working on [Project] for 3 days - almost there!

## 🎯 This Week's Goal
[Reminder of weekly goal and progress]
Progress: [X/Y tasks completed] ([Z%])
```

---

## Evening Review Workflow

### Step 1: Collect Today's Data (2-3 min)

**Completed Tasks:**
```python
completed_today = fetch_completed_tasks(date=today)
time_spent = calculate_time_spent(completed_today)
```

**Incomplete Tasks:**
```python
incomplete = fetch_tasks(status='open', planned_for=today)
reasons = analyze_why_incomplete(incomplete)
```

**Calendar Actuals:**
```python
attended_events = fetch_attended_events(today)
missed_events = fetch_missed_events(today)
```

### Step 2: Analyze Progress (1-2 min)

**Productivity Metrics:**
```python
# Task completion rate
completion_rate = len(completed_today) / len(today_tasks) * 100

# Priority completion (did we do what matters?)
priority_completion = len([t for t in completed_today if t.priority in ['P0', 'P1']])

# Estimate accuracy
estimated_vs_actual = compare_time_estimates(completed_today)
```

**Patterns:**
```python
# Time of day productivity
most_productive_hours = identify_peak_times(completed_tasks)

# Task types
completed_by_type = categorize_tasks(completed_today)

# Blockers
blockers = identify_blockers(incomplete)
```

### Step 3: Prepare Tomorrow (1 min)

**Tomorrow's Priorities:**
```python
tomorrow_tasks = fetch_tasks(due_date=tomorrow)
carried_over = [t for t in incomplete if t.priority in ['P0', 'P1']]
tomorrow_top_3 = prioritize(tomorrow_tasks + carried_over)[:3]
```

**Calendar Preview:**
```python
tomorrow_events = fetch_calendar_events(date=tomorrow)
tomorrow_free_time = calculate_free_time(tomorrow_events)
```

### Step 4: Format Evening Review (1 min)

```markdown
🌙 Evening Review - [Date]

## ✅ Completed Today
[If good progress:]
Great progress! [X/Y] tasks completed ([Z%])

**Finished:**
✅ [Task Name] ([Time spent])
✅ [Task Name]
✅ [Task Name]

[If struggled:]
Challenging day - [X/Y] tasks completed.
Let's adjust tomorrow's plan.

## 🔄 In Progress
[If incomplete high-priority tasks:]
- **[Task]** (P0) - [Reason incomplete]
  - Tomorrow: [Specific next action]

## 📊 Today's Insights
**Productivity:** [High/Moderate/Low] - [Reasoning]
**Focus Time:** [X hours] of deep work
**Meetings:** [X hours] ([Y meetings])

[If patterns noticed:]
💡 **Pattern Spotted:**
- You're most productive [time of day]
- OR: [Task type] tasks consistently take longer than estimated
- OR: Meetings interrupted flow - consider batching

## 🎯 Progress This Week
**Weekly Goal:** [Goal description]
- Progress: [X/Y tasks] ([Z%]) - [On track / Ahead / Behind]
- [Days remaining in week]

## 📅 Tomorrow's Plan ([Day of Week])

**Top 3 Priorities:**
1. [Carried over P0 task or tomorrow's priority]
2. [Task]
3. [Task]

**Calendar:**
- [X meetings] ([Y hours])
- [Z hours] of focus time available

**Energy Level:** [Predict based on tomorrow's schedule]
[If heavy meeting day:] Schedule lighter cognitive tasks
[If light meeting day:] Perfect for tackling [Complex Task]

## 💭 Notes
[If any observations:]
- [Blocker or concern]
- [Win to celebrate]
- [Adjustment needed]

Rest well! Tomorrow's plan is ready. 🌟
```

---

## Special Reviews

### Friday Evening - Weekly Wrap
```markdown
🎉 Week Complete! [Date Range]

## 📈 Weekly Metrics
- **Tasks Completed:** [X] ([Y%] of planned)
- **Top Priority Completion:** [X/Y] P0/P1 tasks done
- **Weekly Goal:** [Status]

## 🏆 This Week's Wins
1. [Achievement]
2. [Achievement]
3. [Achievement]

## 🤔 Lessons Learned
- [What worked well]
- [What to improve]

## 🔮 Next Week Preview
**Goals for [Week]:**
1. [Goal 1]
2. [Goal 2]

**Big Tasks:**
- [Upcoming task with deadline]
- [Upcoming task]

Have a great weekend! 🌟
```

### Monday Morning - Week Start
```markdown
🚀 New Week! [Week of Date]

## 🎯 This Week's Goals
1. [Primary goal]
2. [Secondary goal]
3. [Tertiary goal]

## 📅 Week at a Glance
- **Monday:** [Key tasks/events]
- **Tuesday:** [Key tasks/events]
- **Wednesday:** [Key tasks/events]
- ...

## ⚠️ Key Deadlines
- [Date]: [Deliverable]
- [Date]: [Deliverable]

## 💪 Let's make it happen!
Starting with today's top 3...
[Proceed with normal morning briefing]
```

---

## Proactive Features

### 1. Deadline Warnings
```python
# 3 days before deadline
if task.due_date - today == 3:
    send_warning(f"Reminder: {task.name} due in 3 days")

# Day before
if task.due_date - today == 1:
    send_urgent(f"Tomorrow: {task.name} deadline")
```

### 2. Capacity Checks
```python
# Overcommitment detection
total_estimated_time = sum([t.estimate for t in today_tasks])
available_time = 8 * 60 - meeting_minutes - 60  # 8h minus meetings minus buffer

if total_estimated_time > available_time * 1.2:
    suggest("Today's schedule is overloaded. Consider moving [task] to tomorrow.")
```

### 3. Streak Tracking
```python
# Motivational tracking
consecutive_days_hitting_top_3 = calculate_streak()

if consecutive_days_hitting_top_3 >= 7:
    celebrate("🔥 7-day streak! You're on fire!")
```

### 4. Pattern Recognition
```python
# Example insights
if user_always_productive_between(9, 11):
    suggest("Your peak focus time is 9-11 AM. Schedule your hardest task then.")

if user_underestimates_time_for('coding'):
    suggest("Coding tasks typically take you 1.5x estimate. Adjust accordingly.")
```

---

## Integration Points

### Supported Task Systems
- Google Tasks (via API)
- Linear (via API)
- Todoist (via API)
- File-based (markdown todo files)
- Memory-based (ephemeral, stored in MEMORY.md)

### Supported Calendars
- Google Calendar (via API)
- iCal files (.ics)
- Manual input (user tells agent events)

### Fallback (No Integrations)
```python
# If no external integrations:
# 1. Ask user for top 3 priorities
# 2. Ask for any deadlines today
# 3. Ask for calendar highlights
# 4. Generate review based on conversation history
```

---

## Success Criteria

**Morning Briefing:**
- User knows their top 3 priorities
- Calendar conflicts flagged
- Realistic daily plan
- Motivating and clear

**Evening Review:**
- Honest assessment of progress
- Celebrates wins (even small ones)
- Identifies blockers for resolution
- Tomorrow is planned and ready

**Overall:**
- User feels organized, not overwhelmed
- Deadlines never missed (with sufficient warning)
- Continuous improvement in time estimation
- Sustainable productivity pace

---

This skill creates a daily ritual that transforms productivity from reactive chaos into intentional progress.
