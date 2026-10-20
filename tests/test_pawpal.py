from pawpal_system import Pet, Task


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
