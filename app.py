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

# ── Design system ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mali:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;1,200;1,300;1,400;1,500;1,600;1,700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Mali', sans-serif !important;
    }

    /* Background */
    .stApp, .main .block-container {
        background-color: #F5F1EA !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #4a342a !important;
        font-family: 'Mali', sans-serif !important;
    }

    /* Labels & body text */
    label, p, .stCaption p, div[data-testid="stMarkdownContainer"] p {
        color: #7d5a44 !important;
        font-family: 'Mali', sans-serif !important;
    }

    /* Inputs */
    input, textarea {
        background-color: #d7c9b8 !important;
        color: #4a342a !important;
        font-family: 'Mali', sans-serif !important;
        border-color: #b2967d !important;
    }
    [data-baseweb="select"] * {
        background-color: #d7c9b8 !important;
        color: #4a342a !important;
        font-family: 'Mali', sans-serif !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #b2967d !important;
        color: #F5F1EA !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Mali', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.4rem 1.4rem !important;
    }
    .stButton > button:hover {
        background-color: #7d5a44 !important;
        color: #F5F1EA !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #d7c9b8 !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #7d5a44 !important;
        font-family: 'Mali', sans-serif !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #b2967d !important;
        color: #F5F1EA !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #d7c9b8 !important;
        color: #4a342a !important;
        font-family: 'Mali', sans-serif !important;
        border-radius: 8px !important;
    }

    /* Metric */
    [data-testid="metric-container"] {
        background-color: #d7c9b8 !important;
        border-radius: 8px !important;
        padding: 8px !important;
    }

    /* Divider */
    hr {
        border-color: #d7c9b8 !important;
    }

    /* Task card */
    .task-card {
        background-color: #e8e0d4;
        border-left: 4px solid #b2967d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-family: 'Mali', sans-serif;
    }
    .task-card .task-title {
        font-size: 1.05em;
        font-weight: 600;
        color: #4a342a;
        margin-bottom: 4px;
    }
    .task-card .task-meta {
        color: #7d5a44;
        font-size: 0.88em;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your cozy pet care companion")
st.divider()

# ── Pet & Owner ────────────────────────────────────────────────────────────────
st.subheader("Pet & Owner")
col_own, col_pet, col_spc = st.columns(3)
with col_own:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_pet:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_spc:
    species = st.selectbox("Species", ["dog", "cat", "other"])

# ── Session state ──────────────────────────────────────────────────────────────
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

# ── Priority helpers ───────────────────────────────────────────────────────────
PRIORITY_BADGE = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_BADGE = {TaskStatus.PENDING: "⏳", TaskStatus.COMPLETED: "✅", TaskStatus.SKIPPED: "⏭️"}


def _priority_cell(t: PetTask) -> str:
    badge = PRIORITY_BADGE.get(t.priority, "")
    if t.priority_factors:
        score = t.priority_factors.compute_score(weights)
        return f"{badge} {t.priority} ({score:.1f})"
    return f"{badge} {t.priority}"


def _render_task_card(t: PetTask) -> None:
    status = STATUS_BADGE.get(t.status, "")
    st.markdown(f"""
    <div class="task-card">
        <div class="task-title">{status} {t.title}</div>
        <div class="task-meta">
            {_priority_cell(t)} &nbsp;·&nbsp;
            Start: <strong>{t.startAt.strftime("%H:%M")}</strong> &nbsp;·&nbsp;
            {t.estimatedMinutes} min
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_schedule_card(t: PetTask) -> None:
    status = STATUS_BADGE.get(t.status, "")
    st.markdown(f"""
    <div class="task-card">
        <div class="task-title">{status} {t.title}</div>
        <div class="task-meta">
            {_priority_cell(t)} &nbsp;·&nbsp;
            {t.startAt.strftime("%H:%M")} → {t.endAt.strftime("%H:%M")} &nbsp;·&nbsp;
            {t.estimatedMinutes} min &nbsp;·&nbsp;
            {t.status.name}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_add, tab_tasks, tab_schedule = st.tabs(["➕  Add Task", "📋  My Tasks", "📅  Daily Schedule"])

# ── Tab: Add Task ──────────────────────────────────────────────────────────────
with tab_add:
    with st.expander("New Task", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            care_type = st.selectbox("Care type", ["feeding", "exercise", "grooming", "medication", "checkup", "other"])

        task_date = st.date_input("Date", value=date.today(), min_value=date.today())

        col_start, col_dur, col_due = st.columns(3)
        with col_start:
            default_start = (datetime.now() + timedelta(minutes=30)).time().replace(second=0, microsecond=0)
            start_time = st.time_input("Start time", value=default_start)
            start_at = datetime.combine(task_date, start_time)
        with col_dur:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            end_at = start_at + timedelta(minutes=int(duration))
        with col_due:
            default_due = (datetime.now() + timedelta(hours=2)).time().replace(second=0, microsecond=0)
            due_time = st.time_input("Due time", value=default_due)
            due_at = datetime.combine(task_date, due_time)
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

# ── Tab: My Tasks ──────────────────────────────────────────────────────────────
with tab_tasks:
    if pet.tasks:
        sort_option = st.radio(
            "Sort by",
            ["Start Time", "Status", "Priority"],
            horizontal=True,
        )

        if sort_option == "Start Time":
            sorted_tasks = scheduler.sort_by_time(pet.tasks)
        elif sort_option == "Status":
            sorted_tasks = scheduler.sort_by_completion(pet.tasks)
        else:
            sorted_tasks = scheduler.sort_by_priority(pet.tasks, weights)

        for t in sorted_tasks:
            _render_task_card(t)
    else:
        st.info("No tasks yet. Head to Add Task to get started.")

# ── Tab: Daily Schedule ────────────────────────────────────────────────────────
with tab_schedule:
    schedule_date = st.date_input("Schedule date", value=date.today())
    if st.button("Generate schedule"):
        agenda = scheduler.getPetAgenda(pet, schedule_date)
        if agenda:
            sorted_agenda = scheduler.sort_by_time(agenda)
            st.success(f"Schedule for {pet.name} ({user.name}) — {schedule_date} | {len(sorted_agenda)} task(s)")

            conflicts_found = False
            for t in sorted_agenda:
                warn = scheduler.warnConflict(t)
                if warn:
                    st.warning(warn)
                    conflicts_found = True

            if not conflicts_found:
                st.success("No scheduling conflicts detected.")

            for t in sorted_agenda:
                _render_schedule_card(t)
        else:
            st.warning(f"No tasks scheduled for {pet.name} on {schedule_date}.")
