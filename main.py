import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import date, datetime
from pawpal_system import Pet, PetTask, User, PetTaskScheduler, TaskStatus

# ── Optional pretty-print dependencies (graceful fallback if not installed) ──────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class _Noop:
        def __getattr__(self, _): return ""
    Fore = Style = _Noop()

try:
    from tabulate import tabulate as _tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# ── Emoji / badge maps ───────────────────────────────────────────────────────────
CARE_EMOJI = {
    "feeding":    "🍽️  feeding",
    "grooming":   "✂️  grooming",
    "exercise":   "🏃 exercise",
    "hygiene":    "🧹 hygiene",
    "medication": "💊 medication",
    "checkup":    "🩺 checkup",
    "general":    "📋 general",
    "other":      "📝 other",
}

STATUS_BADGE = {
    TaskStatus.PENDING:   "⏳ PENDING",
    TaskStatus.COMPLETED: "✅ DONE",
    TaskStatus.SKIPPED:   "⏭️  SKIPPED",
}

PRIORITY_BADGE = {
    "critical": "🚨 critical",
    "high":     "🔴 high",
    "medium":   "🟡 medium",
    "low":      "🟢 low",
}

# ── Helper formatters ────────────────────────────────────────────────────────────
def _care_cell(care_type: str) -> str:
    return CARE_EMOJI.get(care_type.lower(), f"📋 {care_type}")


def _priority_cell(priority: str) -> str:
    return PRIORITY_BADGE.get(priority.lower(), priority)


def _status_cell(status: TaskStatus) -> str:
    return STATUS_BADGE.get(status, status.name)


def _section(title: str) -> None:
    bar = "─" * (len(title) + 2)
    print(f"\n{Fore.CYAN}{Style.BRIGHT}┌{bar}┐")
    print(f"│ {title} │")
    print(f"└{bar}┘{Style.RESET_ALL}")


