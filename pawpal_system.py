from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from uuid import uuid4


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    weight: float
    height: float
    health_stats: dict = field(default_factory=dict)
    pet_id: str = field(default_factory=lambda: str(uuid4()))

    def get_info(self) -> dict:
        pass

    def edit_info(self, **updates) -> None:
        pass

    def add_health_record(self, record: dict) -> None:
        pass


@dataclass
class Task:
    pet_id: str
    title: str
    task_type: str
    duration_minutes: int
    priority: str
    scheduled_time: time | None = None
    recurrence: str = "none"
    is_completed: bool = False
    task_id: str = field(default_factory=lambda: str(uuid4()))

    def mark_complete(self) -> None:
        pass

    def edit_task(self, **updates) -> None:
        pass

    def reschedule(self, new_time: time) -> None:
        pass


@dataclass
class Owner:
    name: str
    contact_info: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    owner_id: str = field(default_factory=lambda: str(uuid4()))

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: str) -> None:
        pass

    def get_pet(self, pet_id: str) -> Pet | None:
        pass


class Scheduler:
    def __init__(self, constraints: dict | None = None) -> None:
        self.constraints = constraints or {}

    def generate_schedule(self, pet: Pet, tasks: list[Task], constraints: dict) -> list[Task]:
        pass

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        pass

    def explain_plan(self, schedule: list[Task]) -> str:
        pass
