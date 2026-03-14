"""
Pytest suite for PetTask and Pet.

PetTask tests cover all four implemented methods:
  - validateForPet, markCompleted, reschedule, isOverdue

Pet tests are marked xfail because the methods are still stubs (pass).
Remove @pytest.mark.xfail from each Pet test as you implement it.
"""

import pytest
from datetime import date, datetime, timedelta

from pawpal_system import Pet, PetTask, TaskStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pet():
    return Pet(
        uid="pet-001",
        name="Simba",
        animalProfileId="ap-001",
        birthDate=date(2020, 5, 15),
        weightKg=15.5,
        medicalNotes="Mild seasonal allergies.",
    )


@pytest.fixture
def other_pet():
    return Pet(
        uid="pet-999",
        name="Other",
        animalProfileId="ap-002",
        birthDate=date(2019, 1, 1),
        weightKg=5.0,
    )


def make_task(
    uid="task-001",
    pet_uid="pet-001",
    due_offset_hours: int = 1,
    status: TaskStatus = TaskStatus.PENDING,
) -> PetTask:
    """Helper – creates a PetTask relative to now."""
    now = datetime.now()
    due = now + timedelta(hours=due_offset_hours)
    return PetTask(
        uid=uid,
        petId=pet_uid,
        title="Morning Walk",
        careType="Exercise",
        instructions="30 min walk.",
        dueAt=due,
        startAt=due,
        endAt=due + timedelta(minutes=30),
        estimatedMinutes=30,
        status=status,
        priority="high",
        reminderMinutesBefore=15,
        isRecurring=False,
    )


@pytest.fixture
def pending_future_task(pet):
    """A PENDING task due in the future – not overdue."""
    return make_task(due_offset_hours=24)


@pytest.fixture
def pending_past_task(pet):
    """A PENDING task due in the past – overdue."""
    return make_task(due_offset_hours=-1)


@pytest.fixture
def completed_past_task(pet):
    """A COMPLETED task due in the past – should not be overdue."""
    return make_task(due_offset_hours=-1, status=TaskStatus.COMPLETED)


# ---------------------------------------------------------------------------
# PetTask.validateForPet
# ---------------------------------------------------------------------------

class TestValidateForPet:
    def test_returns_true_when_petId_matches(self, pet, pending_future_task):
        assert pending_future_task.validateForPet(pet) is True

    def test_returns_false_when_petId_mismatches(self, other_pet, pending_future_task):
        assert pending_future_task.validateForPet(other_pet) is False

    def test_returns_false_when_task_has_empty_petId(self, pet):
        """Edge case: task with an empty-string petId never matches any pet."""
        task = make_task(pet_uid="")
        assert task.validateForPet(pet) is False

    def test_returns_false_when_pet_uid_is_different_case(self, pet):
        """Edge case: petId comparison is case-sensitive."""
        task = make_task(pet_uid="PET-001")  # uppercase vs 'pet-001'
        assert task.validateForPet(pet) is False


# ---------------------------------------------------------------------------
# PetTask.markCompleted
# ---------------------------------------------------------------------------

class TestMarkCompleted:
    def test_status_becomes_completed(self, pending_future_task):
        pending_future_task.markCompleted()
        assert pending_future_task.status == TaskStatus.COMPLETED

    def test_lastCompletedAt_is_set(self, pending_future_task):
        before = datetime.now()
        pending_future_task.markCompleted()
        after = datetime.now()
        assert before <= pending_future_task.lastCompletedAt <= after

    def test_calling_twice_updates_lastCompletedAt(self, pending_future_task):
        pending_future_task.markCompleted()
        first = pending_future_task.lastCompletedAt
        pending_future_task.markCompleted()
        assert pending_future_task.lastCompletedAt >= first

    def test_marking_already_completed_task_stays_completed(self, completed_past_task):
        """Edge case: calling markCompleted on an already-completed task keeps COMPLETED status."""
        completed_past_task.markCompleted()
        assert completed_past_task.status == TaskStatus.COMPLETED

    def test_markCompleted_does_not_alter_other_fields(self, pending_future_task):
        """Edge case: markCompleted must not touch unrelated fields."""
        original_title = pending_future_task.title
        original_petId = pending_future_task.petId
        pending_future_task.markCompleted()
        assert pending_future_task.title == original_title
        assert pending_future_task.petId == original_petId


