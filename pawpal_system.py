"""
PawPal+ core domain model.

Four classes carry the system. `Task` is a single piece of care work (a
description, duration, priority, and when it's scheduled). `Pet` holds a
pet's identity/health info and owns its own list of `Task`s. `Owner` holds
a list of `Pet`s and can flatten every pet's tasks into one list via
`get_all_tasks()`. `Scheduler` is the only class with ordering logic: it
reads tasks exclusively through `Owner.get_all_tasks()` (never from a
single `Pet` directly), ranks them by priority, and assigns each one a
time slot within the day's constraints, producing a plan `explain_plan()`
can render as a readable timeline. It can also find open gaps directly
(`find_next_available_slot()`) and use that to bump a freshly-recurring
task off of a time it now conflicts with (`resolve_recurrence_conflict()`).
`Task`, `Pet`, and `Owner` each support `to_dict()`/`from_dict()`, and
`Owner.save_to_json()`/`load_from_json()` persist a whole owner's data
(pets and tasks included) to a JSON file between runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from uuid import uuid4


@dataclass
class Task:
    pet_id: str
    description: str
    task_type: str
    duration_minutes: int
    priority: str
    scheduled_time: time | None = None
    recurrence: str = "none"
    is_completed: bool = False
    due_date: date | None = None
    task_id: str = field(default_factory=lambda: str(uuid4()))

    _EDITABLE_FIELDS = {"description", "task_type", "duration_minutes", "priority", "recurrence"}
    _RECURRENCE_DELTA = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}

    def mark_complete(self) -> "Task | None":
        """Mark this task as done. If it recurs daily/weekly, return a new Task for the next occurrence."""
        self.is_completed = True
        delta = self._RECURRENCE_DELTA.get(self.recurrence)
        if delta is None:
            return None
        return Task(
            pet_id=self.pet_id,
            description=self.description,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            scheduled_time=self.scheduled_time,
            recurrence=self.recurrence,
            due_date=(self.due_date or date.today()) + delta,
        )

    def edit_task(self, **updates) -> None:
        """Update one or more editable fields on this task."""
        invalid = set(updates) - self._EDITABLE_FIELDS
        if invalid:
            raise AttributeError(f"Cannot edit fields: {', '.join(sorted(invalid))}")
        for key, value in updates.items():
            setattr(self, key, value)

    def reschedule(self, new_time: time) -> None:
        """Change this task's scheduled time."""
        self.scheduled_time = new_time

    def to_dict(self) -> dict:
        """Convert this task to a JSON-serializable dict (times/dates become ISO strings)."""
        return {
            "task_id": self.task_id,
            "pet_id": self.pet_id,
            "description": self.description,
            "task_type": self.task_type,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "recurrence": self.recurrence,
            "is_completed": self.is_completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a Task from a dict produced by to_dict()."""
        return cls(
            pet_id=data["pet_id"],
            description=data["description"],
            task_type=data["task_type"],
            duration_minutes=data["duration_minutes"],
            priority=data["priority"],
            scheduled_time=time.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else None,
            recurrence=data.get("recurrence", "none"),
            is_completed=data.get("is_completed", False),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            task_id=data["task_id"],
        )


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    weight: float
    height: float
    health_stats: dict = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)
    pet_id: str = field(default_factory=lambda: str(uuid4()))

    _EDITABLE_FIELDS = {"name", "species", "breed", "age", "weight", "height"}

    def get_info(self) -> dict:
        """Return this pet's details as a dict."""
        return {
            "pet_id": self.pet_id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "weight": self.weight,
            "height": self.height,
            "health_stats": dict(self.health_stats),
            "task_count": len(self.tasks),
        }

    def edit_info(self, **updates) -> None:
        """Update one or more editable fields on this pet."""
        invalid = set(updates) - self._EDITABLE_FIELDS
        if invalid:
            raise AttributeError(f"Cannot edit fields: {', '.join(sorted(invalid))}")
        for key, value in updates.items():
            setattr(self, key, value)

    def add_health_record(self, record: dict) -> None:
        """Append a health record (e.g. vaccination, vet visit) for this pet."""
        self.health_stats.setdefault("records", []).append(record)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def to_dict(self) -> dict:
        """Convert this pet (and its tasks) to a JSON-serializable dict."""
        return {
            "pet_id": self.pet_id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "weight": self.weight,
            "height": self.height,
            "health_stats": self.health_stats,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a Pet (and its tasks) from a dict produced by to_dict()."""
        pet = cls(
            name=data["name"],
            species=data["species"],
            breed=data["breed"],
            age=data["age"],
            weight=data["weight"],
            height=data["height"],
            health_stats=data.get("health_stats", {}),
            pet_id=data["pet_id"],
        )
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return pet


@dataclass
class Owner:
    name: str
    contact_info: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    owner_id: str = field(default_factory=lambda: str(uuid4()))

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove the pet with the given id from this owner's list of pets."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_pet(self, pet_id: str) -> Pet | None:
        """Return the pet with the given id, or None if not found."""
        return next((p for p in self.pets if p.pet_id == pet_id), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def filter_tasks(self, is_completed: bool | None = None, pet_name: str | None = None) -> list[Task]:
        """Return tasks matching the given completion status and/or pet name (either filter is optional)."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            matching_pet_ids = {p.pet_id for p in self.pets if p.name == pet_name}
            tasks = [t for t in tasks if t.pet_id in matching_pet_ids]
        if is_completed is not None:
            tasks = [t for t in tasks if t.is_completed == is_completed]
        return tasks

    def to_dict(self) -> dict:
        """Convert this owner (and every pet/task beneath it) to a JSON-serializable dict."""
        return {
            "owner_id": self.owner_id,
            "name": self.name,
            "contact_info": self.contact_info,
            "preferences": self.preferences,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an Owner (and its pets/tasks) from a dict produced by to_dict()."""
        owner = cls(
            name=data["name"],
            contact_info=data["contact_info"],
            preferences=data.get("preferences", {}),
            owner_id=data["owner_id"],
        )
        owner.pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return owner

    def save_to_json(self, path: str = "data.json") -> None:
        """Persist this owner and everything beneath it (pets, tasks) to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load an owner (and its pets/tasks) previously saved with save_to_json()."""
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)


class Scheduler:
    _PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

    def __init__(self, constraints: dict | None = None) -> None:
        """Store this scheduler's default constraints."""
        self.constraints = constraints or {}

    def generate_schedule(self, owner: Owner, constraints: dict | None = None) -> list[Task]:
        """Build an ordered daily plan from all of the owner's pets' tasks."""
        effective = constraints if constraints is not None else self.constraints
        available_minutes = effective.get("available_minutes")
        current_time = effective.get("start_time", time(8, 0))

        schedule: list[Task] = []
        minutes_used = 0
        for task in self.sort_by_priority(owner.get_all_tasks()):
            if task.is_completed:
                continue
            if available_minutes is not None and minutes_used + task.duration_minutes > available_minutes:
                continue
            task.reschedule(current_time)
            schedule.append(task)
            minutes_used += task.duration_minutes
            current_time = self._add_minutes(current_time, task.duration_minutes)

        return schedule

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority (high to low), then by scheduled time (earliest first,
        unscheduled last), then by duration (short to long) as a final tiebreaker."""
        return sorted(
            tasks,
            key=lambda t: (
                -self._PRIORITY_WEIGHT.get(t.priority, 0),
                t.scheduled_time is None,
                t.scheduled_time or time.min,
                t.duration_minutes,
            ),
        )

    def complete_task(self, owner: Owner, task_id: str) -> Task | None:
        """Mark a task complete and, if it recurs daily/weekly, add its next occurrence to the same pet.

        Returns the newly created next-occurrence Task, or None if the task doesn't recur.
        Raises ValueError if no task with the given id exists on any of the owner's pets.
        """
        for pet in owner.pets:
            for task in pet.tasks:
                if task.task_id == task_id:
                    next_task = task.mark_complete()
                    if next_task is not None:
                        pet.add_task(next_task)
                    return next_task
        raise ValueError(f"No task found with id {task_id}")

    def check_conflict(self, task: Task, other_tasks: list[Task]) -> str | None:
        """Lightweight check: does `task` overlap any task in `other_tasks`?

        Scans once, stops at the first overlap found, and returns a warning string
        instead of raising — safe to call after any reschedule() without risking
        a crash. Returns None when there's no conflict (or `task` isn't scheduled).
        """
        if task.scheduled_time is None:
            return None

        task_start, task_end = self._task_interval(task)
        for other in other_tasks:
            if other.task_id == task.task_id or other.scheduled_time is None or other.is_completed:
                continue
            other_start, other_end = self._task_interval(other)
            if task_start < other_end and other_start < task_end:
                return (
                    f"Warning: '{task.description}' at {task.scheduled_time.strftime('%H:%M')} "
                    f"conflicts with '{other.description}' at {other.scheduled_time.strftime('%H:%M')}."
                )
        return None

    def find_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return every pair of tasks whose scheduled time ranges overlap, across any pet.

        Sorts by start time once, then for each task scans forward only until a
        later task's start reaches or passes the current task's end — since the
        list is sorted, every task after that starts even later, so none of them
        can overlap either. Skips completed tasks so a finished recurring task
        never conflicts with its own next-occurrence clone.
        """
        scheduled = sorted(
            (t for t in tasks if t.scheduled_time is not None and not t.is_completed),
            key=lambda t: t.scheduled_time,
        )

        conflicts: list[tuple[Task, Task]] = []
        for i, a in enumerate(scheduled):
            _, a_end = self._task_interval(a)
            for b in scheduled[i + 1:]:
                b_start, _ = self._task_interval(b)
                if b_start >= a_end:
                    break  # sorted by start time, so no later task can overlap `a` either
                conflicts.append((a, b))
        return conflicts

    def explain_conflicts(self, owner: Owner, conflicts: list[tuple[Task, Task]]) -> str:
        """Render detected conflicts as human-readable lines, naming each task's pet."""
        if not conflicts:
            return "No scheduling conflicts detected."

        lines = []
        for a, b in conflicts:
            pet_a = owner.get_pet(a.pet_id)
            pet_b = owner.get_pet(b.pet_id)
            name_a = pet_a.name if pet_a else a.pet_id
            name_b = pet_b.name if pet_b else b.pet_id
            lines.append(
                f"{a.scheduled_time.strftime('%H:%M')}-{b.scheduled_time.strftime('%H:%M')} overlap: "
                f"'{a.description}' ({name_a}) vs '{b.description}' ({name_b})"
            )
        return "\n".join(lines)

    def find_next_available_slot(
        self,
        tasks: list[Task],
        duration_minutes: int,
        day_start: time = time(7, 0),
        day_end: time = time(21, 0),
        after: time | None = None,
    ) -> time | None:
        """Find the earliest open gap (of at least `duration_minutes`) among `tasks`.

        Walks the already-scheduled, incomplete tasks in time order and checks the
        gap before each one, then the gap after the last one, against `day_end`.
        `after` moves the search window forward (e.g. "find me a slot after 2pm")
        without needing to filter `tasks` yourself. Returns None if nothing in
        [day_start, day_end] is big enough.
        """
        today = date.today()
        cursor = after if after is not None and after > day_start else day_start
        needed = timedelta(minutes=duration_minutes)

        scheduled = sorted(
            (t for t in tasks if t.scheduled_time is not None and not t.is_completed),
            key=lambda t: t.scheduled_time,
        )
        for task in scheduled:
            task_start, task_end = self._task_interval(task)
            if task_end.time() <= cursor:
                continue  # entirely before our search window, doesn't block anything
            if task_start.time() > cursor and task_start - datetime.combine(today, cursor) >= needed:
                return cursor
            cursor = max(cursor, task_end.time())
            if cursor >= day_end:
                return None

        if datetime.combine(today, day_end) - datetime.combine(today, cursor) >= needed:
            return cursor
        return None

    def resolve_recurrence_conflict(
        self,
        owner: Owner,
        task: Task,
        day_start: time = time(7, 0),
        day_end: time = time(21, 0),
    ) -> bool:
        """If `task` (typically a freshly-created recurring next-occurrence) overlaps
        another of the owner's scheduled tasks, move it to the next open slot at or
        after its current time. Returns True if it was moved, False if it was
        already conflict-free or no open slot could be found within the day.
        """
        if task.scheduled_time is None:
            return False

        other_tasks = [t for t in owner.get_all_tasks() if t.task_id != task.task_id]
        if self.check_conflict(task, other_tasks) is None:
            return False

        slot = self.find_next_available_slot(
            other_tasks,
            task.duration_minutes,
            day_start=day_start,
            day_end=day_end,
            after=task.scheduled_time,
        )
        if slot is None:
            return False
        task.reschedule(slot)
        return True

    @staticmethod
    def _task_interval(task: Task) -> tuple[datetime, datetime]:
        """Return a task's (start, end) datetimes, derived from its scheduled time and duration."""
        start = datetime.combine(date.today(), task.scheduled_time)
        return start, start + timedelta(minutes=task.duration_minutes)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by their scheduled time (earliest first); unscheduled tasks go last."""
        return sorted(
            tasks,
            key=lambda t: (t.scheduled_time is None, t.scheduled_time or time.min),
        )

    def explain_plan(self, schedule: list[Task]) -> str:
        """Render a scheduled task list as a human-readable timeline."""
        if not schedule:
            return "No tasks were scheduled."

        lines = []
        for task in schedule:
            time_str = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "unscheduled"
            lines.append(f"{time_str} — {task.description} ({task.duration_minutes} min, {task.priority} priority)")
        return "\n".join(lines)

    @staticmethod
    def _add_minutes(start: time, minutes: int) -> time:
        """Return the time that is the given number of minutes after start."""
        return (datetime.combine(date.today(), start) + timedelta(minutes=minutes)).time()
