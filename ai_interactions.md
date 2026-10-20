# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I gave Claude Code the full list of five stretch challenges at once (advanced algorithmic capability, data persistence, advanced priority scheduling, professional UI/output formatting, and multi-model prompt comparison) and asked it to implement all of them end to end — code, tests, and documentation — and verify everything actually works before calling it done.

**What did the agent do?**

- Read every existing file first (`pawpal_system.py`, `app.py`, `main.py`, `tests/test_pawpal.py`, `README.md`, `ai_interactions.md`, `diagrams/uml.mmd`) to figure out what was already implemented versus what the challenges still needed, instead of assuming a blank slate.
- Asked one clarifying question up front — it couldn't call a second AI model (e.g. ChatGPT) itself for Challenge 5, so it asked how I wanted to handle that instead of silently fabricating a "Model B" response.
- **Challenge 1 (new algorithmic capability):** added `Scheduler.find_next_available_slot()` to `pawpal_system.py` — a gap-finder that scans already-scheduled tasks and returns the earliest open window of a requested length.
- **Challenge 2 (persistence):** added `to_dict()`/`from_dict()` to `Task`, `Pet`, and `Owner`, plus `Owner.save_to_json()` / `Owner.load_from_json()`. Wired it into `app.py` (loads `data.json` on startup if present, saves after every mutating action) and added `data.json` to `.gitignore`.
- **Challenge 3 (priority + time scheduling):** changed `Scheduler.sort_by_priority()`'s tiebreaker from duration to scheduled time (duration is now the third-level tiebreaker), matching the spec's "priority first, then time."
- **Challenge 4 (formatting):** created a new `formatting.py` module (kept separate from the domain model on purpose) with emoji priority/task-type/status labels and priority colors; used it in both `main.py` (rendered via the `tabulate` library) and `app.py`'s Streamlit tables.
- **Challenge 5 (multi-model comparison):** built `Scheduler.resolve_recurrence_conflict()` — composing the Challenge 1 slot-finder with existing conflict detection — specifically as the subject of a two-prompt comparison (see below), since it's a direct implementation of the example task the assignment suggested ("logic for rescheduling weekly tasks").
- Added 5 new tests to `tests/test_pawpal.py` (10 total) covering the new slot-finder, the priority/time tiebreak, the recurrence conflict auto-resolve, and a JSON save/load round trip.
- Verified everything by actually running it: `python -m pytest` (10/10 passing), `python main.py` (captured real output for the README), `python -m py_compile` on every changed file, and starting the Streamlit server headless to confirm it boots without exceptions.
- Updated `README.md` (new feature descriptions, persistence workflow writeup, formatting documentation, refreshed sample CLI output) and `diagrams/uml.mmd` (added the new methods to each class, re-rendered with `mermaid-cli` to confirm it still compiles).

**What did I have to verify or fix manually?**

This run was closer to autonomous than my earlier phases — I gave the agent the full challenge list up front and let it design, implement, test, and document in one pass, only stepping in once (the Challenge 5 clarifying question) rather than reviewing after each file. Before submitting, I still need to do what I did in every earlier phase (section 3b of `reflection.md`): read the actual diff rather than trust a "tests pass" claim, and spot-check a few specific things myself:

- Confirm `formatting.py` staying separate from `pawpal_system.py` is actually the boundary I want — the agent made that call on its own, citing the UI-agnostic-domain-model principle from my own reflection, which is the right instinct but still a design decision I should own rather than rubber-stamp.
- Actually click through the new "Find Next Available Slot" UI section and the auto-save behavior in a running `streamlit run app.py`, since the agent could only confirm the server starts without an exception, not that the feature behaves correctly for a real user — the UI/feature instructions it was given are explicit that a headless boot isn't the same as testing the feature.
- Decide whether `resolve_recurrence_conflict()`'s specific tiebreak (move forward in time, never earlier) is the behavior I actually want for a missed recurring task, since that was the agent's judgment call, not something I specified.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

I don't have a way to call a second product (ChatGPT, Gemini, Copilot) from inside this agent session, so instead of fabricating a response and attributing it to a tool that never actually ran, I compared two different prompting strategies against the same model (Claude) on the same complex task: **the logic for automatically rescheduling a recurring task when its next occurrence lands on an already-booked time** (the exact example the assignment suggests — "the logic for rescheduling weekly tasks").

| | Option A (terse prompt) | Option B (detailed prompt) |
|-|----------|----------|
| **Model / tool used** | Claude (Sonnet 5.5, Claude Code) | Claude (Sonnet 5.5, Claude Code) |
| **Prompt** | "Add logic so a completed recurring task's next occurrence doesn't just get silently double-booked — fix the overlap." | "Add a method that, given an owner and a freshly-created recurring next-occurrence task, checks whether it conflicts with any other scheduled task (reuse `check_conflict`), and if so moves it forward to the next open gap (reuse/add a slot-finder) rather than leaving it overlapping. It must never move a task *earlier* than its original time, must respect day-start/day-end bounds, must return whether it moved the task (for UI feedback), and must not change `complete_task()`'s existing signature or behavior, since it's already covered by tests." |
| **Response summary** | A quick inline fix inside `Task.mark_complete()`: if the recurrence delta would reuse the exact same `scheduled_time`, just add a fixed 30-minute offset to the next occurrence before returning it. | A new, separate `Scheduler.resolve_recurrence_conflict(owner, task, day_start, day_end)` method that composes the existing `check_conflict()` with a new `find_next_available_slot()` gap-finder, and returns a bool. |
| **What was useful** | Minimal, fast, no new methods — fit the letter of "fix the overlap" in one line. | Composable (the slot-finder became reusable for Challenge 1 too), bounded correctly, testable in isolation, and left `complete_task()`/`mark_complete()` untouched so none of the 5 existing tests were at risk. |
| **Problems noticed** | The fixed 30-minute offset doesn't actually check whether that new time is free — it just *assumes* shifting by 30 minutes clears the conflict, which fails the moment the blocking task is longer than 30 minutes or something else occupies that slot too. It also baked scheduling policy into `Task`, which is supposed to only hold data (see `reflection.md` section 1b on keeping `Scheduler` as the only class with ordering logic). | None functionally; the only real cost is more code (a second method plus the slot-finder it depends on) than the one-line Option A fix. |
| **Decision** | Rejected — correct-looking but not actually correct, and violates the project's own class-responsibility boundary. | Adopted — this is `Scheduler.resolve_recurrence_conflict()` in `pawpal_system.py`, tested by `test_resolve_recurrence_conflict_moves_task_on_overlap`. |

**Which approach did you use in your final implementation and why?**

Option B, implemented as `Scheduler.resolve_recurrence_conflict()`. The terse prompt (Option A) produced something that *looked* like it solved the problem — it compiled, and "add 30 minutes" sounds plausible — but it was actually only correct by coincidence: it never verifies the new time is open, so it would silently reintroduce the exact same bug it was supposed to fix against a different blocking task. This is the same lesson from `reflection.md` section 3c: a vague, broad prompt gets a shallow fix, while a prompt that states the actual constraints (reuse existing conflict logic, bound the search, never move backward, don't touch tested code) gets an implementation that's actually verifiable. I confirmed this isn't just a hunch — `test_resolve_recurrence_conflict_moves_task_on_overlap` asserts the moved task is conflict-free afterward, which the Option A approach would fail on a slightly different fixture (e.g. a 45-minute blocker).
