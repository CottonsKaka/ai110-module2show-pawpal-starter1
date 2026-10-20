# PawPal+ Project Reflection

## 1. System Design

**App requirements**

PawPal+ should be able to:
- Add a new pet
- Retrieve a pet's full information (breed, health statistics, etc.)
- Edit a pet's information
- Schedule feeding time, walk time, and other outdoor activities
- Track all tasks needed for a pet's care and wellbeing

**a. Initial design**

- Briefly describe your initial UML design.

  The design has four main components: `Owner`, `Pet`, `Task`, and `Scheduler`. An `Owner` manages one or more `Pet`s, each `Pet` has a set of `Task`s it needs done, and `Scheduler` takes those tasks plus constraints (time available, priority, owner preferences) and produces an ordered daily plan.

  | Class | Responsibility | Key attributes | Key methods |
  |---|---|---|---|
  | `Owner` | Represents the pet owner and the pets they manage | `name`, `contact_info`, `pets` (list of `Pet`), `preferences` | `add_pet()`, `remove_pet()`, `get_pet()` |
  | `Pet` | Stores a single pet's identity and health info | `name`, `species`, `breed`, `age`, `weight`, `height`, `health_stats` (vaccinations, conditions, vet notes) | `get_info()`, `edit_info()`, `add_health_record()` |
  | `Task` | Represents one task a pet needs (feeding, walk, outdoor activity, grooming, meds, etc.) | `title`, `task_type`, `duration_minutes`, `priority`, `scheduled_time`, `recurrence`, `is_completed`, `pet` (reference) | `mark_complete()`, `edit_task()`, `reschedule()` |
  | `Scheduler` | Builds and holds a day's plan from a pet's tasks and constraints | `constraints` (time available, owner preferences) | `generate_schedule()`, `sort_by_priority()`, `explain_plan()` |

- What classes did you include, and what responsibilities did you assign to each?

  `Owner` and `Pet` handle identity and data — adding, editing, and retrieving pet info. `Task` represents a unit of care work, including when it's scheduled for. `Scheduler` owns the logic of turning a pool of tasks into an ordered daily plan, respecting time constraints and priority, and can explain why it chose that order. Keeping scheduling logic in its own class means it can change later without touching pet or task data.
    

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

  Yes. An AI code review of the class skeleton flagged a missing relationship and an ambiguous attribute, and I made two changes in response:

  1. **Gave `Pet` ownership of its tasks** — added a `tasks` list to `Pet` along with `add_task()`, `get_tasks()`, and `remove_task()`. Originally `Task` only stored a `pet_id` back-reference, but no class actually held the collection of a pet's tasks, so `Scheduler.generate_schedule()` had no way to get a pet's tasks without extra bookkeeping living outside the model, in `app.py`. This also means removing a pet now naturally removes its tasks instead of needing separate cascade-delete logic.
  2. **Made `Scheduler.generate_schedule()`'s `constraints` parameter optional**, falling back to the instance's `self.constraints` when omitted. Previously `constraints` existed both as a constructor attribute and a required method parameter with no stated precedence between them, so it was unclear which one a caller should trust.

  Still to decide before implementing the scheduling logic: whether `generate_schedule()` mutates a task's `scheduled_time` in place or returns new scheduled copies.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

  `Scheduler` considers three things: each task's `priority` (high/medium/low), its `duration_minutes`, and two constraints passed in at schedule time — a `start_time` for the day and an optional `available_minutes` cap on the total time budget. `generate_schedule()` sorts by priority first, duration second, then walks that order filling the day from `start_time` and skipping any task that would push past `available_minutes`.

  Priority mattered most to me because of what this app is actually for: missing a high-priority task like medication or feeding is a real-world problem for a pet, while a low-priority task like a nail trim slipping to tomorrow isn't. Time constraints come second — they're what make the schedule realistic instead of an idealized list, since an owner only has so many minutes before work or school. Duration is the tiebreaker rather than a primary constraint, so that if two tasks share a priority, the shorter one goes first and more tasks have a chance to fit before the time budget runs out.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

  `generate_schedule()` packs tasks greedily: it sorts all tasks by priority (then duration) once, then walks that fixed order, placing each task in the next open slot and simply skipping any task that no longer fits in the remaining `available_minutes` — it never looks ahead to see whether a shorter, lower-priority task later in the list would fit the leftover gap. That's a simple, fast algorithm (one sort plus one linear pass), but it isn't optimal: a tight time budget can leave a few minutes of unused slack that a true bin-packing approach would have filled.

  I think that tradeoff is reasonable for this app. A pet owner's daily task list is small — a handful of tasks per pet — so the gap between "optimal" and "greedy" packing is at most a few minutes, not a meaningfully different schedule. Implementing real bin-packing would add noticeable complexity for a marginal time-utilization gain, and it would also make the output less predictable to the person reading it: a strictly priority-ordered plan ("highest priority goes first, always") is easier for an owner to trust at a glance than one that's been reshuffled purely to minimize idle time.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

  I used Claude Code across the whole design-to-implementation pipeline: brainstorming the class breakdown from my feature list, drafting the Mermaid UML, generating the Python class skeletons from that UML, reviewing the skeleton for structural gaps, fleshing out the method bodies, writing a demo script (`main.py`) and two unit tests, and adding docstrings/documentation. The most useful prompts were the narrow, specific ones — "do you notice any missing relationships or potential logic bottlenecks" against the actual skeleton file got far more actionable feedback than a generic "check my code" would have, because it was scoped to structure rather than style.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

  Two moments stand out. First, the AI's initial brainstorm proposed five classes, including a separate `Schedule` class to hold the daily plan. I rejected that and said the real components should be just `Owner`, `Pet`, `Task`, and `Scheduler` — so the design was redone with `Scheduler` building *and* holding the plan itself, rather than handing it off to a fifth class.

  Second, after the skeleton was fleshed out, the `Scheduler` took a single `Pet` and its task list as arguments (`generate_schedule(pet, tasks, constraints)`). That design would only ever schedule one pet at a time, which doesn't satisfy a multi-pet system. I rejected that signature and had it rebuilt so `Scheduler` takes an `Owner` and pulls tasks exclusively through `Owner.get_all_tasks()`, which flattens every pet's tasks into one list — so there's no code path left that can schedule just one pet.

  For verification I didn't just read the code — I ran it. `main.py` builds an owner with two pets and tasks on each, and running it confirmed the printed "Today's Schedule" actually interleaves tasks from both pets by priority rather than grouping them by pet. I also ran the test suite (`pytest`) and caught a real bug that way: the tests passed under `python -m pytest` but failed under the plain `pytest` command the README documents, because the project root wasn't being added to `sys.path`. Actually running the documented command instead of trusting that "tests pass" was what surfaced it; the fix was a `pytest.ini` with `pythonpath = .`.

