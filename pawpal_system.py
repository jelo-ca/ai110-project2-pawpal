from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, time, datetime


@dataclass
class Animal:
    uid: str
    type: str
    breed: str
    
    def displayName(self) -> str:
        """Returns formatted display name of the animal"""
        pass


@dataclass
class Pet:
    uid: str
    name: str
    animal: Animal
    age: int
    birthDate: date
    weight: float
    medicalNotes: str = ""
    
    def updateInfo(self, name: str, animal: Animal, age: int) -> None:
        """Updates pet information"""
        pass
    
    def calculateAge(self, today: date) -> int:
        """Calculates age based on birth date"""
        pass
    
    def getUpcomingTasks(self, tasks: List['Task']) -> List['Task']:
        """Returns upcoming tasks for this pet"""
        pass


@dataclass
class Task:
    uid: str
    name: str
    description: str
    associatedPetId: str
    type: str
    duration: int
    startDate: date
    endDate: date
    startTime: time
    endTime: time
    status: str
    priority: str
    reminderMinutesBefore: int
    isRecurring: bool
    recurrenceRule: str = ""
    completedAt: Optional[datetime] = None
    
    def add(self) -> None:
        """Adds the task"""
        pass
    
    def edit(self, updates: Dict) -> None:
        """Edits task with provided updates"""
        pass
    
    def delete(self) -> None:
        """Deletes the task"""
        pass
    
    def markCompleted(self, completedAt: datetime) -> None:
        """Marks task as completed"""
        pass
    
    def isOverdue(self, now: datetime) -> bool:
        """Checks if task is overdue"""
        pass
    
    def setRecurring(self, rule: str) -> None:
        """Sets recurrence rule for the task"""
        pass
    
    def validateTimeRange(self) -> bool:
        """Validates that time range is valid"""
        pass
    
    def overlapsWith(self, other: 'Task') -> bool:
        """Checks if this task overlaps with another task"""
        pass
    
    def getStartDateTime(self) -> datetime:
        """Returns combined start date and time"""
        pass
    
    def getEndDateTime(self) -> datetime:
        """Returns combined end date and time"""
        pass


@dataclass
class User:
    uid: str
    name: str
    email: str
    address: str
    phoneNumber: str
    timezone: str
    pets: List[Pet] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    
    def addPet(self, pet: Pet) -> None:
        """Adds a pet to the user's pet list"""
        pass
    
    def removePet(self, petId: str) -> None:
        """Removes a pet from the user's pet list"""
        pass
    
    def addTask(self, task: Task) -> bool:
        """Adds a task to the user's task list"""
        pass
    
    def editTask(self, taskId: str, updates: Dict) -> bool:
        """Edits a task with provided updates"""
        pass
    
    def deleteTask(self, taskId: str) -> bool:
        """Deletes a task from the user's task list"""
        pass
    
    def hasTaskConflict(self, candidate: Task) -> bool:
        """Checks if a candidate task conflicts with existing tasks"""
        pass
    
    def getTasksByPet(self, petId: str) -> List[Task]:
        """Returns all tasks associated with a specific pet"""
        pass