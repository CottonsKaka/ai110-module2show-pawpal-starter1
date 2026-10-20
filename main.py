from datetime import time

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", contact_info="jordan@example.com")

    mochi = Pet(name="Mochi", species="dog", breed="Shiba Inu", age=3, weight=22.5, height=40.0)
    luna = Pet(name="Luna", species="cat", breed="Tabby", age=5, weight=9.0, height=25.0)
    owner.add_pet(mochi)
    owner.add_pet(luna)

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
        )
    )

    scheduler = Scheduler(constraints={"start_time": time(7, 0)})
    schedule = scheduler.generate_schedule(owner)

    print("Today's Schedule")
    print("=================")
    print(scheduler.explain_plan(schedule))


if __name__ == "__main__":
    main()
