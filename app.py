from datetime import time
from pathlib import Path

import streamlit as st

import formatting
from pawpal_system import Owner, Pet, Scheduler, Task

DATA_FILE = Path(__file__).parent / "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to **PawPal+**, a pet care planning assistant.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

owner_name = st.text_input("Owner name", value="Jordan")

if "owner" not in st.session_state:
    if DATA_FILE.exists():
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
    else:
        st.session_state.owner = Owner(name=owner_name, contact_info="")

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(constraints={"start_time": time(7, 0)})

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler


def persist() -> None:
    """Save the current owner (pets + tasks) to disk so it survives a page refresh."""
    owner.save_to_json(DATA_FILE)


if DATA_FILE.exists():
    st.caption(f"💾 Loaded saved data from `{DATA_FILE.name}` ({len(owner.pets)} pet(s)).")

st.divider()

st.subheader("Adding a Pet")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    breed = st.text_input("Breed", value="Shiba Inu")

col4, col5, col6 = st.columns(3)
with col4:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
with col5:
    weight = st.number_input("Weight (lbs)", min_value=0.0, value=20.0)
with col6:
    height = st.number_input("Height (in)", min_value=0.0, value=16.0)

if st.button("Add pet"):
    pet = Pet(
        name=pet_name,
        species=species,
        breed=breed,
        age=int(age),
        weight=float(weight),
        height=float(height),
    )
    owner.add_pet(pet)
    persist()
    st.success(f"Added {pet.name} the {pet.breed}.")
    st.rerun()

if owner.pets:
    st.write("Pets:")
    st.table([p.get_info() for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Scheduling a Task")

if not owner.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    pets_by_name = {p.name: p for p in owner.pets}
    selected_pet = pets_by_name[st.selectbox("Pet", list(pets_by_name.keys()))]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_description = st.text_input("Task description", value="Morning walk")
    with col2:
        task_type = st.selectbox(
            "Task type", ["walk", "feeding", "outdoor_activity", "grooming", "medication"]
        )
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)

    if st.button("Add task"):
        task = Task(
            pet_id=selected_pet.pet_id,
            description=task_description,
            task_type=task_type,
            duration_minutes=int(duration),
            priority=priority,
        )
        selected_pet.add_task(task)
        persist()
        st.success(f"Added '{task.description}' to {selected_pet.name}.")
        st.rerun()

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("All tasks:")

        filter_col1, filter_col2, sort_col = st.columns(3)
        with filter_col1:
            pet_filter = st.selectbox("Filter by pet", ["All"] + list(pets_by_name.keys()))
        with filter_col2:
            status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
        with sort_col:
            sort_choice = st.radio("Sort by", ["Priority", "Scheduled time"], horizontal=True)

        is_completed = {"All": None, "Pending": False, "Completed": True}[status_filter]
        pet_name_filter = None if pet_filter == "All" else pet_filter
        filtered_tasks = owner.filter_tasks(is_completed=is_completed, pet_name=pet_name_filter)

        if sort_choice == "Priority":
            display_tasks = scheduler.sort_by_priority(filtered_tasks)
        else:
            display_tasks = scheduler.sort_by_time(filtered_tasks)

        if display_tasks:
            st.success(f"Showing {len(display_tasks)} of {len(all_tasks)} task(s).")
            st.table(
                [
                    formatting.task_to_row(t, next(p.name for p in owner.pets if p.pet_id == t.pet_id))
                    for t in display_tasks
                ]
            )
        else:
            st.warning("No tasks match the selected filters.")

        conflicts = scheduler.find_conflicts(filtered_tasks)
        if conflicts:
            st.warning(scheduler.explain_conflicts(owner, conflicts))
        elif display_tasks:
            st.success("No scheduling conflicts among the tasks shown.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Find Next Available Slot")

if not owner.get_all_tasks():
    st.info("Add some tasks first to search for an open slot around them.")
else:
    slot_col1, slot_col2 = st.columns(2)
    with slot_col1:
        slot_duration = st.number_input("Needed duration (minutes)", min_value=1, max_value=240, value=15)
    with slot_col2:
        slot_after = st.time_input("Search after", value=time(7, 0))

    if st.button("Find slot"):
        slot = scheduler.find_next_available_slot(
            owner.get_all_tasks(), duration_minutes=int(slot_duration), after=slot_after
        )
        if slot:
            st.success(f"Next open {int(slot_duration)}-minute slot: **{slot.strftime('%H:%M')}**")
        else:
            st.warning("No open slot of that length was found in the day.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet and one task first.")
    else:
        schedule = scheduler.generate_schedule(owner)
        persist()
        st.markdown("### Today's Schedule")

        if schedule:
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Tasks scheduled", len(schedule))
            with metric_col2:
                st.metric("Total minutes", sum(t.duration_minutes for t in schedule))

            st.table(
                [
                    formatting.task_to_row(t, next(p.name for p in owner.pets if p.pet_id == t.pet_id))
                    for t in schedule
                ]
            )

            conflicts = scheduler.find_conflicts(schedule)
            if conflicts:
                st.error(scheduler.explain_conflicts(owner, conflicts))
            else:
                st.success("No scheduling conflicts detected.")
        else:
            st.warning("No tasks could be scheduled within the given constraints.")
