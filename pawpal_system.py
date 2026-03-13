from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List
from enum import Enum, auto


class TaskStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()



@dataclass
class AnimalProfile:
    uid: str
    species: str
    breed: str
    lifeStage: str
    defaultCareGuidelines: str
    
    def displayName(self) -> str:
        """Returns formatted display name of the animal profile."""
        pass


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
        pass
    
    def calculateAge(self, today: date) -> int:
        """Calculates age based on birth date."""
        pass
    
    def addTask(self, task: "PetTask") -> bool:
        """Adds a task to this pet's task list."""
        pass

    def updateTask(self, taskId: str, updates: Dict) -> bool:
        """Updates a task associated with this pet."""
        pass

    def completeTask(self, taskId: str, completedAt: datetime) -> bool:
        """Marks a task as complete for this pet."""
        pass

    def getDueTasks(self, windowStart: datetime, windowEnd: datetime) -> List["PetTask"]:
        """Returns tasks due in the provided time window."""
        pass
    
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
        pass
    
    def removePet(self, petId: str) -> None:
        """Removes a pet from the user's pet list."""
        pass
    
    def getPet(self, petId: str) -> Pet:
        """Returns the pet that matches the provided pet ID."""
        pass
    
    def getUpcomingPetTasks(self, days: int) -> List["PetTask"]:
        """Returns upcoming tasks across all pets within the given window."""
        pass
    
    def __repr__(self):
        """Returns a string representation of the user."""
        return f"<User name={self.name}>"
    
class PetTaskScheduler:
    """Scheduler for creating and managing pet tasks."""

    def createTaskForPet(self, pet: Pet, task: PetTask) -> bool:
        """Creates a task for a specific pet."""
        pass

    def detectPetTaskConflicts(self, pet: Pet, candidate: PetTask) -> List[PetTask]:
        """Detects scheduling conflicts for a pet task candidate."""
        pass

    def autoScheduleRecurringTasks(self, pet: Pet, windowDays: int) -> List[PetTask]:
        """Auto-schedules recurring tasks for a pet."""
        pass

    def getPetAgenda(self, pet: Pet, day: date) -> List[PetTask]:
        """Returns all tasks for a pet on the provided day."""
        pass

    def skipTask(self, taskId: str, reason: str) -> bool:
        """Skips a task with a reason."""
        pass