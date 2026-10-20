"""
Presentation helpers shared by main.py (CLI) and app.py (Streamlit).

Kept separate from pawpal_system.py on purpose: Task/Pet/Owner/Scheduler stay
UI-agnostic, and only this module knows about emojis, colors, or table layout.
"""

from __future__ import annotations

from pawpal_system import Task

PRIORITY_LABELS = {
    "high": "\U0001f534 High",
    "medium": "\U0001f7e1 Medium",
    "low": "\U0001f7e2 Low",
}

PRIORITY_COLORS = {
    "high": "#e03131",
    "medium": "#f2994a",
    "low": "#2f9e44",
}

TASK_TYPE_ICONS = {
    "walk": "\U0001f6b6",
    "feeding": "\U0001f356",
    "outdoor_activity": "\U0001f3be",
    "grooming": "✂️",
    "medication": "\U0001f48a",
    "vet": "\U0001fa7a",
    "play": "\U0001f9f8",
}

STATUS_ICONS = {True: "✅ Done", False: "⏳ Pending"}


def priority_label(priority: str) -> str:
    """Return a priority as an emoji-prefixed label, e.g. '\U0001f534 High'."""
    return PRIORITY_LABELS.get(priority, priority.title())


def priority_color(priority: str) -> str:
    """Return a hex color for a priority, for use in colored UI elements."""
    return PRIORITY_COLORS.get(priority, "#868e96")


def task_type_icon(task_type: str) -> str:
    """Return an emoji for a task type, or a generic fallback icon."""
    return TASK_TYPE_ICONS.get(task_type, "\U0001f4cb")


def status_label(is_completed: bool) -> str:
    """Return a completion status as an emoji-prefixed label."""
    return STATUS_ICONS[is_completed]


def task_to_row(task: Task, pet_name: str) -> dict:
    """Convert a Task into a flat dict suitable for a formatted table row."""
    time_str = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "unscheduled"
    return {
        "time": time_str,
        "pet": pet_name,
        "task": f"{task_type_icon(task.task_type)} {task.description}",
        "duration": f"{task.duration_minutes} min",
        "priority": priority_label(task.priority),
        "status": status_label(task.is_completed),
    }
