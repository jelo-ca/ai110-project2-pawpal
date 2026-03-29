import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

from pawpal_system import (
    Pet, PetTask, PetTaskScheduler,
    PriorityWeights, TaskPriorityFactors, TaskStatus,
)

TASKS_FILE = Path(__file__).parent / "tasks_data.json"
USERS_FILE = Path(__file__).parent / "users_data.json"


def load_tasks() -> list:
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []


def save_tasks(tasks: list) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


def load_users() -> list:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return []


def save_users(users: list) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2))


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
    input:disabled {
        -webkit-text-fill-color: #4a342a !important;
        opacity: 1 !important;
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
        width: 100% !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: #7d5a44 !important;
        font-family: 'Mali', sans-serif !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        flex: 1 !important;
        justify-content: center !important;
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

    /* Actionable card: flatten bottom so button attaches flush */
    .task-card-actionable {
        border-radius: 8px 8px 0 0 !important;
        margin-bottom: 0 !important;
    }

    /* Button immediately following an actionable card */
    .element-container:has(.task-card-actionable) + .element-container button {
        border-radius: 0 0 8px 8px !important;
        width: 100% !important;
        margin-top: 0 !important;
        padding: 4px 16px !important;
        font-size: 0.85em !important;
        background-color: #c4a285 !important;
        margin-bottom: 10px !important;
    }

    /* Delete button: stretch column to row height, remove inner gaps */
    div[data-testid="stHorizontalBlock"]:has(.task-card) {
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:first-child {
        padding-right: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:last-child {
        padding-left: 0 !important;
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:last-child > div,
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:last-child .stButton {
        flex: 1 !important;
        display: flex !important;
        flex-direction: column !important;
    }

    /* Delete button: brown background, flat left corners, fills full height */
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:last-child .stButton > button {
        background-color: #b2967d !important;
        color: #F5F1EA !important;
        border: none !important;
        border-radius: 0 8px 8px 0 !important;
        flex: 1 !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 10px !important;
        font-size: 1.1em !important;
        font-weight: 600 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.task-card) > [data-testid="column"]:last-child .stButton > button:hover {
        background-color: #7d5a44 !important;
        color: #F5F1EA !important;
    }

    /* Card in delete row: flat right corners */
    div[data-testid="stHorizontalBlock"]:has(.task-card) .task-card {
        border-radius: 8px 0 0 8px !important;
        margin-bottom: 10px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.task-card) .task-card-actionable {
        border-radius: 8px 0 0 0 !important;
        margin-bottom: 0 !important;
    }

    /* Mark-complete button in delete row: flat right corner */
    div[data-testid="stHorizontalBlock"]:has(.task-card-actionable) .element-container:has(.task-card-actionable) + .element-container button {
        border-radius: 0 0 0 8px !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🐾 PawPal+")
st.caption("Your cozy pet care companion")
st.divider()

# ── Session state ──────────────────────────────────────────────────────────────
if "scheduler" not in st.session_state:
    st.session_state.scheduler = PetTaskScheduler()

# Load/init persistent users & pets
if "users_data" not in st.session_state:
    raw = load_users()
    if not raw:
        raw = [{"uid": "user-1", "name": "Bey", "pets": [
            {"uid": "pet-1", "name": "Simba", "species": "cat"}
        ]}]
        save_users(raw)
    st.session_state.users_data = raw

if "selected_user_uid" not in st.session_state:
    st.session_state.selected_user_uid = st.session_state.users_data[0]["uid"]

if "selected_pet_uid" not in st.session_state:
    first_user = st.session_state.users_data[0]
    st.session_state.selected_pet_uid = first_user["pets"][0]["uid"] if first_user["pets"] else None

# Build Pet dataclass objects for all pets (once per session)
if "pet_objects" not in st.session_state:
    st.session_state.pet_objects = {}
    for u in st.session_state.users_data:
        for p_data in u["pets"]:
            st.session_state.pet_objects[p_data["uid"]] = Pet(
                uid=p_data["uid"],
                name=p_data["name"],
                animalProfileId="profile-1",
                birthDate=date(2020, 1, 1),
                weightKg=5.0,
            )

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# Load tasks into scheduler once per session
if "tasks_loaded" not in st.session_state:
    st.session_state.tasks_loaded = True
    needs_save = False
    now = datetime.now()
    for t in st.session_state.tasks:
        # Migrate older tasks that have no uid
        if "uid" not in t:
            t["uid"] = str(uuid.uuid4())
            needs_save = True
        # Migrate older tasks that have no status
        if "status" not in t:
            t["status"] = TaskStatus.PENDING.name
            needs_save = True
        # Migrate older tasks that have no pet_id to the default first pet
        pet_id = t.get("pet_id", "pet-1")
        pet_obj = st.session_state.pet_objects.get(pet_id)
        if pet_obj is None:
            continue
        pf = None
        if "due_at" in t and "user_importance" in t:
            saved_due = datetime.fromisoformat(t["due_at"])
            pf = TaskPriorityFactors(
                urgency=_compute_urgency(saved_due),
                user_importance=t["user_importance"],
            )
        saved_start = datetime.fromisoformat(t["start_at"]) if "start_at" in t else now
        saved_due_dt = datetime.fromisoformat(t["due_at"]) if "due_at" in t else now
        saved_status = TaskStatus[t.get("status", "PENDING")]
        pet_task = PetTask(
            uid=t["uid"],
            petId=pet_id,
            title=t["title"],
            careType=t.get("care_type", "general"),
            instructions=t.get("instructions", ""),
            dueAt=saved_due_dt,
            startAt=saved_start,
            endAt=saved_start + timedelta(minutes=t["duration_minutes"]),
            estimatedMinutes=t["duration_minutes"],
            status=saved_status,
            priority=t["priority"],
            priority_factors=pf,
            reminderMinutesBefore=t.get("reminder_minutes", 15),
            isRecurring=t.get("is_recurring", False),
        )
        st.session_state.scheduler.createTaskForPet(pet_obj, pet_task)
    if needs_save:
        save_tasks(st.session_state.tasks)

# ── Pet & Owner selection ───────────────────────────────────────────────────────
st.subheader("Pet & Owner")

_ADD_OWNER = "➕ Add new owner..."
_ADD_PET   = "➕ Add new pet..."

users_data = st.session_state.users_data
user_names = [u["name"] for u in users_data]
user_uids  = [u["uid"]  for u in users_data]

col_own, col_pet, col_spc = st.columns(3)

# ── Owner column ────────────────────────────────────────────────────────────────
with col_own:
    cur_user_idx = user_uids.index(st.session_state.selected_user_uid) if st.session_state.selected_user_uid in user_uids else 0
    selected_owner = st.selectbox("Owner", user_names + [_ADD_OWNER], index=cur_user_idx, key="owner_select")

    if selected_owner == _ADD_OWNER:
        new_owner_input = st.text_input("New owner name", key="new_owner_input",
                                        label_visibility="collapsed", placeholder="Owner name")
        if st.button("Add owner", key="btn_add_owner"):
            if new_owner_input.strip():
                new_uid = str(uuid.uuid4())
                st.session_state.users_data.append({
                    "uid": new_uid,
                    "name": new_owner_input.strip(),
                    "pets": [],
                })
                st.session_state.selected_user_uid = new_uid
                st.session_state.selected_pet_uid = None
                save_users(st.session_state.users_data)
                st.rerun()
            else:
                st.warning("Enter an owner name.")
    else:
        new_user_uid = user_uids[user_names.index(selected_owner)]
        if new_user_uid != st.session_state.selected_user_uid:
            st.session_state.selected_user_uid = new_user_uid
            new_pets = next((u["pets"] for u in users_data if u["uid"] == new_user_uid), [])
            st.session_state.selected_pet_uid = new_pets[0]["uid"] if new_pets else None

current_user_data = next((u for u in users_data if u["uid"] == st.session_state.selected_user_uid), None)

# Track whether the user is in "add pet" mode
adding_pet = False
selected_pet = None

# ── Pet column ──────────────────────────────────────────────────────────────────
with col_pet:
    if selected_owner == _ADD_OWNER or not current_user_data:
        st.selectbox("Pet", ["—"], disabled=True, key="pet_select_disabled")
    else:
        pet_names = [p["name"] for p in current_user_data["pets"]]
        pet_uids  = [p["uid"]  for p in current_user_data["pets"]]
        cur_pet_idx = pet_uids.index(st.session_state.selected_pet_uid) if st.session_state.selected_pet_uid in pet_uids else 0
        selected_pet = st.selectbox("Pet", pet_names + [_ADD_PET], index=cur_pet_idx, key="pet_select")

        if selected_pet == _ADD_PET:
            adding_pet = True
            new_pet_input   = st.text_input("Pet name", key="new_pet_input",
                                            label_visibility="collapsed", placeholder="Pet name")
            new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species_input",
                                           label_visibility="collapsed")
            if st.button("Add pet", key="btn_add_pet"):
                if new_pet_input.strip():
                    new_pet_uid = str(uuid.uuid4())
                    for u in st.session_state.users_data:
                        if u["uid"] == st.session_state.selected_user_uid:
                            u["pets"].append({"uid": new_pet_uid, "name": new_pet_input.strip(),
                                              "species": new_pet_species})
                            break
                    st.session_state.pet_objects[new_pet_uid] = Pet(
                        uid=new_pet_uid,
                        name=new_pet_input.strip(),
                        animalProfileId="profile-1",
                        birthDate=date(2020, 1, 1),
                        weightKg=5.0,
                    )
                    st.session_state.selected_pet_uid = new_pet_uid
                    save_users(st.session_state.users_data)
                    st.rerun()
                else:
                    st.warning("Enter a pet name.")
        else:
            if pet_names:
                st.session_state.selected_pet_uid = pet_uids[pet_names.index(selected_pet)]

# ── Species column (read-only display for selected pet) ─────────────────────────
with col_spc:
    if not adding_pet and current_user_data and st.session_state.selected_pet_uid:
        pet_d = next((p for p in current_user_data["pets"] if p["uid"] == st.session_state.selected_pet_uid), None)
        if pet_d:
            st.text_input("Species", value=pet_d.get("species", "dog"),
                          disabled=True, key="species_display")

st.divider()

# ── Convenience references ──────────────────────────────────────────────────────
scheduler: PetTaskScheduler = st.session_state.scheduler
weights = PriorityWeights()
pet: Pet = st.session_state.pet_objects.get(st.session_state.selected_pet_uid) if st.session_state.selected_pet_uid else None
owner_name: str = current_user_data["name"] if current_user_data else "Unknown"

# ── Priority helpers ────────────────────────────────────────────────────────────
PRIORITY_BADGE = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}
STATUS_BADGE = {TaskStatus.PENDING: "⏳", TaskStatus.COMPLETED: "✅", TaskStatus.SKIPPED: "⏭️"}
CARE_EMOJI = {
    "feeding":    "🍽️",
    "grooming":   "✂️",
    "exercise":   "🏃",
    "hygiene":    "🧹",
    "medication": "💊",
    "checkup":    "🩺",
    "general":    "📋",
    "other":      "📝",
}


def _priority_cell(t: PetTask) -> str:
    badge = PRIORITY_BADGE.get(t.priority, "")
    if t.priority_factors:
        score = t.priority_factors.compute_score(weights)
        return f"{badge} {t.priority} ({score:.1f})"
    return f"{badge} {t.priority}"


def _status_label(t: PetTask) -> str:
    if t.status == TaskStatus.PENDING:
        return "SCHEDULED"
    return t.status.name


def _render_task_card(t: PetTask) -> None:
    status = STATUS_BADGE.get(t.status, "")
    care_icon = CARE_EMOJI.get(t.careType.lower(), "📋")
    card_class = "task-card" + (" task-card-actionable" if t.status != TaskStatus.COMPLETED else "")
    st.markdown(f"""
    <div class="{card_class}">
        <div class="task-title">{status} {t.title}</div>
        <div class="task-meta">
            {care_icon} {t.careType} &nbsp;·&nbsp;
            {_priority_cell(t)} &nbsp;·&nbsp;
            {t.startAt.strftime("%b %d")} &nbsp;·&nbsp;
            Start: <strong>{t.startAt.strftime("%H:%M")}</strong> &nbsp;·&nbsp;
            {t.estimatedMinutes} min &nbsp;·&nbsp;
            {_status_label(t)}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_schedule_card(t: PetTask) -> None:
    status = STATUS_BADGE.get(t.status, "")
    care_icon = CARE_EMOJI.get(t.careType.lower(), "📋")
    st.markdown(f"""
    <div class="task-card">
        <div class="task-title">{status} {t.title}</div>
        <div class="task-meta">
            {care_icon} {t.careType} &nbsp;·&nbsp;
            {_priority_cell(t)} &nbsp;·&nbsp;
            {t.startAt.strftime("%b %d")} &nbsp;·&nbsp;
            {t.startAt.strftime("%H:%M")} → {t.endAt.strftime("%H:%M")} &nbsp;·&nbsp;
            {t.estimatedMinutes} min &nbsp;·&nbsp;
            {_status_label(t)}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Tabs ────────────────────────────────────────────────────────────────────────
tab_add, tab_tasks, tab_schedule = st.tabs(["➕  Add Task", "📋  My Tasks", "📅  Daily Schedule"])

_TASK_FORM_KEYS = [
    "task_title", "task_care_type", "task_date",
    "task_start_time", "task_duration", "task_due_time",
    "task_importance", "task_instructions", "task_reminder", "task_is_recurring",
]

# ── Tab: Add Task ───────────────────────────────────────────────────────────────
with tab_add:
    if pet is None:
        st.info("Select or add a pet above to get started.")
    else:
        # Show result message from previous submit (survives the rerun)
        if "_task_msg" in st.session_state:
            msg_type, msg_text = st.session_state.pop("_task_msg")
            (st.warning if msg_type == "warning" else st.success)(msg_text)

        with st.expander("New Task", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                task_title = st.text_input("Task title", value="", key="task_title")
            with col2:
                care_type = st.selectbox("Care type", ["feeding", "exercise", "grooming", "medication", "checkup", "other"], key="task_care_type")

            task_date = st.date_input("Date", value=date.today(), min_value=date.today(), key="task_date")

            col_start, col_dur, col_due = st.columns(3)
            with col_start:
                default_start = (datetime.now() + timedelta(minutes=30)).time().replace(second=0, microsecond=0)
                start_time = st.time_input("Start time", value=default_start, key="task_start_time")
                start_at = datetime.combine(task_date, start_time)
            with col_dur:
                duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="task_duration")
                end_at = start_at + timedelta(minutes=int(duration))
            with col_due:
                default_due = (datetime.now() + timedelta(hours=2)).time().replace(second=0, microsecond=0)
                due_time = st.time_input("Due time", value=default_due, key="task_due_time")
                due_at = datetime.combine(task_date, due_time)
                urgency = _compute_urgency(due_at)
                st.caption(f"Urgency: **{urgency}/5**")

            col_imp, _, col_preview = st.columns([2, 1, 1])
            with col_imp:
                importance = st.slider("User importance", 1, 5, 3, help="1 = low priority  |  5 = must-do", key="task_importance")
            with col_preview:
                _preview = TaskPriorityFactors(urgency=urgency, user_importance=importance)
                st.metric("Priority", _preview.to_label(weights), f"score {_preview.compute_score(weights):.1f}")

            with st.expander("Optional details"):
                instructions = st.text_area("Instructions", value="", placeholder="Any special notes...", key="task_instructions")
                col_rem, col_rec = st.columns(2)
                with col_rem:
                    reminder = st.number_input("Reminder (min before)", min_value=0, max_value=120, value=15, key="task_reminder")
                with col_rec:
                    is_recurring = st.checkbox("Recurring task", key="task_is_recurring")

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
                    "uid": pet_task.uid,
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
                    "status": TaskStatus.PENDING.name,
                    "pet_id": pet.uid,
                    "owner_id": st.session_state.selected_user_uid,
                })
                save_tasks(st.session_state.tasks)
                if conflict_warning:
                    st.session_state["_task_msg"] = ("warning", conflict_warning)
                else:
                    st.session_state["_task_msg"] = ("success", f"Task '{task_title}' added for {pet.name} ({owner_name}).")
                for k in _TASK_FORM_KEYS:
                    st.session_state.pop(k, None)
                st.rerun()

# ── Tab: My Tasks ───────────────────────────────────────────────────────────────
with tab_tasks:
    if pet is None:
        st.info("Select or add a pet above to see tasks.")
    elif pet.tasks:
        st.caption(f"Showing tasks for **{pet.name}** · owner: **{owner_name}**")
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
            col_card, col_del = st.columns([12, 1])
            with col_card:
                _render_task_card(t)
                if t.status != TaskStatus.COMPLETED:
                    if st.button("✓ Mark complete", key=f"complete_{t.uid}"):
                        scheduler.completeTask(pet, t.uid, datetime.now())
                        for saved in st.session_state.tasks:
                            if saved.get("uid") == t.uid:
                                saved["status"] = TaskStatus.COMPLETED.name
                                break
                        save_tasks(st.session_state.tasks)
                        st.rerun()
            with col_del:
                if st.button("🗑", key=f"delete_{t.uid}"):
                    pet.removeTask(t.uid)
                    st.session_state.tasks = [
                        s for s in st.session_state.tasks if s.get("uid") != t.uid
                    ]
                    save_tasks(st.session_state.tasks)
                    st.rerun()
    else:
        st.info("No tasks yet. Head to Add Task to get started.")

# ── Tab: Daily Schedule ─────────────────────────────────────────────────────────
with tab_schedule:
    if pet is None:
        st.info("Select or add a pet above to view the schedule.")
    else:
        schedule_date = st.date_input("Schedule date", value=date.today())
        agenda = scheduler.getPetAgenda(pet, schedule_date)
        if agenda:
            sorted_agenda = scheduler.sort_by_time(agenda)
            st.success(f"Schedule for {pet.name} ({owner_name}) — {schedule_date} | {len(sorted_agenda)} task(s)")

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
