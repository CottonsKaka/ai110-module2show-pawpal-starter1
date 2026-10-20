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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
