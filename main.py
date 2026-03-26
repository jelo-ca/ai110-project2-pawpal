from datetime import date, datetime
from pawpal_system import Pet, PetTask, User, PetTaskScheduler, TaskStatus

today = date.today()
now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def make_time(hour: int, minute: int = 0) -> datetime:
    return now.replace(hour=hour, minute=minute)

# Owner
owner = User(uid="user-001", name="Bey", phoneNumber="555-0100", timezone="America/New_York")

# Pets
simba = Pet(uid="pet-001", name="Simba", animalProfileId="profile-cat",
            birthDate=date(2022, 4, 10), weightKg=6.8, medicalNotes="Overweight; vet recommends diet food.")
kayne = Pet(uid="pet-002", name="Kayne", animalProfileId="profile-cat",
            birthDate=date(2022, 11, 3), weightKg=3.1)
owner.addPet(simba)
owner.addPet(kayne)

# Tasks
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

# Print Today's Schedule
print("=" * 50)
print(f"  Today's Schedule — {today.strftime('%A, %B %d %Y')}")
print(f"  Owner: {owner.name}")
print("=" * 50)

for pet in owner.pets:
    agenda = scheduler.getPetAgenda(pet, today)
    age = pet.calculateAge(today)
    print(f"\n  {pet.name}  ({age} yr old)  •  {pet.weightKg} kg")
    if pet.medicalNotes:
        print(f"  Note: {pet.medicalNotes}")
    print(f"  {'-' * 44}")
    if not agenda:
        print("  No tasks scheduled for today.")
        continue
    for task in sorted(agenda, key=lambda t: t.startAt):
        time_range = f"{task.startAt.strftime('%I:%M %p')} – {task.endAt.strftime('%I:%M %p')}"
        recur_tag = " [recurring]" if task.isRecurring else ""
        print(f"  {time_range}  [{task.priority.upper()}]  {task.title}{recur_tag}")
        print(f"    {task.instructions}")

print(f"\n{'=' * 50}\n")
