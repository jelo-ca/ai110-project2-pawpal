import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from pawpal_system import AnimalProfile, Pet, PetTask, PetTaskScheduler, TaskStatus, User

TASKS_FILE = Path(__file__).parent / "tasks_data.json"


def load_tasks() -> list:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def save_tasks(tasks: list) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# --- Session state initialization ---
# Reference existing objects before creating new ones so data survives reruns.

if "scheduler" not in st.session_state:
    st.session_state.scheduler = PetTaskScheduler()

if "pet" not in st.session_state:
    st.session_state.pet = Pet(
        uid="pet-1",
        name=pet_name,
        animalProfileId="profile-1",
        birthDate=date(2020, 1, 1),
        weightKg=5.0,
    )
else:
    st.session_state.pet.name = pet_name

if "user" not in st.session_state:
    st.session_state.user = User(
        uid="user-1",
        name=owner_name,
        phoneNumber="",
        timezone="UTC",
        pets=[st.session_state.pet],
    )
else:
    st.session_state.user.name = owner_name

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# Convenience references
scheduler: PetTaskScheduler = st.session_state.scheduler
pet: Pet = st.session_state.pet
user: User = st.session_state.user

# Reconstruct PetTask objects from persisted task dicts so the scheduler is in sync
if not pet.tasks and st.session_state.tasks:
    now = datetime.now()
    for t in st.session_state.tasks:
        pet_task = PetTask(
            uid=str(uuid.uuid4()),
            petId=pet.uid,
            title=t["title"],
            careType="general",
            instructions="",
            dueAt=now,
            startAt=now,
            endAt=now + timedelta(minutes=t["duration_minutes"]),
            estimatedMinutes=t["duration_minutes"],
            status=TaskStatus.PENDING,
            priority=t["priority"],
            reminderMinutesBefore=15,
            isRecurring=False,
        )
        scheduler.createTaskForPet(pet, pet_task)

# --- Task input ---
st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    now = datetime.now()
    pet_task = PetTask(
        uid=str(uuid.uuid4()),
        petId=pet.uid,
        title=task_title,
        careType="general",
        instructions="",
        dueAt=now,
        startAt=now,
        endAt=now + timedelta(minutes=int(duration)),
        estimatedMinutes=int(duration),
        status=TaskStatus.PENDING,
        priority=priority,
        reminderMinutesBefore=15,
        isRecurring=False,
    )
    conflict_warning = scheduler.warnConflict(pet_task)
    scheduler.createTaskForPet(pet, pet_task)
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )
    save_tasks(st.session_state.tasks)
    if conflict_warning:
        st.warning(conflict_warning)
    else:
        st.success(f"Task '{task_title}' added successfully.")

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PRIORITY_BADGE = {"high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_BADGE = {TaskStatus.PENDING: "⏳", TaskStatus.COMPLETED: "✅", TaskStatus.SKIPPED: "⏭️"}

if pet.tasks:
    sort_option = st.radio(
        "Sort tasks by",
        ["Start Time", "Status", "Priority"],
        horizontal=True,
    )

    if sort_option == "Start Time":
        sorted_tasks = scheduler.sort_by_time(pet.tasks)
    elif sort_option == "Status":
        sorted_tasks = scheduler.sort_by_completion(pet.tasks)
    else:
        sorted_tasks = sorted(pet.tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    rows = [
        {
            "": STATUS_BADGE.get(t.status, ""),
            "Task": t.title,
            "Priority": f"{PRIORITY_BADGE.get(t.priority, '')} {t.priority}",
            "Duration (min)": t.estimatedMinutes,
            "Start": t.startAt.strftime("%H:%M"),
        }
        for t in sorted_tasks
    ]
    st.table(rows)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    today = date.today()
    agenda = scheduler.getPetAgenda(pet, today)
    if agenda:
        sorted_agenda = scheduler.sort_by_time(agenda)
        st.success(f"Schedule for {pet.name} ({user.name}) — {today} | {len(sorted_agenda)} task(s)")

        conflicts_found = False
        for t in sorted_agenda:
            warn = scheduler.warnConflict(t)
            if warn:
                st.warning(warn)
                conflicts_found = True

        if not conflicts_found:
            st.success("No scheduling conflicts detected.")

        agenda_rows = [
            {
                "": STATUS_BADGE.get(t.status, ""),
                "Task": t.title,
                "Priority": f"{PRIORITY_BADGE.get(t.priority, '')} {t.priority}",
                "Start": t.startAt.strftime("%H:%M"),
                "End": t.endAt.strftime("%H:%M"),
                "Duration (min)": t.estimatedMinutes,
                "Status": t.status.name,
            }
            for t in sorted_agenda
        ]
        st.table(agenda_rows)
    else:
        st.warning(f"No tasks scheduled for {pet.name} today ({today}).")
