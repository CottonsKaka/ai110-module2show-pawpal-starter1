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

## ✨ Features

- **Priority-based daily scheduling** — `Scheduler.generate_schedule()` fills the day by priority (high → low), then earliest-scheduled-first, stopping once the day's time constraints are met.
- **Sorting by time** — `Scheduler.sort_by_time()` re-orders any task list chronologically by `scheduled_time`, pushing unscheduled tasks to the end.
- **Sorting by priority, then time** — `Scheduler.sort_by_priority()` orders tasks high → low priority, then by `scheduled_time` (earliest first, unscheduled last), then shortest → longest duration as a final tiebreaker.
- **Task filtering** — `Owner.filter_tasks()` narrows the full task list by completion status and/or pet name.
- **Conflict warnings** — `Scheduler.check_conflict()` (single task) and `Scheduler.find_conflicts()` (full audit) detect true overlapping time *ranges*, not just identical start times, within a pet or across pets; `explain_conflicts()` renders them as readable warnings.
- **Daily/weekly recurrence** — `Task.mark_complete()` and `Scheduler.complete_task()` automatically generate the next occurrence of a recurring task when it's marked done.
- **Next-available-slot finder** — `Scheduler.find_next_available_slot()` scans a task list and returns the earliest open gap (of a requested length, optionally after a given time) that doesn't overlap anything already scheduled.
- **Recurrence conflict auto-resolve** — `Scheduler.resolve_recurrence_conflict()` builds on the slot finder: if a freshly-recurring task would land on top of something else, it's automatically bumped to the next open slot instead of silently overlapping.
- **JSON persistence** — `Owner.save_to_json()` / `Owner.load_from_json()` (backed by `to_dict()`/`from_dict()` on `Task`, `Pet`, and `Owner`) let the whole system — every pet and every task — survive between runs.
- **Formatted output** — emoji priority/task-type labels and a `tabulate`-rendered CLI table (`formatting.py`, used by `main.py`), plus color-coded priority badges in the Streamlit UI.

## Implementation Summary

The system is four classes in `pawpal_system.py`. `Task` represents a single piece of care work — a description, duration, priority, and scheduled time. `Pet` holds a pet's identity and health info and owns its own list of `Task`s. `Owner` holds a list of `Pet`s and can flatten every pet's tasks into one list with `get_all_tasks()`. `Scheduler` is the only class with ordering logic: it reads tasks exclusively through `Owner.get_all_tasks()` (never from a single `Pet` directly, so scheduling always spans every pet an owner has), ranks them by priority and duration, and assigns each one a time slot within the day's constraints — the result can be rendered as a readable timeline with `explain_plan()`. `Task`, `Pet`, and `Owner` also know how to turn themselves into plain dicts (`to_dict()`/`from_dict()`), which is what makes `Owner.save_to_json()`/`load_from_json()` possible. A separate `formatting.py` module keeps emoji/color presentation logic out of the domain model entirely. `main.py` demonstrates the whole flow end to end: build an `Owner` with two `Pet`s, add tasks to each, print the generated schedule, and exercise every stretch feature (slot-finding, recurrence conflict resolution, persistence).

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

```
Today's Schedule
=================
07:00 — Vet checkup (20 min, high priority)
07:20 — Morning walk (30 min, high priority)
07:50 — Feeding (10 min, high priority)
08:00 — Litter box cleaning (15 min, medium priority)
08:15 — Evening walk (20 min, medium priority)
```

## 🧪 Testing PawPal+

Tests live in `tests/test_pawpal.py` and cover the core domain logic end to end:

- **Task completion** — marking a task complete flips `is_completed`.
- **Pet task tracking** — adding a task to a `Pet` increases its task count.
- **Sorting correctness** — `Scheduler.sort_by_time()` returns tasks in chronological order, with unscheduled tasks pushed to the end.
- **Priority sorting with tiebreak** — `Scheduler.sort_by_priority()` orders by priority first, then by `scheduled_time`, even when a lower-priority task is scheduled earlier.
- **Recurrence logic** — completing a `recurrence="daily"` task returns a new `Task` for the next day (via `Task.mark_complete()`).
- **Conflict detection** — `Scheduler.find_conflicts()` flags two tasks on the same pet scheduled at the same time.
- **Next-available-slot finder** — `Scheduler.find_next_available_slot()` returns the correct gap between two scheduled tasks, and `None` when the day is already full.
- **Recurrence conflict auto-resolve** — `Scheduler.resolve_recurrence_conflict()` moves a task off of a real overlap and confirms the move actually resolved the conflict.
- **Persistence round-trip** — `Owner.save_to_json()` followed by `Owner.load_from_json()` reproduces the same owner, pet, and task data (including dates and times).

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
python -m pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/cottonskaka/Desktop/Codepath/ai110-module2show-pawpal-starter1
configfile: pytest.ini
plugins: anyio-4.15.1
collected 10 items

