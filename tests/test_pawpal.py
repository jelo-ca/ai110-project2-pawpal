import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, timedelta
from pawpal_system import Pet, PetTask, TaskStatus, PetTaskScheduler


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


# --- Recurring Task Spawn on Completion ---

def make_recurring_task(uid="task-r", pet_id="pet-1", rule="daily"):
    base = datetime(2026, 3, 26, 8, 0, 0)
    return PetTask(
        uid=uid, petId=pet_id, title="Morning Meal", careType="feeding",
        instructions="Serve kibble.", dueAt=base, startAt=base,
        endAt=base + timedelta(minutes=10), estimatedMinutes=10,
        status=TaskStatus.PENDING, priority="high", reminderMinutesBefore=5,
        isRecurring=True, recurrenceRule=rule,
    )


class TestSchedulerCompleteTaskRecurring:
    def _setup(self, rule="daily"):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_recurring_task(rule=rule)
        scheduler.createTaskForPet(pet, task)
        return scheduler, pet, task

    # --- daily recurrence ---

    def test_recurring_daily_returns_new_task(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task is not None

    def test_recurring_daily_new_task_is_pending(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.status == TaskStatus.PENDING

    def test_recurring_daily_next_due_is_plus_one_day(self):
        scheduler, pet, task = self._setup("daily")
        original_due = task.dueAt
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.dueAt == original_due + timedelta(days=1)

    def test_recurring_daily_duration_preserved(self):
        scheduler, pet, task = self._setup("daily")
        original_duration = task.endAt - task.startAt
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.endAt - new_task.startAt == original_duration

    def test_recurring_daily_new_task_added_to_pet(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task in pet.tasks

    def test_recurring_daily_new_task_registered_in_scheduler(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.uid in scheduler._tasks

    def test_recurring_daily_original_marked_completed(self):
        scheduler, pet, task = self._setup("daily")
        scheduler.completeTask(pet, task.uid, datetime.now())
        assert task.status == TaskStatus.COMPLETED

    def test_recurring_daily_next_due_at_updated_on_original(self):
        scheduler, pet, task = self._setup("daily")
        original_due = task.dueAt
        scheduler.completeTask(pet, task.uid, datetime.now())
        assert task.nextDueAt == original_due + timedelta(days=1)

    def test_recurring_daily_new_task_has_unique_uid(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.uid != task.uid

    def test_recurring_daily_new_task_inherits_metadata(self):
        scheduler, pet, task = self._setup("daily")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.title == task.title
        assert new_task.careType == task.careType
        assert new_task.petId == task.petId
        assert new_task.recurrenceRule == task.recurrenceRule
        assert new_task.isRecurring is True

    # --- weekly recurrence ---

    def test_recurring_weekly_returns_new_task(self):
        scheduler, pet, task = self._setup("weekly")
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task is not None

    def test_recurring_weekly_next_due_is_plus_seven_days(self):
        scheduler, pet, task = self._setup("weekly")
        original_due = task.dueAt
        new_task = scheduler.completeTask(pet, task.uid, datetime.now())
        assert new_task.dueAt == original_due + timedelta(weeks=1)

    # --- non-recurring task ---

    def test_non_recurring_returns_none(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_task()  # isRecurring=False
        scheduler.createTaskForPet(pet, task)
        result = scheduler.completeTask(pet, task.uid, datetime.now())
        assert result is None

    def test_non_recurring_still_marks_completed(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_task()
        scheduler.createTaskForPet(pet, task)
        scheduler.completeTask(pet, task.uid, datetime.now())
        assert task.status == TaskStatus.COMPLETED

    def test_non_recurring_no_new_task_added(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        task = make_task()
        scheduler.createTaskForPet(pet, task)
        count_before = len(pet.tasks)
        scheduler.completeTask(pet, task.uid, datetime.now())
        assert len(pet.tasks) == count_before

    # --- unknown recurrence rule ---

    def test_unknown_rule_returns_none(self):
        scheduler, pet, task = self._setup("monthly")
        result = scheduler.completeTask(pet, task.uid, datetime.now())
        assert result is None

    def test_unknown_rule_still_marks_completed(self):
        scheduler, pet, task = self._setup("monthly")
        scheduler.completeTask(pet, task.uid, datetime.now())
        assert task.status == TaskStatus.COMPLETED

    # --- invalid task id ---

    def test_invalid_task_id_returns_none(self):
        scheduler = PetTaskScheduler()
        pet = make_pet()
        result = scheduler.completeTask(pet, "nonexistent-id", datetime.now())
        assert result is None


# --- Conflict Warning Tests ---

def make_task_at(uid, start: datetime, duration_minutes=15, pet_id="pet-1"):
    return PetTask(
        uid=uid,
        petId=pet_id,
        title=f"Task {uid}",
        careType="feeding",
        instructions="",
        dueAt=start,
        startAt=start,
        endAt=start + timedelta(minutes=duration_minutes),
        estimatedMinutes=duration_minutes,
        status=TaskStatus.PENDING,
        priority="medium",
        reminderMinutesBefore=5,
        isRecurring=False,
    )


class TestWarnConflict:
    BASE = datetime(2026, 3, 26, 9, 0, 0)

    def _scheduler_and_pet(self):
        return PetTaskScheduler(), make_pet()

    def test_no_conflict_returns_empty_string(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE + timedelta(hours=1))
        assert scheduler.warnConflict(candidate) == ""

    def test_same_start_returns_warning(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert warning != ""
        assert "Warning:" in warning

    def test_warning_names_conflicting_task(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert existing.title in warning

    def test_warning_names_candidate_task(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert candidate.title in warning

    def test_warning_includes_time(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert "09:00" in warning

    def test_no_tasks_in_scheduler_returns_empty_string(self):
        scheduler = PetTaskScheduler()
        candidate = make_task_at("t1", self.BASE)
        assert scheduler.warnConflict(candidate) == ""

    def test_candidate_already_registered_not_self_conflicting(self):
        scheduler, pet = self._scheduler_and_pet()
        task = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, task)
        assert scheduler.warnConflict(task) == ""

    def test_completed_task_ignored(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        existing.status = TaskStatus.COMPLETED
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        assert scheduler.warnConflict(candidate) == ""

    def test_skipped_task_ignored(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        existing.status = TaskStatus.SKIPPED
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        assert scheduler.warnConflict(candidate) == ""

    def test_multiple_conflicts_all_named(self):
        scheduler, pet = self._scheduler_and_pet()
        t1 = make_task_at("t1", self.BASE)
        t2 = make_task_at("t2", self.BASE)
        scheduler.createTaskForPet(pet, t1)
        scheduler.createTaskForPet(pet, t2)
        candidate = make_task_at("t3", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert t1.title in warning
        assert t2.title in warning

    # --- multi-pet conflict tests ---

    def test_cross_pet_conflict_detected(self):
        scheduler = PetTaskScheduler()
        pet_a = make_pet(uid="pet-1")
        pet_b = make_pet(uid="pet-2")
        task_a = make_task_at("ta", self.BASE, pet_id="pet-1")
        task_b = make_task_at("tb", self.BASE, pet_id="pet-2")
        scheduler.createTaskForPet(pet_a, task_a)
        scheduler.createTaskForPet(pet_b, task_b)
        # candidate for pet-1 at same time as pet-2's task
        candidate = make_task_at("tc", self.BASE, pet_id="pet-1")
        warning = scheduler.warnConflict(candidate)
        assert warning != ""
        assert task_a.title in warning  # same-pet conflict
        assert task_b.title in warning  # cross-pet conflict

    def test_cross_pet_warning_labels_other_pet(self):
        scheduler = PetTaskScheduler()
        pet_a = make_pet(uid="pet-1")
        pet_b = make_pet(uid="pet-2")
        task_b = make_task_at("tb", self.BASE, pet_id="pet-2")
        scheduler.createTaskForPet(pet_b, task_b)
        candidate = make_task_at("tc", self.BASE, pet_id="pet-1")
        warning = scheduler.warnConflict(candidate)
        assert "pet-2" in warning  # cross-pet context shown

    def test_same_pet_conflict_no_extra_label(self):
        scheduler, pet = self._scheduler_and_pet()
        existing = make_task_at("t1", self.BASE)
        scheduler.createTaskForPet(pet, existing)
        candidate = make_task_at("t2", self.BASE)
        warning = scheduler.warnConflict(candidate)
        assert "pet-1" not in warning  # same pet — no redundant label

    def test_no_cross_pet_conflict_different_times(self):
        scheduler = PetTaskScheduler()
        pet_a = make_pet(uid="pet-1")
        pet_b = make_pet(uid="pet-2")
        task_a = make_task_at("ta", self.BASE, pet_id="pet-1")
        task_b = make_task_at("tb", self.BASE + timedelta(hours=1), pet_id="pet-2")
        scheduler.createTaskForPet(pet_a, task_a)
        scheduler.createTaskForPet(pet_b, task_b)
        candidate = make_task_at("tc", self.BASE, pet_id="pet-1")
        warning = scheduler.warnConflict(candidate)
        assert task_b.title not in warning


class TestPawPalSystem:

    def setup_method(self):
        self.pet = Pet(
            uid="pet1",
            name="Buddy",
            animalProfileId="profile1",
            birthDate=date(2020, 5, 20),
            weightKg=10.0
        )
        self.scheduler = PetTaskScheduler()

    def test_calculate_age(self):
        today = date(2026, 3, 26)
        assert self.pet.calculateAge(today) == 5

        # Edge case: Birthday today
        today = date(2026, 5, 20)
        assert self.pet.calculateAge(today) == 6

        # Edge case: Leap year
        self.pet.birthDate = date(2020, 2, 29)
        today = date(2024, 2, 28)
        assert self.pet.calculateAge(today) == 3

    def test_add_task(self):
        task = PetTask(
            uid="task1",
            petId="pet1",
            title="Morning Walk",
            careType="Exercise",
            instructions="Take Buddy for a 30-minute walk.",
            dueAt=datetime(2026, 3, 27, 8, 0),
            startAt=datetime(2026, 3, 27, 8, 0),
            endAt=datetime(2026, 3, 27, 8, 30),
            estimatedMinutes=30,
            status=TaskStatus.PENDING,
            priority="High",
            reminderMinutesBefore=15,
            isRecurring=False
        )
        assert self.pet.addTask(task) is True
        assert task in self.pet.tasks

    def test_update_task(self):
        task = PetTask(
            uid="task1",
            petId="pet1",
            title="Morning Walk",
            careType="Exercise",
            instructions="Take Buddy for a 30-minute walk.",
            dueAt=datetime(2026, 3, 27, 8, 0),
            startAt=datetime(2026, 3, 27, 8, 0),
            endAt=datetime(2026, 3, 27, 8, 30),
            estimatedMinutes=30,
            status=TaskStatus.PENDING,
            priority="High",
            reminderMinutesBefore=15,
            isRecurring=False
        )
        self.pet.addTask(task)
        updates = {"title": "Evening Walk", "priority": "Medium"}
        assert self.pet.updateTask("task1", updates) is True
        assert task.title == "Evening Walk"
        assert task.priority == "Medium"

    def test_task_conflict_detection(self):
        task1 = PetTask(
            uid="task1",
            petId="pet1",
            title="Morning Walk",
            careType="Exercise",
            instructions="Take Buddy for a 30-minute walk.",
            dueAt=datetime(2026, 3, 27, 8, 0),
            startAt=datetime(2026, 3, 27, 8, 0),
            endAt=datetime(2026, 3, 27, 8, 30),
            estimatedMinutes=30,
            status=TaskStatus.PENDING,
            priority="High",
            reminderMinutesBefore=15,
            isRecurring=False
        )
        task2 = PetTask(
            uid="task2",
            petId="pet1",
            title="Vet Appointment",
            careType="Health",
            instructions="Visit the vet for a check-up.",
            dueAt=datetime(2026, 3, 27, 8, 15),
            startAt=datetime(2026, 3, 27, 8, 15),
            endAt=datetime(2026, 3, 27, 9, 0),
            estimatedMinutes=45,
            status=TaskStatus.PENDING,
            priority="High",
            reminderMinutesBefore=30,
            isRecurring=False
        )
        self.pet.addTask(task1)
        conflicts = self.scheduler.detectPetTaskConflicts(self.pet, task2)
        assert task1 in conflicts

    def test_recurring_task_scheduling(self):
        task = PetTask(
            uid="task1",
            petId="pet1",
            title="Daily Walk",
            careType="Exercise",
            instructions="Take Buddy for a walk.",
            dueAt=datetime(2026, 3, 26, 8, 0),
            startAt=datetime(2026, 3, 26, 8, 0),
            endAt=datetime(2026, 3, 26, 8, 30),
            estimatedMinutes=30,
            status=TaskStatus.PENDING,
            priority="Medium",
            reminderMinutesBefore=15,
            isRecurring=True,
            recurrenceRule="daily"
        )
        self.pet.addTask(task)
        scheduled_tasks = self.scheduler.autoScheduleRecurringTasks(self.pet, 3)
        assert len(scheduled_tasks) == 3
        assert scheduled_tasks[0].dueAt == datetime(2026, 3, 27, 8, 0)
        assert scheduled_tasks[1].dueAt == datetime(2026, 3, 28, 8, 0)
        assert scheduled_tasks[2].dueAt == datetime(2026, 3, 29, 8, 0)