**c. AI Strategy**

- Which AI coding assistant features were most effective for building your scheduler?

  Two habits did most of the work. First, verifying instead of trusting: rather than accepting a diff or a "this should work" claim, I had the assistant actually execute things — run `main.py` and `pytest`, render the Mermaid UML through `mermaid-cli` to confirm it compiled before I pasted it anywhere, recompile after every edit to `pawpal_system.py`. That caught real problems (the `pytest.ini` path bug above) that reading the code alone wouldn't have. Second, narrow and scoped prompts beat broad ones — asking it to review one specific file for "missing relationships or logic bottlenecks" surfaced the `Pet.tasks` gap and the ambiguous `constraints` parameter; a generic "review my code" pass earlier in the project hadn't caught either.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

  The AI's first-pass brainstorm proposed five classes, splitting the daily plan out into its own `Schedule` class alongside `Scheduler`. I rejected that — it would have meant two classes jointly responsible for "what the plan is," with no clear line dividing the logic in `Scheduler` from the data in `Schedule`. I kept the design at four classes instead, with `Scheduler` both building and holding the plan (`generate_schedule()` returns the ordered task list directly, and `explain_plan()` renders whatever list it's given). That keeps the plan as plain data (a `list[Task]`) rather than inventing a bespoke container type for it.