# ---------------------------------------------------------------------------
# PetTask.reschedule
# ---------------------------------------------------------------------------

class TestReschedule:
    def test_reschedule_dueAt_only(self, pending_future_task):
        new_due = datetime(2026, 6, 1, 9, 0)
        original_start = pending_future_task.startAt
        original_end = pending_future_task.endAt
        pending_future_task.reschedule(newDueAt=new_due)
        assert pending_future_task.dueAt == new_due
        assert pending_future_task.startAt == original_start
        assert pending_future_task.endAt == original_end

    def test_reschedule_startAt_only(self, pending_future_task):
        new_start = datetime(2026, 6, 1, 8, 0)
        pending_future_task.reschedule(newStartAt=new_start)
        assert pending_future_task.startAt == new_start

    def test_reschedule_endAt_only(self, pending_future_task):
        new_end = datetime(2026, 6, 1, 9, 0)
        pending_future_task.reschedule(newEndAt=new_end)
        assert pending_future_task.endAt == new_end

    def test_reschedule_all_fields(self, pending_future_task):
        new_due = datetime(2026, 7, 1, 10, 0)
        new_start = datetime(2026, 7, 1, 10, 0)
        new_end = datetime(2026, 7, 1, 10, 45)
        pending_future_task.reschedule(
            newDueAt=new_due, newStartAt=new_start, newEndAt=new_end
        )
        assert pending_future_task.dueAt == new_due
        assert pending_future_task.startAt == new_start
        assert pending_future_task.endAt == new_end

    def test_reschedule_no_args_is_noop(self, pending_future_task):
        original_due = pending_future_task.dueAt
        original_start = pending_future_task.startAt
        original_end = pending_future_task.endAt
        pending_future_task.reschedule()
        assert pending_future_task.dueAt == original_due
        assert pending_future_task.startAt == original_start
        assert pending_future_task.endAt == original_end

    def test_reschedule_to_past_datetime_is_accepted(self, pending_future_task):
        """Edge case: reschedule accepts past datetimes (no validation in this method)."""
        past = datetime(2020, 1, 1, 0, 0)
        pending_future_task.reschedule(newDueAt=past)
        assert pending_future_task.dueAt == past

    def test_reschedule_to_same_value_is_idempotent(self, pending_future_task):
        """Edge case: rescheduling to the current value leaves it unchanged."""
        original_due = pending_future_task.dueAt
        pending_future_task.reschedule(newDueAt=original_due)
        assert pending_future_task.dueAt == original_due


# ---------------------------------------------------------------------------
# PetTask.isOverdue
# ---------------------------------------------------------------------------

class TestIsOverdue:
    def test_pending_past_due_is_overdue(self, pending_past_task):
        assert pending_past_task.isOverdue() is True

    def test_pending_future_not_overdue(self, pending_future_task):
        assert pending_future_task.isOverdue() is False

    def test_completed_past_due_not_overdue(self, completed_past_task):
        assert completed_past_task.isOverdue() is False

    def test_completed_future_task_not_overdue(self):
        """Edge case: a COMPLETED task due in the future is not overdue."""
        task = make_task(due_offset_hours=48, status=TaskStatus.COMPLETED)
        assert task.isOverdue() is False

    def test_pending_task_far_in_past_is_overdue(self):
        """Edge case: task many days overdue is still detected correctly."""
        task = make_task(due_offset_hours=-720)  # 30 days ago
        assert task.isOverdue() is True

    def test_task_becomes_overdue_after_markCompleted_then_reschedule(self):
        """Edge case: after completion, even rescheduling to the past doesn't make it overdue."""
        task = make_task(due_offset_hours=1)
        task.markCompleted()
        task.reschedule(newDueAt=datetime.now() - timedelta(hours=5))
        assert task.isOverdue() is False


# ---------------------------------------------------------------------------
# Pet.addTask  (xfail until implemented)
# ---------------------------------------------------------------------------

