import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime
from pawpal_system import Pet, PetTask, PetTaskScheduler, TaskStatus


# --- Fixtures ---

def make_pet(uid="pet-1"):
    return Pet(
        uid=uid,
        name="Buddy",
        animalProfileId="profile-1",
        birthDate=date(2020, 1, 1),
        weightKg=10.0,
    )


def make_task(uid="task-1", pet_id="pet-1", due_offset_hours=1):
    now = datetime(2026, 3, 26, 10, 0, 0)
    due = datetime(2026, 3, 26, 10 + due_offset_hours, 0, 0)
    return PetTask(
        uid=uid,
        petId=pet_id,
        title="Feed Buddy",
        careType="feeding",
        instructions="1 cup dry food",
        dueAt=due,
        startAt=now,
        endAt=datetime(2026, 3, 26, 10 + due_offset_hours, 15, 0),
        estimatedMinutes=15,
        status=TaskStatus.PENDING,
        priority="high",
        reminderMinutesBefore=10,
        isRecurring=False,
    )


# --- Task Addition Tests ---

class TestAddTask:
    def test_add_task_success(self):
        pet = make_pet()
        task = make_task()
        result = pet.addTask(task)
        assert result is True
        assert task in pet.tasks

    def test_add_task_appends_to_list(self):
        pet = make_pet()
        task1 = make_task(uid="task-1")
        task2 = make_task(uid="task-2")
        pet.addTask(task1)
        pet.addTask(task2)
        assert len(pet.tasks) == 2

    def test_add_task_wrong_pet_id_fails(self):
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="pet-999")
        result = pet.addTask(task)
        assert result is False
        assert task not in pet.tasks

    def test_add_task_does_not_add_on_failure(self):
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="other-pet")
        pet.addTask(task)
        assert len(pet.tasks) == 0


# --- Task Completion Tests ---

class TestCompleteTask:
    def test_complete_task_returns_true(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        completed_at = datetime(2026, 3, 26, 11, 5, 0)
        result = pet.completeTask("task-1", completed_at)
        assert result is True

    def test_complete_task_sets_status(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        completed_at = datetime(2026, 3, 26, 11, 5, 0)
        pet.completeTask("task-1", completed_at)
        assert task.status == TaskStatus.COMPLETED

    def test_complete_task_sets_last_completed_at(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        completed_at = datetime(2026, 3, 26, 11, 5, 0)
        pet.completeTask("task-1", completed_at)
        assert task.lastCompletedAt == completed_at

    def test_complete_nonexistent_task_returns_false(self):
        pet = make_pet()
        result = pet.completeTask("nonexistent-id", datetime.now())
        assert result is False

    def test_complete_task_wrong_id_does_not_affect_others(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        pet.completeTask("wrong-id", datetime.now())
        assert task.status == TaskStatus.PENDING


# --- Scheduler Task Creation Tests ---

class TestSchedulerCreateTask:
    def test_scheduler_creates_task_on_pet(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_task()
        result = scheduler.createTaskForPet(pet, task)
        assert result is True
        assert task in pet.tasks

    def test_scheduler_registers_task_internally(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_task()
        scheduler.createTaskForPet(pet, task)
        assert "task-1" in scheduler._tasks

    def test_scheduler_rejects_task_wrong_pet(self):
        scheduler = PetTaskScheduler()
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="pet-999")
        result = scheduler.createTaskForPet(pet, task)
        assert result is False
        assert task not in pet.tasks
        assert "task-1" not in scheduler._tasks
