from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List
from enum import Enum, auto


class TaskStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    SKIPPED = auto()



@dataclass
class AnimalProfile:
    uid: str
    species: str
    breed: str
    lifeStage: str
    defaultCareGuidelines: str
    
    def displayName(self) -> str:
        """Returns formatted display name of the animal profile."""
        return f"{self.breed} ({self.species}) - {self.lifeStage}"


@dataclass
class Pet:
    uid: str
    name: str
    animalProfileId: str
    birthDate: date
    weightKg: float
    medicalNotes: str = ""
    tasks: List["PetTask"] = field(default_factory=list)
    
    def updateInfo(self, name: str, weightKg: float, medicalNotes: str) -> None:
        """Updates pet information."""
        self.name = name
        self.weightKg = weightKg
        self.medicalNotes = medicalNotes

    def calculateAge(self, today: date) -> int:
        """Calculates age based on birth date."""
        age = today.year - self.birthDate.year
        if (today.month, today.day) < (self.birthDate.month, self.birthDate.day):
            age -= 1
        return age

    def addTask(self, task: "PetTask") -> bool:
        """Adds a task to this pet's task list."""
        if task.petId != self.uid:
            return False
        self.tasks.append(task)
        return True

    def updateTask(self, taskId: str, updates: Dict) -> bool:
        """Updates a task associated with this pet."""
        for task in self.tasks:
            if task.uid == taskId:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                return True
        return False

    def completeTask(self, taskId: str, completedAt: datetime) -> bool:
        """Marks a task as complete for this pet."""
        for task in self.tasks:
            if task.uid == taskId:
                task.status = TaskStatus.COMPLETED
                task.lastCompletedAt = completedAt
                return True
        return False

    def getDueTasks(self, windowStart: datetime, windowEnd: datetime) -> List["PetTask"]:
        """Returns tasks due in the provided time window."""
        return [t for t in self.tasks if windowStart <= t.dueAt <= windowEnd]
    
    def __repr__(self) -> str:
        """Returns a string representation of the pet."""
        return f"<Pet name={self.name}>"


@dataclass
class PetTask:
    uid: str
    petId: str
    title: str
    careType: str
    instructions: str
    dueAt: datetime
    startAt: datetime
    endAt: datetime
    estimatedMinutes: int
    status: TaskStatus
    priority: str
    reminderMinutesBefore: int
    isRecurring: bool
    recurrenceRule: str = ""
    lastCompletedAt: datetime = None
    nextDueAt: datetime = None
    
    def validateForPet(self, p: Pet) -> bool:
        """Validates if the task can be assigned to the pet."""
        if self.petId != p.uid:
            return False
        return True

    def markCompleted(self) -> None:
        """Marks the task as completed and updates status."""
        self.status = TaskStatus.COMPLETED
        self.lastCompletedAt = datetime.now()

    def reschedule(self, newDueAt=None, newStartAt=None, newEndAt=None) -> None:
        """Reschedules the task start, end, OR due time."""
        if newDueAt is not None:
            self.dueAt = newDueAt
        if newStartAt is not None:
            self.startAt = newStartAt
        if newEndAt is not None:
            self.endAt = newEndAt
    
    def isOverdue(self) -> bool:
        """Checks if task is overdue."""
        return self.status == TaskStatus.PENDING and self.dueAt < datetime.now()
    
    def __repr__(self) -> str:
        """Returns a string representation of the pet task."""
        return f"<Task={self.title} startTime={self.startAt.time()} endTime={self.endAt.time()} dueAt={self.dueAt} status={self.status.name}>"


@dataclass
class User:
    uid: str
    name: str
    phoneNumber: str
    timezone: str
    pets: List[Pet] = field(default_factory=list)
    
    def addPet(self, pet: Pet) -> None:
        """Adds a pet to the user's pet list."""
        self.pets.append(pet)

    def removePet(self, petId: str) -> None:
        """Removes a pet from the user's pet list."""
        self.pets = [p for p in self.pets if p.uid != petId]

    def getPet(self, petId: str) -> Pet:
        """Returns the pet that matches the provided pet ID."""
        for pet in self.pets:
            if pet.uid == petId:
                return pet
        return None

    def getUpcomingPetTasks(self, days: int) -> List["PetTask"]:
        """Returns upcoming tasks across all pets within the given window."""
        now = datetime.now()
        window_end = now + timedelta(days=days)
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.getDueTasks(now, window_end))
        return tasks
    
    def __repr__(self):
        """Returns a string representation of the user."""
        return f"<User name={self.name}>"
    
class PetTaskScheduler:
    """Scheduler for creating and managing pet tasks."""

    def __init__(self):
        self._tasks: Dict[str, PetTask] = {}

    def createTaskForPet(self, pet: Pet, task: PetTask) -> bool:
        """Creates a task for a specific pet."""
        if not pet.addTask(task):
            return False
        self._tasks[task.uid] = task
        return True

    def detectPetTaskConflicts(self, pet: Pet, candidate: PetTask) -> List[PetTask]:
        """Detects scheduling conflicts for a pet task candidate."""
        return [
            t for t in pet.tasks
            if t.uid != candidate.uid
            and t.status == TaskStatus.PENDING
            and t.startAt < candidate.endAt
            and t.endAt > candidate.startAt
        ]

    def autoScheduleRecurringTasks(self, pet: Pet, windowDays: int) -> List[PetTask]:
        """Auto-schedules recurring tasks for a pet."""
        import uuid

        scheduled = []
        window_end = datetime.now() + timedelta(days=windowDays)
        deltas = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}

        for task in list(pet.tasks):
            if not task.isRecurring or task.recurrenceRule.lower() not in deltas:
                continue
            delta = deltas[task.recurrenceRule.lower()]
            duration = task.endAt - task.startAt
            current = (task.nextDueAt or task.dueAt) + delta

            while current <= window_end:
                new_task = PetTask(
                    uid=str(uuid.uuid4()),
                    petId=task.petId,
                    title=task.title,
                    careType=task.careType,
                    instructions=task.instructions,
                    dueAt=current,
                    startAt=current,
                    endAt=current + duration,
                    estimatedMinutes=task.estimatedMinutes,
                    status=TaskStatus.PENDING,
                    priority=task.priority,
                    reminderMinutesBefore=task.reminderMinutesBefore,
                    isRecurring=task.isRecurring,
                    recurrenceRule=task.recurrenceRule,
                )
                pet.tasks.append(new_task)
                self._tasks[new_task.uid] = new_task
                scheduled.append(new_task)
                current += delta

            task.nextDueAt = current
        return scheduled

    def getPetAgenda(self, pet: Pet, day: date) -> List[PetTask]:
        """Returns all tasks for a pet on the provided day."""
        return [t for t in pet.tasks if t.dueAt.date() == day]

    def sort_by_time(self, tasks: List[PetTask]) -> List[PetTask]:
        """Returns tasks sorted by startAt time."""
        return sorted(tasks, key=lambda t: t.startAt)

    def skipTask(self, taskId: str, reason: str) -> bool:
        """Skips a task with a reason."""
        task = self._tasks.get(taskId)
        if task is None:
            return False
        task.status = TaskStatus.SKIPPED
        return True