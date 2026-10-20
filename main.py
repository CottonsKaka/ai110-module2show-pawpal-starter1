from datetime import time

from tabulate import tabulate

import formatting
from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", contact_info="jordan@example.com")

    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5, weight=9.0, height=25.0)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks are added out of chronological order on purpose, to exercise sort_by_time().
    mochi.add_task(
        Task(
            pet_id=mochi.pet_id,
            description="Feeding",
            task_type="feeding",
            duration_minutes=10,
            priority="high",
            scheduled_time=time(8, 15),
        )
    )
    luna.add_task(
        Task(
            pet_id=luna.pet_id,
            description="Litter box cleaning",
            task_type="grooming",
            duration_minutes=15,
            priority="medium",
            scheduled_time=time(9, 0),
            recurrence="daily",
        )
    )
    mochi.add_task(
        Task(
            pet_id=mochi.pet_id,
            description="Morning walk",
            task_type="walk",
            duration_minutes=30,
            priority="high",
            scheduled_time=time(7, 30),
        )
    )
    luna.add_task(
        Task(
            pet_id=luna.pet_id,
            description="Vet checkup",
            task_type="vet",
            duration_minutes=20,
            priority="high",
            scheduled_time=time(6, 45),
        )
    )
    mochi.add_task(
        Task(
            pet_id=mochi.pet_id,
            description="Evening walk",
            task_type="walk",
            duration_minutes=20,
            priority="medium",
            scheduled_time=None,
        )
    )

    scheduler = Scheduler(constraints={"start_time": time(7, 0)})
    schedule = scheduler.generate_schedule(owner)

    print("Today's Schedule")
    print("=================")
    print(scheduler.explain_plan(schedule))

    # Complete the daily litter box task through the Scheduler so the next
    # occurrence is automatically created and added back to Luna's task list.
    litter_box_task = luna.get_tasks()[0]  # "Litter box cleaning" (recurrence="daily")
    next_occurrence = scheduler.complete_task(owner, litter_box_task.task_id)

    print("\nRecurring Task Rollover")
    print("========================")
    if next_occurrence:
        print(
            f"Completed '{litter_box_task.description}' -> created next occurrence "
            f"(due {next_occurrence.due_date}, task_id={next_occurrence.task_id[:8]})"
        )

    print("\nAll Tasks Sorted by Time")
    print("=========================")
    print(scheduler.explain_plan(scheduler.sort_by_time(owner.get_all_tasks())))

    print("\nIncomplete Tasks Only")
    print("======================")
    print(scheduler.explain_plan(owner.filter_tasks(is_completed=False)))

    print("\nCompleted Tasks Only")
    print("======================")
    print(scheduler.explain_plan(owner.filter_tasks(is_completed=True)))

    print("\nMochi's Tasks Only")
    print("====================")
    print(scheduler.explain_plan(owner.filter_tasks(pet_name="Mochi")))

    # Force an overlap to demonstrate conflict detection: reschedule Mochi's
    # "Evening walk" (20 min) to 07:15, which now overlaps both Mochi's own
    # "Morning walk" (07:30-08:00, same pet) and Luna's "Vet checkup"
    # (07:10-07:30, different pet).
    evening_walk = mochi.get_tasks()[-1]
    evening_walk.reschedule(time(7, 15))

    print("\nLightweight Conflict Check (single task)")
    print("===========================================")
    warning = scheduler.check_conflict(evening_walk, owner.get_all_tasks())
    print(warning or "No conflict detected for 'Evening walk'.")

    print("\nFull Conflict Audit (entire schedule)")
    print("========================================")
    conflicts = scheduler.find_conflicts(owner.get_all_tasks())
    print(scheduler.explain_conflicts(owner, conflicts))

    # Explicit same-time test: two different pets' tasks scheduled at the
    # identical clock time (10:00), not just overlapping durations.
    nail_trim = Task(
        pet_id=mochi.pet_id,
        description="Nail trim",
        task_type="grooming",
        duration_minutes=15,
        priority="low",
        scheduled_time=time(10, 0),
    )
    playtime = Task(
        pet_id=luna.pet_id,
        description="Playtime",
        task_type="play",
        duration_minutes=15,
        priority="low",
        scheduled_time=time(10, 0),
    )
    mochi.add_task(nail_trim)
    luna.add_task(playtime)

    print("\nSame-Time Conflict Check")
    print("==========================")
    warning = scheduler.check_conflict(nail_trim, owner.get_all_tasks())
    print(warning or "No conflict detected.")

    print("\nFormatted Schedule (emojis + table)")
    print("======================================")
    rows = [
        formatting.task_to_row(t, next(p.name for p in owner.pets if p.pet_id == t.pet_id))
        for t in scheduler.sort_by_time(owner.get_all_tasks())
    ]
    print(tabulate(rows, headers="keys", tablefmt="simple"))

    print("\nFind Next Available Slot")
    print("===========================")
    slot = scheduler.find_next_available_slot(owner.get_all_tasks(), duration_minutes=15, after=time(9, 0))
    if slot:
        print(f"Next open 15-minute slot after 09:00: {slot.strftime('%H:%M')}")
    else:
        print("No open 15-minute slot found after 09:00.")

    print("\nRecurrence Conflict Auto-Resolve")
    print("===================================")
    medication = Task(
        pet_id=mochi.pet_id,
        description="Evening medication",
        task_type="medication",
        duration_minutes=10,
        priority="high",
        scheduled_time=time(11, 0),
        recurrence="daily",
    )
    mochi.add_task(medication)
    blocker = Task(
        pet_id=luna.pet_id,
        description="Grooming session",
        task_type="grooming",
        duration_minutes=30,
        priority="low",
        scheduled_time=time(11, 0),
    )
    luna.add_task(blocker)

    next_medication = scheduler.complete_task(owner, medication.task_id)
    print(f"Next occurrence inherited the same time: {next_medication.scheduled_time.strftime('%H:%M')}")
    print(scheduler.check_conflict(next_medication, owner.get_all_tasks()) or "No conflict before resolving.")

    moved = scheduler.resolve_recurrence_conflict(owner, next_medication)
    if moved:
        print(f"Auto-resolved: moved to {next_medication.scheduled_time.strftime('%H:%M')} to avoid the conflict.")
    else:
        print("No move was needed or possible.")

    print("\nPersistence (save/load)")
    print("==========================")
    owner.save_to_json("data.json")
    print("Saved current owner, pets, and tasks to data.json")
    reloaded = Owner.load_from_json("data.json")
    print(
        f"Reloaded owner '{reloaded.name}' with {len(reloaded.pets)} pet(s) and "
        f"{len(reloaded.get_all_tasks())} task(s) from data.json"
    )


if __name__ == "__main__":
    main()