class TestPetAddTask:
    @pytest.mark.xfail(reason="Pet.addTask not yet implemented", strict=True)
    def test_addTask_appends_to_tasks(self, pet):
        task = make_task()
        pet.addTask(task)
        assert task in pet.tasks

    @pytest.mark.xfail(reason="Pet.addTask not yet implemented", strict=True)
    def test_addTask_returns_true(self, pet):
        task = make_task()
        result = pet.addTask(task)
        assert result is True

    @pytest.mark.xfail(reason="Pet.addTask not yet implemented", strict=True)
    def test_addTask_duplicate_uid_not_added_twice(self, pet):
        """Edge case: adding the same task twice should not create a duplicate entry."""
        task = make_task(uid="task-dup")
        pet.addTask(task)
        pet.addTask(task)
        assert pet.tasks.count(task) == 1

    @pytest.mark.xfail(reason="Pet.addTask not yet implemented", strict=True)
    def test_addTask_for_wrong_pet_returns_false(self, pet):
        """Edge case: a task belonging to a different pet should be rejected."""
        foreign_task = make_task(uid="task-foreign", pet_uid="pet-999")
        result = pet.addTask(foreign_task)
        assert result is False


# ---------------------------------------------------------------------------
# Pet.updateTask  (xfail until implemented)
# ---------------------------------------------------------------------------

class TestPetUpdateTask:
    @pytest.mark.xfail(reason="Pet.updateTask not yet implemented", strict=True)
    def test_updateTask_changes_field(self, pet):
        task = make_task()
        pet.tasks.append(task)
        pet.updateTask(task.uid, {"title": "Evening Walk"})
        assert task.title == "Evening Walk"

    @pytest.mark.xfail(reason="Pet.updateTask not yet implemented", strict=True)
    def test_updateTask_unknown_id_returns_false(self, pet):
        result = pet.updateTask("nonexistent-uid", {"title": "x"})
        assert result is False

    @pytest.mark.xfail(reason="Pet.updateTask not yet implemented", strict=True)
    def test_updateTask_empty_updates_dict_is_noop(self, pet):
        """Edge case: passing an empty updates dict changes nothing but still returns True."""
        task = make_task()
        pet.tasks.append(task)
        original_title = task.title
        result = pet.updateTask(task.uid, {})
        assert result is True  # stub returns None → xfail until implemented
        assert task.title == original_title

    @pytest.mark.xfail(reason="Pet.updateTask not yet implemented", strict=True)
    def test_updateTask_multiple_fields_at_once(self, pet):
        """Edge case: multiple fields updated in a single call."""
        task = make_task()
        pet.tasks.append(task)
        pet.updateTask(task.uid, {"title": "Night Walk", "priority": "low"})
        assert task.title == "Night Walk"
        assert task.priority == "low"


# ---------------------------------------------------------------------------
# Pet.completeTask  (xfail until implemented)
# ---------------------------------------------------------------------------

class TestPetCompleteTask:
    @pytest.mark.xfail(reason="Pet.completeTask not yet implemented", strict=True)
    def test_completeTask_marks_task_completed(self, pet):
        task = make_task()
        pet.tasks.append(task)
        pet.completeTask(task.uid, datetime.now())
        assert task.status == TaskStatus.COMPLETED

    @pytest.mark.xfail(reason="Pet.completeTask not yet implemented", strict=True)
    def test_completeTask_unknown_id_returns_false(self, pet):
        result = pet.completeTask("nonexistent-uid", datetime.now())
        assert result is False

    @pytest.mark.xfail(reason="Pet.completeTask not yet implemented", strict=True)
    def test_completeTask_already_completed_returns_true(self, pet):
        """Edge case: completing an already-completed task is idempotent and returns True."""
        task = make_task(status=TaskStatus.COMPLETED)
        pet.tasks.append(task)
        result = pet.completeTask(task.uid, datetime.now())
        assert result is True
        assert task.status == TaskStatus.COMPLETED

    @pytest.mark.xfail(reason="Pet.completeTask not yet implemented", strict=True)
    def test_completeTask_records_provided_completedAt(self, pet):
        """Edge case: the completedAt timestamp passed in is stored on the task."""
        task = make_task()
        pet.tasks.append(task)
        completed_time = datetime(2026, 3, 13, 12, 0, 0)
        pet.completeTask(task.uid, completed_time)
        assert task.lastCompletedAt == completed_time


