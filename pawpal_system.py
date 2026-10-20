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
can render as a readable timeline.
"""

from __future__ import annotations

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
    task_id: str = field(default_factory=lambda: str(uuid4()))

    _EDITABLE_FIELDS = {"description", "task_type", "duration_minutes", "priority", "recurrence"}

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

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
        """Sort tasks by priority (high to low), then by duration (short to long)."""
        return sorted(
            tasks,
            key=lambda t: (-self._PRIORITY_WEIGHT.get(t.priority, 0), t.duration_minutes),
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
