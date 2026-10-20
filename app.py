from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

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
    st.session_state.owner = Owner(name=owner_name, contact_info="")

owner: Owner = st.session_state.owner

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
        st.success(f"Added '{task.description}' to {selected_pet.name}.")
        st.rerun()

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("All tasks:")
        st.table(
            [
                {
                    "pet": next(p.name for p in owner.pets if p.pet_id == t.pet_id),
                    "description": t.description,
                    "duration_minutes": t.duration_minutes,
                    "priority": t.priority,
                    "completed": t.is_completed,
                }
                for t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not owner.pets or not owner.get_all_tasks():
        st.warning("Add at least one pet and one task first.")
    else:
        scheduler = Scheduler(constraints={"start_time": time(7, 0)})
        schedule = scheduler.generate_schedule(owner)
        st.markdown("### Today's Schedule")
        st.code(scheduler.explain_plan(schedule))
