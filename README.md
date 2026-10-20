# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation Summary

The system is four classes in `pawpal_system.py`. `Task` represents a single piece of care work — a description, duration, priority, and scheduled time. `Pet` holds a pet's identity and health info and owns its own list of `Task`s. `Owner` holds a list of `Pet`s and can flatten every pet's tasks into one list with `get_all_tasks()`. `Scheduler` is the only class with ordering logic: it reads tasks exclusively through `Owner.get_all_tasks()` (never from a single `Pet` directly, so scheduling always spans every pet an owner has), ranks them by priority and duration, and assigns each one a time slot within the day's constraints — the result can be rendered as a readable timeline with `explain_plan()`. `main.py` demonstrates the whole flow end to end: build an `Owner` with two `Pet`s, add tasks to each, and print the generated schedule.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]

#   ...

```
Today's Schedule
=================
07:00 — Feeding (10 min, high priority)
07:10 — Morning walk (30 min, high priority)
07:40 — Litter box cleaning (15 min, medium priority)

## 🧪 Testing PawPal+

Tests live in `tests/test_pawpal.py` and cover the core domain logic end to end:

- **Task completion** — marking a task complete flips `is_completed`.
- **Pet task tracking** — adding a task to a `Pet` increases its task count.
- **Sorting correctness** — `Scheduler.sort_by_time()` returns tasks in chronological order, with unscheduled tasks pushed to the end.
- **Recurrence logic** — completing a `recurrence="daily"` task returns a new `Task` for the next day (via `Task.mark_complete()`).
- **Conflict detection** — `Scheduler.find_conflicts()` flags two tasks on the same pet scheduled at the same time.

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov
```

Sample test output:

```
======================================== test session starts ========================================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/cottonskaka/Desktop/Codepath/ai110-module2show-pawpal-starter1
configfile: pytest.ini
plugins: anyio-4.15.1
collected 5 items                                                                                   

tests/test_pawpal.py .....                                                                    [100%]

========================================= 5 passed in 0.02s =========================================
```

### Confidence Level

⭐⭐⭐⭐☆ (4/5) — All 5 tests pass, covering task completion, pet task tracking, chronological sorting, daily recurrence, and same-time conflict detection. Confidence isn't a full 5 stars because several edge cases discussed during development (midnight rollover in `generate_schedule`, double-completing a recurring task, unknown priority strings, exact-boundary `available_minutes`) are understood but not yet covered by tests.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | `sort_by_priority()` orders tasks high → low priority, then shortest → longest duration, and is what `generate_schedule()` uses to build the day's plan. `sort_by_time()` orders tasks by `scheduled_time` ascending, pushing any unscheduled (`None`) tasks to the end — useful for re-sorting a schedule after manual reschedules. |
| Filtering | `Owner.filter_tasks(is_completed=None, pet_name=None)` | Returns tasks matching either or both of: completion status, and/or a specific pet's name. Both filters are optional and combine with AND logic, so you can ask for e.g. "Mochi's incomplete tasks" in one call. |
| Conflict handling | `Scheduler.check_conflict()`, `Scheduler.find_conflicts()`, `Scheduler.explain_conflicts()` | Conflicts are true overlapping time *ranges* (start + duration), not just identical start times, so two tasks that merely abut don't falsely flag. `check_conflict(task, other_tasks)` is a lightweight, single-task check — it scans once, stops at the first overlap, and returns a warning string (or `None`) instead of raising, so it's safe to call right after any `reschedule()`. `find_conflicts(tasks)` is the full audit — it sorts once by start time and returns every overlapping pair across all pets, same-pet or cross-pet, skipping completed tasks to avoid false positives from a finished recurring task's own next-occurrence clone. `explain_conflicts(owner, conflicts)` renders those pairs as readable lines naming each task's pet. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.complete_task()` | When a task with `recurrence="daily"` or `"weekly"` is completed, `Task.mark_complete()` marks it done and returns a new `Task` for the next occurrence (fresh id, `due_date` advanced by 1 day or 7 days). Since a `Task` has no reference back to its `Pet`, `Scheduler.complete_task(owner, task_id)` is the entry point that finds the task across the owner's pets, calls `mark_complete()`, and appends the returned next-occurrence task back onto that same pet's task list. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
