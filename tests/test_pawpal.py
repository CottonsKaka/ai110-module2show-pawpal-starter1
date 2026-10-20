from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_sort_by_time_returns_chronological_order():
    scheduler = Scheduler()
    early = Task(
        pet_id="pet-1",
        description="Breakfast",
        task_type="feeding",
        duration_minutes=10,
        priority="high",
        scheduled_time=time(7, 0),
    )
    late = Task(
        pet_id="pet-1",
        description="Evening walk",
        task_type="walk",
        duration_minutes=30,
        priority="medium",
        scheduled_time=time(18, 0),
    )
    middle = Task(
        pet_id="pet-1",
        description="Medication",
        task_type="medication",
        duration_minutes=5,
        priority="high",
        scheduled_time=time(12, 30),
    )

    ordered = scheduler.sort_by_time([late, early, middle])

    assert ordered == [early, middle, late]


def test_mark_complete_on_daily_task_creates_next_day_task():
    today = date.today()
    task = Task(
        pet_id="pet-1",
        description="Feeding",
        task_type="feeding",
        duration_minutes=10,
        priority="high",
        recurrence="daily",
        due_date=today,
    )

    next_task = task.mark_complete()

    assert task.is_completed is True
    assert next_task is not None
    assert next_task.is_completed is False
    assert next_task.recurrence == "daily"
    assert next_task.description == task.description
    assert next_task.due_date == today + timedelta(days=1)


def test_find_conflicts_flags_duplicate_scheduled_times():
    scheduler = Scheduler()
    owner = Owner(name="Alex", contact_info="alex@example.com")
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    owner.add_pet(pet)

    task_a = Task(
        pet_id=pet.pet_id,
        description="Walk",
        task_type="walk",
        duration_minutes=30,
        priority="high",
        scheduled_time=time(9, 0),
    )
    task_b = Task(
        pet_id=pet.pet_id,
        description="Grooming",
        task_type="grooming",
        duration_minutes=20,
        priority="medium",
        scheduled_time=time(9, 0),
    )
    pet.add_task(task_a)
    pet.add_task(task_b)

    conflicts = scheduler.find_conflicts(owner.get_all_tasks())

    assert conflicts == [(task_a, task_b)]


def test_mark_complete_changes_task_status():
    task = Task(
        pet_id="pet-1",
        description="Morning walk",
        task_type="walk",
        duration_minutes=30,
        priority="high",
    )
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    assert len(pet.get_tasks()) == 0

    task = Task(
        pet_id=pet.pet_id,
        description="Feeding",
        task_type="feeding",
        duration_minutes=10,
        priority="high",
    )
    pet.add_task(task)

    assert len(pet.get_tasks()) == 1


def test_sort_by_priority_breaks_ties_by_scheduled_time():
    scheduler = Scheduler()
    later = Task(
        pet_id="pet-1",
        description="Afternoon walk",
        task_type="walk",
        duration_minutes=20,
        priority="high",
        scheduled_time=time(14, 0),
    )
    earlier = Task(
        pet_id="pet-1",
        description="Morning walk",
        task_type="walk",
        duration_minutes=20,
        priority="high",
        scheduled_time=time(8, 0),
    )
    low_priority = Task(
        pet_id="pet-1",
        description="Nail trim",
        task_type="grooming",
        duration_minutes=5,
        priority="low",
        scheduled_time=time(7, 0),
    )

    ordered = scheduler.sort_by_priority([later, low_priority, earlier])

    assert ordered == [earlier, later, low_priority]


def test_find_next_available_slot_finds_gap_between_tasks():
    scheduler = Scheduler()
    morning = Task(
        pet_id="pet-1",
        description="Feeding",
        task_type="feeding",
        duration_minutes=10,
        priority="high",
        scheduled_time=time(8, 0),
    )
    afternoon = Task(
        pet_id="pet-1",
        description="Walk",
        task_type="walk",
        duration_minutes=30,
        priority="high",
        scheduled_time=time(8, 30),
    )

    slot = scheduler.find_next_available_slot([morning, afternoon], duration_minutes=15, after=time(8, 0))

    assert slot == time(8, 10)


def test_find_next_available_slot_returns_none_when_day_is_full():
    scheduler = Scheduler()
    all_day = Task(
        pet_id="pet-1",
        description="All day thing",
        task_type="walk",
        duration_minutes=14 * 60,
        priority="low",
        scheduled_time=time(7, 0),
    )

    slot = scheduler.find_next_available_slot(
        [all_day], duration_minutes=10, day_start=time(7, 0), day_end=time(21, 0)
    )

    assert slot is None


def test_resolve_recurrence_conflict_moves_task_on_overlap():
    scheduler = Scheduler()
    owner = Owner(name="Alex", contact_info="alex@example.com")
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    owner.add_pet(pet)

    blocker = Task(
        pet_id=pet.pet_id,
        description="Grooming",
        task_type="grooming",
        duration_minutes=30,
        priority="low",
        scheduled_time=time(10, 0),
    )
    recurring_next = Task(
        pet_id=pet.pet_id,
        description="Medication",
        task_type="medication",
        duration_minutes=10,
        priority="high",
        scheduled_time=time(10, 0),
        recurrence="daily",
    )
    pet.add_task(blocker)
    pet.add_task(recurring_next)

    moved = scheduler.resolve_recurrence_conflict(owner, recurring_next)

    assert moved is True
    assert recurring_next.scheduled_time == time(10, 30)
    assert scheduler.check_conflict(recurring_next, owner.get_all_tasks()) is None


def test_save_and_load_json_round_trip(tmp_path):
    owner = Owner(name="Alex", contact_info="alex@example.com")
    pet = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            description="Feeding",
            task_type="feeding",
            duration_minutes=10,
            priority="high",
            scheduled_time=time(8, 0),
            due_date=date(2026, 1, 1),
        )
    )
    owner.add_pet(pet)

    path = tmp_path / "data.json"
    owner.save_to_json(path)
    reloaded = Owner.load_from_json(path)

    assert reloaded.name == owner.name
    assert len(reloaded.pets) == 1
    assert reloaded.pets[0].name == "Mochi"
    reloaded_task = reloaded.pets[0].tasks[0]
    assert reloaded_task.description == "Feeding"
    assert reloaded_task.scheduled_time == time(8, 0)
    assert reloaded_task.due_date == date(2026, 1, 1)