tests/test_pawpal.py ..........                                          [100%]

============================== 10 passed in 0.01s ==============================
```

### Confidence Level

⭐⭐⭐⭐☆ (4/5) — All 10 tests pass, covering task completion, pet task tracking, chronological and priority+time sorting, daily recurrence, conflict detection, slot-finding, recurrence conflict auto-resolve, and JSON persistence. Confidence isn't a full 5 stars because a few edge cases discussed during development (midnight rollover in `generate_schedule`/`find_next_available_slot`, double-completing a recurring task, unknown priority strings, exact-boundary `available_minutes`) are understood but not yet covered by tests.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `Scheduler.sort_by_time()` | `sort_by_priority()` orders tasks high → low priority, then shortest → longest duration, and is what `generate_schedule()` uses to build the day's plan. `sort_by_time()` orders tasks by `scheduled_time` ascending, pushing any unscheduled (`None`) tasks to the end — useful for re-sorting a schedule after manual reschedules. |
| Filtering | `Owner.filter_tasks(is_completed=None, pet_name=None)` | Returns tasks matching either or both of: completion status, and/or a specific pet's name. Both filters are optional and combine with AND logic, so you can ask for e.g. "Mochi's incomplete tasks" in one call. |
| Conflict handling | `Scheduler.check_conflict()`, `Scheduler.find_conflicts()`, `Scheduler.explain_conflicts()` | Conflicts are true overlapping time *ranges* (start + duration), not just identical start times, so two tasks that merely abut don't falsely flag. `check_conflict(task, other_tasks)` is a lightweight, single-task check — it scans once, stops at the first overlap, and returns a warning string (or `None`) instead of raising, so it's safe to call right after any `reschedule()`. `find_conflicts(tasks)` is the full audit — it sorts once by start time and returns every overlapping pair across all pets, same-pet or cross-pet, skipping completed tasks to avoid false positives from a finished recurring task's own next-occurrence clone. `explain_conflicts(owner, conflicts)` renders those pairs as readable lines naming each task's pet. |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.complete_task()` | When a task with `recurrence="daily"` or `"weekly"` is completed, `Task.mark_complete()` marks it done and returns a new `Task` for the next occurrence (fresh id, `due_date` advanced by 1 day or 7 days). Since a `Task` has no reference back to its `Pet`, `Scheduler.complete_task(owner, task_id)` is the entry point that finds the task across the owner's pets, calls `mark_complete()`, and appends the returned next-occurrence task back onto that same pet's task list. |
| Next-available-slot finder | `Scheduler.find_next_available_slot(tasks, duration_minutes, day_start, day_end, after)` | Walks the already-scheduled, incomplete tasks in time order and checks each gap (before the first task, between two tasks, after the last one) against the requested duration. `after` lets a caller say "find me a slot after 2pm" without pre-filtering the task list. Returns `None` if nothing in `[day_start, day_end]` is big enough. |
| Recurrence conflict auto-resolve | `Scheduler.resolve_recurrence_conflict(owner, task, day_start, day_end)` | Composes `check_conflict()` + `find_next_available_slot()`: if a task (typically a freshly-created recurring next-occurrence) overlaps something else the owner has scheduled, it's moved to the next open slot at or after its current time. Returns whether a move happened, so a caller can tell the user their recurring task shifted. |

## 💾 Data Persistence

**Workflow:** on startup, `app.py` checks whether `data.json` exists next to it. If it does, the owner (every pet, every task) is loaded straight from it via `Owner.load_from_json()`; if not, a fresh `Owner` is created. From then on, every mutating action — adding a pet, adding a task, generating a schedule — calls a small `persist()` helper that writes the current owner back out with `Owner.save_to_json()`. The net effect: closing the browser tab and reopening the app (or restarting `streamlit run`) brings everything back exactly as it was.