- How did using separate chat sessions for different phases help you stay organized?

  Starting a fresh session for each phase — UML/design, skeleton generation, core implementation, then sorting/filtering/conflict logic, then tests — kept each session's context limited to the one thing it was reviewing. That made it easy to look at one commit's diff (`111ad37` skeletons, `9a358ac` core implementation, `93005bf` sorting/filtering/conflicts, `54261db` tests) and know exactly which phase produced it and why, instead of untangling a single sprawling thread that mixed design debates with implementation details with test output. It also meant a bad turn in one phase (like the rejected five-class brainstorm) didn't linger in context to bias later, unrelated phases.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

  The AI is fast and reliable at the things I can specify precisely — implementing a method once its contract is clear, writing tests for a behavior I've named, running verification commands — but it isn't positioned to judge the shape of the system, because it doesn't have my intent for where boundaries should sit. Both of my rejected suggestions (the extra `Schedule` class, the single-pet `generate_schedule()` signature) were locally reasonable — they'd have worked — but each one would have quietly broken a constraint I cared about (a flat four-class design, scheduling that always spans every pet an owner has). Being the lead architect meant holding onto those constraints myself and treating every AI suggestion as a proposal to check against them, not a decision already made — while delegating the actual typing, running, and re-checking to the assistant once the shape was settled.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

  Five tests in `tests/test_pawpal.py` cover the behaviors I trust the least to just "look right" by eye: `sort_by_time()` returning tasks in true chronological order even when they're passed in out of order; `mark_complete()` both flipping `is_completed` and, for a `recurrence="daily"` task, returning a fresh next-day `Task` with the due date advanced by one day; `find_conflicts()` correctly flagging two different tasks scheduled at the identical time; and `Pet.add_task()` actually growing the pet's task list. These mattered because they're exactly the places a small logic mistake (an off-by-one in a date delta, a `<=` instead of `<` in a time comparison, forgetting to append in a list) would silently produce a wrong schedule without throwing an error — the kind of bug you'd only notice by carefully reading the output, which a test catches automatically every time.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

  I'd put myself at 4/5. All 5 tests pass, and between them they cover the behaviors I'd most expect to break silently: chronological sorting, daily recurrence, same-time conflict detection, and basic task/pet bookkeeping. It's not a 5 because I can name specific edge cases I've thought about but haven't written tests for: a schedule that runs past midnight (does `_add_minutes` wrap correctly, and does `explain_plan` still read sensibly?), completing an already-completed recurring task twice (does it create two next-occurrence tasks?), a task with a priority string outside `high`/`medium`/`low` (right now it silently sorts as weight `0` instead of raising), and a task that lands exactly on the `available_minutes` boundary. If I had more time, those four would be the next tests I'd write, roughly in that order since the midnight rollover feels most likely to actually happen to a real user.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

  The part I'm most satisfied with is how I collaborated with Claude rather than just handing the whole thing over. My process was to review each file myself first and brainstorm what I actually wanted the system to do, rather than accepting whatever came out first. After the class skeletons were generated from the UML, I went through them and realized a fair amount was wrong for what I actually wanted — the missing `Pet.tasks` relationship and the ambiguous `constraints` parameter (section 1b) are two concrete examples. Instead of just living with those gaps, I asked Claude to correct them, and then verified the fixes actually worked by testing the result (running `main.py` and the test suite) rather than assuming the correction was right because it compiled. That loop — review, brainstorm what's wrong, ask for a fix, test it — is the habit I'm proudest of, because it meant I stayed the one deciding what "correct" meant for this system instead of outsourcing that judgment.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

  I'd tackle the two gaps I already called out elsewhere in this reflection. First, the greedy packing in `generate_schedule()` (section 2b) — I'd add a pass that, after the priority-ordered walk, checks whether any skipped lower-priority task fits in whatever time is left over, instead of just stopping once a task doesn't fit. Second, I'd harden the edge cases from section 4b, especially the unvalidated priority string and the midnight-rollover case, since both could produce a silently wrong schedule rather than a visible error. Beyond logic, I'd also want the app to persist data between runs — right now everything lives in Streamlit's `session_state`, so a page refresh loses every pet and task, which isn't realistic for something meant to be used daily.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

  Keeping each class's responsibility narrow and singular paid off every time I touched this codebase. `Pet` only knows about its own identity and task list, `Owner` only aggregates pets, and `Scheduler` is the one place that knows about ordering, conflicts, and time — so when I added filtering, conflict detection, and recurrence partway through the project, each one slotted into exactly one class without rippling changes through the others. That discipline is also what made AI collaboration work well: because each class had one clear job, I could ask Claude to fix or extend one of them in isolation and actually verify the result, instead of having to reason about a tangle of responsibilities every time. The lesson I'm taking forward is that a clean boundary between classes isn't just a design nicety — it's what makes a system reviewable, testable, and safe to hand pieces of to an AI collaborator.
