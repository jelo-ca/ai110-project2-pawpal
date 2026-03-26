# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling System

The PawPal+ app now includes a smarter scheduling system with the following new features:

- **Priority-Based Scheduling**: Tasks are dynamically scheduled based on their priority levels (high, medium, low) to ensure critical tasks are completed first.
- **Conflict Resolution**: Automatically detects and resolves overlapping tasks for the same pet, rescheduling lower-priority tasks as needed.
- **Recurring Task Optimization**: Recurring tasks are precomputed and cached for efficient scheduling, reducing runtime overhead.
- **Enhanced Reminder System**: Sends reminders for tasks using customizable methods (e.g., SMS, email, app notifications).
- **Analytics and Insights**: Tracks task completion rates and provides insights to help users optimize their pet care routines.
- **Improved Data Storage**: Tasks are stored in a scalable database for faster retrieval and better performance as the app grows.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

To ensure the reliability of the PawPal+ system, we use `pytest` for testing. Run the following command to execute the test suite:

```bash
pytest
```

### Reliability Confidence Level

I rate the reliability of the system at **4/5 stars**, based on the robustness of the implemented features and the comprehensive test coverage.