**Serialization approach:** `Task`, `Pet`, and `Owner` each implement `to_dict()`/`from_dict()` by hand rather than pulling in a library like `marshmallow`. The only field types that aren't natively JSON-serializable are `datetime.time` and `datetime.date` (on `Task.scheduled_time` and `Task.due_date`), so `to_dict()` converts those to ISO-format strings and `from_dict()` parses them back with `time.fromisoformat()` / `date.fromisoformat()`. Everything else (strings, ints, floats, bools, nested dicts/lists) round-trips through `json.dump`/`json.load` unchanged. A hand-written conversion was simpler than adding a schema library for a system with only three classes to serialize.

**Files modified:** `pawpal_system.py` (added `to_dict()`/`from_dict()` to `Task`, `Pet`, `Owner`, plus `Owner.save_to_json()`/`load_from_json()`), `app.py` (load-on-startup + `persist()` calls after each mutation), `main.py` (demonstrates a save/load round trip), `.gitignore` (excludes the generated `data.json` from version control), `tests/test_pawpal.py` (round-trip test).

## 🎨 Professional UI & Output Formatting

Presentation logic (emojis, colors, table rows) lives in its own `formatting.py` module rather than inside `pawpal_system.py` — the domain classes stay UI-agnostic, and only `main.py`/`app.py` import `formatting`.