def _print_table(rows: list, headers: list) -> None:
    if HAS_TABULATE:
        print(_tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    else:
        # plain fallback
        widths = [max(len(str(r[i])) for r in ([headers] + rows)) for i in range(len(headers))]
        fmt = "  ".join(f"{{:<{w}}}" for w in widths)
        print(fmt.format(*headers))
        print("  ".join("─" * w for w in widths))
        for row in rows:
            print(fmt.format(*[str(c) for c in row]))


# ── Data setup ───────────────────────────────────────────────────────────────────
today = date.today()
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


def make_time(hour: int, minute: int = 0) -> datetime:
    return now.replace(hour=hour, minute=minute)


owner = User(uid="user-001", name="Bey", phoneNumber="555-0100", timezone="America/New_York")

simba = Pet(uid="pet-001", name="Simba", animalProfileId="profile-cat",
            birthDate=date(2022, 4, 10), weightKg=6.8, medicalNotes="Overweight; vet recommends diet food.")
kayne = Pet(uid="pet-002", name="Kayne", animalProfileId="profile-cat",
            birthDate=date(2022, 11, 3), weightKg=3.1)
owner.addPet(simba)
owner.addPet(kayne)

tasks = [
    PetTask(uid="task-001", petId="pet-001", title="Weight Control Meal", careType="feeding",
            instructions="Serve 1/4 cup of diet kibble. No treats.",
            dueAt=make_time(8),  startAt=make_time(8),    endAt=make_time(8, 10),
            estimatedMinutes=10, status=TaskStatus.PENDING, priority="high",
            reminderMinutesBefore=10, isRecurring=True, recurrenceRule="daily"),
    PetTask(uid="task-002", petId="pet-001", title="Brush Coat",          careType="grooming",
            instructions="Brush Simba's thick coat for 10 minutes to reduce shedding.",
            dueAt=make_time(9),  startAt=make_time(9),    endAt=make_time(9, 10),
            estimatedMinutes=10, status=TaskStatus.PENDING, priority="medium",
            reminderMinutesBefore=5, isRecurring=True, recurrenceRule="daily"),
    PetTask(uid="task-003", petId="pet-001", title="Exercise Play",       careType="exercise",
            instructions="Wand toy session to encourage movement. At least 15 minutes.",
            dueAt=make_time(11), startAt=make_time(11),   endAt=make_time(11, 15),
            estimatedMinutes=15, status=TaskStatus.PENDING, priority="high",
            reminderMinutesBefore=5, isRecurring=False, recurrenceRule=""),
    PetTask(uid="task-004", petId="pet-002", title="Morning Meal",        careType="feeding",
            instructions="Serve 1/3 cup of kitten kibble with a splash of water.",
            dueAt=make_time(8),  startAt=make_time(8),    endAt=make_time(8, 5),
            estimatedMinutes=5,  status=TaskStatus.PENDING, priority="high",
            reminderMinutesBefore=5, isRecurring=True, recurrenceRule="daily"),
    PetTask(uid="task-005", petId="pet-002", title="Litter Box Clean",    careType="hygiene",
            instructions="Scoop Kayne's litter box and replace as needed.",
            dueAt=make_time(10), startAt=make_time(10),   endAt=make_time(10, 10),
            estimatedMinutes=10, status=TaskStatus.PENDING, priority="medium",
            reminderMinutesBefore=5, isRecurring=True, recurrenceRule="daily"),
    PetTask(uid="task-006", petId="pet-002", title="Socialization Time",  careType="exercise",
            instructions="Spend 20 minutes playing with Kayne to build confidence.",
            dueAt=make_time(16), startAt=make_time(16),   endAt=make_time(16, 20),
            estimatedMinutes=20, status=TaskStatus.PENDING, priority="low",
            reminderMinutesBefore=5, isRecurring=False, recurrenceRule=""),
]

scheduler = PetTaskScheduler()
for task in tasks:
    scheduler.createTaskForPet(owner.getPet(task.petId), task)

# ── Today's Schedule ─────────────────────────────────────────────────────────────
_section(f"Today's Schedule — {today.strftime('%A, %B %d %Y')}  |  Owner: {owner.name}")

for pet in owner.pets:
    agenda = scheduler.getPetAgenda(pet, today)
    age = pet.calculateAge(today)
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}  🐾 {pet.name}  ({age} yr)  ·  {pet.weightKg} kg{Style.RESET_ALL}")
    if pet.medicalNotes:
        print(f"  {Fore.RED}⚕️  {pet.medicalNotes}{Style.RESET_ALL}")
    if not agenda:
        print("  No tasks scheduled for today.")
        continue
    rows = []
    for t in sorted(agenda, key=lambda t: t.startAt):
        time_range = f"{t.startAt.strftime('%I:%M %p')} – {t.endAt.strftime('%I:%M %p')}"
        rows.append([
            time_range,
            _care_cell(t.careType),
            t.title,
            _priority_cell(t.priority),
            "↩ recurring" if t.isRecurring else "—",
            _status_cell(t.status),
        ])
    _print_table(rows, ["Time", "Care Type", "Task", "Priority", "Recurs", "Status"])

# ── sort_by_time ──────────────────────────────────────────────────────────────────
all_tasks = [t for pet in owner.pets for t in pet.tasks]

_section("sort_by_time()")
rows = []
for t in scheduler.sort_by_time(all_tasks):
    pet_name = owner.getPet(t.petId).name
    rows.append([
        t.startAt.strftime("%I:%M %p"),
        f"🐾 {pet_name}",
        _care_cell(t.careType),
        t.title,
    ])
_print_table(rows, ["Start Time", "Pet", "Care Type", "Task"])

# ── sort_by_completion ────────────────────────────────────────────────────────────
# Mark a couple tasks complete/skipped so the sort is visible
tasks[0].status = TaskStatus.COMPLETED   # Simba – Weight Control Meal
tasks[4].status = TaskStatus.SKIPPED     # Kayne  – Litter Box Clean

_section("sort_by_completion()  (PENDING → COMPLETED → SKIPPED)")
rows = []
for t in scheduler.sort_by_completion(all_tasks):
    pet_name = owner.getPet(t.petId).name
    rows.append([
        _status_cell(t.status),
        f"🐾 {pet_name}",
        _care_cell(t.careType),
        t.title,
    ])
_print_table(rows, ["Status", "Pet", "Care Type", "Task"])

# ── sort_by_pet_name ──────────────────────────────────────────────────────────────
_section("sort_by_pet_name()")
rows = []
for t in scheduler.sort_by_pet_name(all_tasks, owner.pets):
    pet_name = owner.getPet(t.petId).name
    rows.append([
        f"🐾 {pet_name}",
        _care_cell(t.careType),
        t.title,
        _status_cell(t.status),
    ])
_print_table(rows, ["Pet", "Care Type", "Task", "Status"])

print()
