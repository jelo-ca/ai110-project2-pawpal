import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from pawpal_system import (
    AnimalProfile, Pet, PetTask, PetTaskScheduler,
    PriorityWeights, TaskPriorityFactors, TaskStatus, User,
)

TASKS_FILE = Path(__file__).parent / "tasks_data.json"


def load_tasks() -> list:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def save_tasks(tasks: list) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def _compute_urgency(due_at: datetime) -> int:
    """Map time-until-due to an urgency score 1–5."""
    hours_left = (due_at - datetime.now()).total_seconds() / 3600
    if hours_left < 1:
        return 5
    if hours_left < 3:
        return 4
    if hours_left < 6:
        return 3
    if hours_left < 12:
        return 2
    return 1

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

weights = PriorityWeights()

# Reconstruct PetTask objects from persisted task dicts so the scheduler is in sync
if not pet.tasks and st.session_state.tasks:
    now = datetime.now()
    for t in st.session_state.tasks:
        pf = None
        if "due_at" in t and "user_importance" in t:
            saved_due = datetime.fromisoformat(t["due_at"])
            pf = TaskPriorityFactors(
                urgency=_compute_urgency(saved_due),
                user_importance=t["user_importance"],
            )
        saved_start = datetime.fromisoformat(t["start_at"]) if "start_at" in t else now
        saved_due_dt = datetime.fromisoformat(t["due_at"]) if "due_at" in t else now
        pet_task = PetTask(
            uid=str(uuid.uuid4()),
            petId=pet.uid,
            title=t["title"],
            careType=t.get("care_type", "general"),
            instructions=t.get("instructions", ""),
            dueAt=saved_due_dt,
            startAt=saved_start,
            endAt=saved_start + timedelta(minutes=t["duration_minutes"]),
            estimatedMinutes=t["duration_minutes"],
            status=TaskStatus.PENDING,
            priority=t["priority"],
            priority_factors=pf,
            reminderMinutesBefore=t.get("reminder_minutes", 15),
            isRecurring=t.get("is_recurring", False),
        )
        scheduler.createTaskForPet(pet, pet_task)

# --- Task input ---
st.markdown("### Add Task")

col1, col2 = st.columns([3, 1])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    care_type = st.selectbox("Care type", ["feeding", "exercise", "grooming", "medication", "checkup", "other"])

col_start, col_dur, col_due = st.columns(3)
with col_start:
    default_start = (datetime.now() + timedelta(minutes=30)).time().replace(second=0, microsecond=0)
    start_time = st.time_input("Start time", value=default_start)
    start_at = datetime.combine(date.today(), start_time)
with col_dur:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    end_at = start_at + timedelta(minutes=int(duration))
with col_due:
    default_due = (datetime.now() + timedelta(hours=2)).time().replace(second=0, microsecond=0)
    due_time = st.time_input("Due time", value=default_due)
    due_at = datetime.combine(date.today(), due_time)
    urgency = _compute_urgency(due_at)
    st.caption(f"Urgency: **{urgency}/5**")

col_imp, _, col_preview = st.columns([2, 1, 1])
with col_imp:
    importance = st.slider("User importance", 1, 5, 3, help="1 = low priority  |  5 = must-do")
with col_preview:
    _preview = TaskPriorityFactors(urgency=urgency, user_importance=importance)
    st.metric("Priority", _preview.to_label(weights), f"score {_preview.compute_score(weights):.1f}")

with st.expander("Optional details"):
    instructions = st.text_area("Instructions", value="", placeholder="Any special notes...")
    col_rem, col_rec = st.columns(2)
    with col_rem:
        reminder = st.number_input("Reminder (min before)", min_value=0, max_value=120, value=15)
    with col_rec:
        is_recurring = st.checkbox("Recurring task")

if st.button("Add task"):
    factors = TaskPriorityFactors(urgency=urgency, user_importance=importance)
    priority_label = factors.to_label(weights)
    pet_task = PetTask(
        uid=str(uuid.uuid4()),
        petId=pet.uid,
        title=task_title,
        careType=care_type,
        instructions=instructions,
        dueAt=due_at,
        startAt=start_at,
        endAt=end_at,
        estimatedMinutes=int(duration),
        status=TaskStatus.PENDING,
        priority=priority_label,
        priority_factors=factors,
        reminderMinutesBefore=int(reminder),
        isRecurring=is_recurring,
    )
    conflict_warning = scheduler.warnConflict(pet_task)
    scheduler.createTaskForPet(pet, pet_task)
    st.session_state.tasks.append({
        "title": task_title,
        "care_type": care_type,
        "duration_minutes": int(duration),
        "start_at": start_at.isoformat(),
        "due_at": due_at.isoformat(),
        "priority": priority_label,
        "user_importance": importance,
        "instructions": instructions,
        "reminder_minutes": int(reminder),
        "is_recurring": is_recurring,
    })
    save_tasks(st.session_state.tasks)
    if conflict_warning:
        st.warning(conflict_warning)
    else:
        st.success(f"Task '{task_title}' added successfully.")

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PRIORITY_BADGE = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_BADGE = {TaskStatus.PENDING: "⏳", TaskStatus.COMPLETED: "✅", TaskStatus.SKIPPED: "⏭️"}


def _priority_cell(t: PetTask) -> str:
    badge = PRIORITY_BADGE.get(t.priority, "")
    if t.priority_factors:
        score = t.priority_factors.compute_score(weights)
        return f"{badge} {t.priority} ({score:.1f})"
    return f"{badge} {t.priority}"

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
        sorted_tasks = scheduler.sort_by_priority(pet.tasks, weights)

    rows = [
        {
            "": STATUS_BADGE.get(t.status, ""),
            "Task": t.title,
            "Priority": _priority_cell(t),
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
                "Priority": _priority_cell(t),
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