# ---------------------------------------------------------------------------
# Pet.getDueTasks  (xfail until implemented)
# ---------------------------------------------------------------------------

class TestPetGetDueTasks:
    @pytest.mark.xfail(reason="Pet.getDueTasks not yet implemented", strict=True)
    def test_getDueTasks_returns_tasks_in_window(self, pet):
        now = datetime.now()
        inside = make_task("t1", due_offset_hours=2)
        outside = make_task("t2", due_offset_hours=48)
        pet.tasks.extend([inside, outside])
        result = pet.getDueTasks(now, now + timedelta(hours=24))
        assert inside in result
        assert outside not in result

    @pytest.mark.xfail(reason="Pet.getDueTasks not yet implemented", strict=True)
    def test_getDueTasks_empty_when_no_tasks(self, pet):
        now = datetime.now()
        result = pet.getDueTasks(now, now + timedelta(hours=24))
        assert result == []

    @pytest.mark.xfail(reason="Pet.getDueTasks not yet implemented", strict=True)
    def test_getDueTasks_task_exactly_at_window_start_is_included(self, pet):
        """Edge case: a task due exactly at windowStart (inclusive boundary)."""
        now = datetime.now()
        boundary_task = make_task("t-boundary", due_offset_hours=0)
        boundary_task.dueAt = now  # pin to exact boundary
        pet.tasks.append(boundary_task)
        result = pet.getDueTasks(now, now + timedelta(hours=24))
        assert boundary_task in result

    @pytest.mark.xfail(reason="Pet.getDueTasks not yet implemented", strict=True)
    def test_getDueTasks_window_with_all_tasks_overdue(self, pet):
        """Edge case: window entirely in the past returns no tasks (none are due)."""
        past_start = datetime.now() - timedelta(hours=10)
        past_end = datetime.now() - timedelta(hours=5)
        future_task = make_task("t-future", due_offset_hours=2)
        pet.tasks.append(future_task)
        result = pet.getDueTasks(past_start, past_end)
        assert future_task not in result


# ---------------------------------------------------------------------------
# Pet.calculateAge  (xfail until implemented)
# ---------------------------------------------------------------------------

class TestPetCalculateAge:
    @pytest.mark.xfail(reason="Pet.calculateAge not yet implemented", strict=True)
    def test_calculateAge_correct(self, pet):
        # Simba birthDate is 2020-05-15; on 2026-05-15 he turns 6
        assert pet.calculateAge(date(2026, 5, 15)) == 6

    @pytest.mark.xfail(reason="Pet.calculateAge not yet implemented", strict=True)
    def test_calculateAge_before_birthday_in_year(self, pet):
        # Before May 15 in 2026 → still 5
        assert pet.calculateAge(date(2026, 3, 1)) == 5

    @pytest.mark.xfail(reason="Pet.calculateAge not yet implemented", strict=True)
    def test_calculateAge_on_birth_date_is_zero(self, pet):
        """Edge case: age on the exact birth date should be 0."""
        assert pet.calculateAge(pet.birthDate) == 0

    @pytest.mark.xfail(reason="Pet.calculateAge not yet implemented", strict=True)
    def test_calculateAge_day_before_birthday_does_not_increment(self, pet):
        """Edge case: one day before the birthday should not add a year."""
        # One day before the 6th birthday
        assert pet.calculateAge(date(2026, 5, 14)) == 5

    @pytest.mark.xfail(reason="Pet.calculateAge not yet implemented", strict=True)
    def test_calculateAge_leap_year_birthday(self):
        """Edge case: pet born on Feb 29 — age calculation on a non-leap year."""
        leap_pet = Pet(
            uid="pet-leap",
            name="Leapy",
            animalProfileId="ap-001",
            birthDate=date(2020, 2, 29),
            weightKg=3.0,
        )
        # 2026 is not a leap year; use Mar 1 as the effective birthday
        assert leap_pet.calculateAge(date(2026, 3, 1)) == 6