- **Priority labels** — `formatting.priority_label()` renders `🔴 High` / `🟡 Medium` / `🟢 Low`; `formatting.priority_color()` gives a matching hex color for UI elements that support it.
- **Task-type icons** — `formatting.task_type_icon()` maps each task type to an emoji (🚶 walk, 🍖 feeding, 🎾 outdoor_activity, ✂️ grooming, 💊 medication, 🩺 vet, 🧸 play), with a generic 📋 fallback for anything else.
- **Status labels** — `formatting.status_label()` renders `✅ Done` / `⏳ Pending`.
- **CLI tables** — `main.py` uses the [`tabulate`](https://pypi.org/project/tabulate/) library to render the whole day's schedule as an aligned table, with `formatting.task_to_row()` building each row.
- **Streamlit UI** — `app.py`'s task tables (the full task list, the generated schedule) use the same `formatting.task_to_row()` helper, so the web UI and the CLI show identical emoji/priority formatting.

## 📸 Demo Walkthrough

### UI features (`app.py`)

- Enter the owner's name and add one or more pets (species, breed, age, weight, height), shown in a pet table.
- Add care tasks to a selected pet (description, task type, duration, priority).
- View every task across all pets at once, toggle sorting (Priority vs. Scheduled time), and filter by pet and/or completion status.
- See an inline conflict warning as soon as two visible tasks' time ranges overlap.
- Click "Generate schedule" to build the day's plan, with task-count / total-minutes metrics and a conflict-free confirmation (or warning) for the generated plan.
- Search for the next open time slot of a given length with "Find Next Available Slot," without manually scanning the task list.
- Data persists automatically: adding a pet/task or generating a schedule saves to `data.json`, which is reloaded the next time the app starts.

### Example workflow

1. Enter the owner's name (e.g., "Jordan") and add a pet, e.g., Mochi the Shiba Inu.
2. Add tasks for Mochi: "Morning walk" (30 min, high priority) and "Feeding" (10 min, high priority).
3. Open "All tasks" and sort by Priority — both tasks show in priority order with no conflicts detected.
4. Click "Generate schedule" to see today's plan, starting at 7:00 AM, with Mochi's high-priority tasks scheduled first.

### Key Scheduler behaviors shown

- **Sorting** — switching "Sort by" between Priority and Scheduled time re-orders the same task list via `sort_by_priority()` / `sort_by_time()`. Priority sorting now breaks ties by scheduled time (Challenge 3), not duration.
- **Conflict warnings** — scheduling two tasks whose time ranges overlap (same pet or different pets) immediately surfaces a warning via `find_conflicts()` / `explain_conflicts()`.
- **Daily recurrence** — completing a task with `recurrence="daily"` creates its next occurrence automatically via `complete_task()`.
- **Next-available-slot finder** — `find_next_available_slot()` locates the first open gap of a requested length, demonstrated below finding 09:00 open after the morning tasks.
- **Recurrence conflict auto-resolve** — when a recurring task's next occurrence lands on an already-booked time, `resolve_recurrence_conflict()` bumps it to the next open slot automatically.
- **Persistence** — `save_to_json()` / `load_from_json()` round-trip the entire owner (pets, tasks, completion status, due dates) through `data.json`.

### Sample CLI output (`python main.py`)

This output demonstrates the enhanced priority → time scheduling logic (Challenge 3): among the three `high`-priority tasks, the one with the earliest original `scheduled_time` (Vet checkup, 06:45) is placed first, ahead of Morning walk (07:30) and Feeding (08:15) — priority still wins over everything, but time now breaks the tie instead of duration.

```
Today's Schedule
=================
07:00 — Vet checkup (20 min, high priority)
07:20 — Morning walk (30 min, high priority)
07:50 — Feeding (10 min, high priority)
08:00 — Litter box cleaning (15 min, medium priority)
08:15 — Evening walk (20 min, medium priority)

Recurring Task Rollover
========================
Completed 'Litter box cleaning' -> created next occurrence (due 2026-10-21, task_id=aacc83a3)

All Tasks Sorted by Time
=========================
07:00 — Vet checkup (20 min, high priority)
07:20 — Morning walk (30 min, high priority)
07:50 — Feeding (10 min, high priority)
08:00 — Litter box cleaning (15 min, medium priority)
08:00 — Litter box cleaning (15 min, medium priority)
08:15 — Evening walk (20 min, medium priority)

Incomplete Tasks Only
======================
07:50 — Feeding (10 min, high priority)
07:20 — Morning walk (30 min, high priority)
08:15 — Evening walk (20 min, medium priority)
07:00 — Vet checkup (20 min, high priority)
08:00 — Litter box cleaning (15 min, medium priority)

Completed Tasks Only
======================
08:00 — Litter box cleaning (15 min, medium priority)

Mochi's Tasks Only
====================
07:50 — Feeding (10 min, high priority)
07:20 — Morning walk (30 min, high priority)
08:15 — Evening walk (20 min, medium priority)

Lightweight Conflict Check (single task)
===========================================
Warning: 'Evening walk' at 07:15 conflicts with 'Morning walk' at 07:20.

Full Conflict Audit (entire schedule)
========================================
07:00-07:15 overlap: 'Vet checkup' (Luna) vs 'Evening walk' (Mochi)
07:15-07:20 overlap: 'Evening walk' (Mochi) vs 'Morning walk' (Mochi)

Same-Time Conflict Check
==========================
Warning: 'Nail trim' at 10:00 conflicts with 'Playtime' at 10:00.

Formatted Schedule (emojis + table)
======================================
time    pet    task                    duration    priority    status
------  -----  ----------------------  ----------  ----------  ---------
07:00   Luna   🩺 Vet checkup           20 min      🔴 High      ⏳ Pending
07:15   Mochi  🚶 Evening walk          20 min      🟡 Medium    ⏳ Pending
07:20   Mochi  🚶 Morning walk          30 min      🔴 High      ⏳ Pending
07:50   Mochi  🍖 Feeding               10 min      🔴 High      ⏳ Pending
08:00   Luna   ✂️ Litter box cleaning  15 min      🟡 Medium    ✅ Done
08:00   Luna   ✂️ Litter box cleaning  15 min      🟡 Medium    ⏳ Pending
10:00   Mochi  ✂️ Nail trim            15 min      🟢 Low       ⏳ Pending
10:00   Luna   🧸 Playtime              15 min      🟢 Low       ⏳ Pending

Find Next Available Slot
===========================
Next open 15-minute slot after 09:00: 09:00

Recurrence Conflict Auto-Resolve
===================================
Next occurrence inherited the same time: 11:00
Warning: 'Evening medication' at 11:00 conflicts with 'Grooming session' at 11:00.
Auto-resolved: moved to 11:30 to avoid the conflict.

Persistence (save/load)
==========================
Saved current owner, pets, and tasks to data.json
Reloaded owner 'Jordan' with 2 pet(s) and 11 task(s) from data.json
```
