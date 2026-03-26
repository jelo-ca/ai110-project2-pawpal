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


# --- Extreme Edge Cases: Task Addition ---

class TestAddTaskEdgeCases:
    def test_add_task_empty_string_uid(self):
        # Task whose petId is empty string never matches any real pet uid
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="")
        result = pet.addTask(task)
        assert result is False
        assert len(pet.tasks) == 0

    def test_add_task_pet_uid_empty_string(self):
        # Pet with empty uid — task petId must match exactly
        pet = make_pet(uid="")
        task = make_task(pet_id="")
        result = pet.addTask(task)
        assert result is True
        assert task in pet.tasks

    def test_add_task_uid_case_sensitive(self):
        # "Pet-1" != "pet-1" — IDs are case-sensitive
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="Pet-1")
        result = pet.addTask(task)
        assert result is False

    def test_add_task_very_long_uid(self):
        long_id = "x" * 10_000
        pet = make_pet(uid=long_id)
        task = make_task(pet_id=long_id)
        result = pet.addTask(task)
        assert result is True

    def test_add_task_unicode_uid(self):
        uid = "宠物-🐾-①"
        pet = make_pet(uid=uid)
        task = make_task(pet_id=uid)
        result = pet.addTask(task)
        assert result is True

    def test_add_task_whitespace_only_uid_no_match(self):
        pet = make_pet(uid="pet-1")
        task = make_task(pet_id="   ")
        result = pet.addTask(task)
        assert result is False

    def test_add_task_very_long_title(self):
        pet = make_pet()
        task = make_task()
        task.title = "A" * 100_000
        result = pet.addTask(task)
        assert result is True
        assert pet.tasks[0].title == "A" * 100_000

    def test_add_task_newline_in_instructions(self):
        pet = make_pet()
        task = make_task()
        task.instructions = "Step 1\nStep 2\nStep 3\n" * 1_000
        result = pet.addTask(task)
        assert result is True

    def test_add_same_task_object_twice(self):
        # addTask has no duplicate guard — same object added twice appears twice
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        pet.addTask(task)
        assert len(pet.tasks) == 2

    def test_add_many_tasks(self):
        pet = make_pet()
        for i in range(1_000):
            t = make_task(uid=f"task-{i}")
            pet.addTask(t)
        assert len(pet.tasks) == 1_000

    def test_add_task_negative_estimated_minutes(self):
        pet = make_pet()
        task = make_task()
        task.estimatedMinutes = -999
        result = pet.addTask(task)
        # No validation in addTask — it stores whatever is given
        assert result is True

    def test_add_task_zero_weight_pet(self):
        pet = Pet(
            uid="pet-1",
            name="Ghost",
            animalProfileId="ap-1",
            birthDate=date(2020, 1, 1),
            weightKg=0.0,
        )
        task = make_task()
        result = pet.addTask(task)
        assert result is True

    def test_add_task_future_birth_date(self):
        # Pet born in the future — addTask itself doesn't validate birth dates
        pet = Pet(
            uid="pet-1",
            name="Future",
            animalProfileId="ap-1",
            birthDate=date(2099, 12, 31),
            weightKg=5.0,
        )
        task = make_task()
        result = pet.addTask(task)
        assert result is True


# --- Extreme Edge Cases: Task Completion ---

class TestCompleteTaskEdgeCases:
    def test_complete_task_empty_string_id(self):
        pet = make_pet()
        result = pet.completeTask("", datetime.now())
        assert result is False

    def test_complete_task_whitespace_id(self):
        pet = make_pet()
        task = make_task(uid="task-1")
        pet.addTask(task)
        result = pet.completeTask("  task-1  ", datetime.now())
        assert result is False  # IDs are not stripped — no match
        assert task.status == TaskStatus.PENDING

    def test_complete_task_case_sensitive_id(self):
        pet = make_pet()
        task = make_task(uid="task-1")
        pet.addTask(task)
        result = pet.completeTask("TASK-1", datetime.now())
        assert result is False
        assert task.status == TaskStatus.PENDING

    def test_complete_task_very_long_id_no_match(self):
        pet = make_pet()
        result = pet.completeTask("z" * 10_000, datetime.now())
        assert result is False

    def test_complete_task_already_completed_updates_timestamp(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        first_time = datetime(2026, 1, 1, 8, 0, 0)
        second_time = datetime(2026, 6, 1, 9, 0, 0)
        pet.completeTask("task-1", first_time)
        pet.completeTask("task-1", second_time)
        assert task.lastCompletedAt == second_time

    def test_complete_task_far_future_timestamp(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        far_future = datetime(9999, 12, 31, 23, 59, 59)
        result = pet.completeTask("task-1", far_future)
        assert result is True
        assert task.lastCompletedAt == far_future

    def test_complete_task_epoch_timestamp(self):
        pet = make_pet()
        task = make_task()
        pet.addTask(task)
        epoch = datetime(1970, 1, 1, 0, 0, 0)
        result = pet.completeTask("task-1", epoch)
        assert result is True
        assert task.lastCompletedAt == epoch

    def test_complete_task_only_target_mutated(self):
        # Completing one task must not touch sibling tasks
        pet = make_pet()
        task_a = make_task(uid="task-a")
        task_b = make_task(uid="task-b")
        pet.addTask(task_a)
        pet.addTask(task_b)
        pet.completeTask("task-a", datetime.now())
        assert task_a.status == TaskStatus.COMPLETED
        assert task_b.status == TaskStatus.PENDING

    def test_complete_task_no_tasks_on_pet(self):
        pet = make_pet()
        result = pet.completeTask("task-1", datetime.now())
        assert result is False

    def test_complete_task_unicode_id(self):
        uid = "任务-🐕-001"
        pet = make_pet()
        task = make_task(uid=uid)
        pet.addTask(task)
        result = pet.completeTask(uid, datetime.now())
        assert result is True
        assert task.status == TaskStatus.COMPLETED


# --- Extreme Edge Cases: Scheduler ---

class TestSchedulerEdgeCases:
    def test_scheduler_add_task_empty_pet_uid(self):
        scheduler = PetTaskScheduler()
        pet = make_pet(uid="")
        task = make_task(pet_id="")
        result = scheduler.createTaskForPet(pet, task)
        assert result is True

    def test_scheduler_same_task_added_to_two_pets_fails_second(self):
        scheduler = PetTaskScheduler()
        pet_a = make_pet(uid="pet-1")
        pet_b = make_pet(uid="pet-2")
        task = make_task(pet_id="pet-1")
        scheduler.createTaskForPet(pet_a, task)
        result = scheduler.createTaskForPet(pet_b, task)
        assert result is False
        assert task not in pet_b.tasks

    def test_scheduler_internal_registry_not_polluted_on_rejection(self):
        scheduler = PetTaskScheduler()
        pet = make_pet(uid="pet-1")
        task = make_task(uid="task-x", pet_id="pet-999")
        scheduler.createTaskForPet(pet, task)
        assert "task-x" not in scheduler._tasks

    def test_scheduler_handles_1000_tasks(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        for i in range(1_000):
            t = make_task(uid=f"bulk-{i}")
            scheduler.createTaskForPet(pet, t)
        assert len(pet.tasks) == 1_000
        assert len(scheduler._tasks) == 1_000
