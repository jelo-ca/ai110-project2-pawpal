from datetime import date, datetime

from pawpal_system import AnimalProfile, Pet, PetTask, PetTaskScheduler, User


def InitializeMockSystem() -> None:
    dog_profile = AnimalProfile(
        uid="ap-001",
        species="Dog",
        breed="Golden Retriever",
        lifeStage="Adult",
        defaultCareGuidelines="Daily walks, consistent feeding schedule.",
    )

    cat_profile = AnimalProfile(
        uid="ap-002",
        species="Cat",
        breed="Siamese",
        lifeStage="Young Adult",
        defaultCareGuidelines="Litter cleaning and enrichment play.",
    )

    simba_task = PetTask(
        uid="task-001",
        petId="pet-001",
        title="Morning Walk",
        careType="Exercise",
        instructions="30 minute neighborhood walk.",
        dueAt=datetime(2026, 3, 14, 8, 0),
        startAt=datetime(2026, 3, 14, 8, 0),
        endAt=datetime(2026, 3, 14, 8, 30),
        estimatedMinutes=30,
        status="pending",
        priority="high",
        reminderMinutesBefore=15,
        isRecurring=True,
        recurrenceRule="daily",
        nextDueAt=datetime(2026, 3, 14, 8, 0),
    )

    kayne_task = PetTask(
        uid="task-002",
        petId="pet-002",
        title="Evening Feeding",
        careType="Feeding",
        instructions="Serve measured dry food at 6 PM.",
        dueAt=datetime(2026, 3, 14, 18, 0),
        startAt=datetime(2026, 3, 14, 18, 0),
        endAt=datetime(2026, 3, 14, 18, 10),
        estimatedMinutes=10,
        status="pending",
        priority="medium",
        reminderMinutesBefore=10,
        isRecurring=True,
        recurrenceRule="daily",
        nextDueAt=datetime(2026, 3, 14, 18, 0),
    )

    simba = Pet(
        uid="pet-001",
        name="Simba",
        animalProfileId=dog_profile.uid,
        birthDate=date(2020, 5, 15),
        weightKg=15.5,
        medicalNotes="Mild seasonal allergies.",
        tasks=[simba_task],
    )

    kayne = Pet(
        uid="pet-002",
        name="Kayne",
        animalProfileId=cat_profile.uid,
        birthDate=date(2021, 8, 20),
        weightKg=4.5,
        medicalNotes="No known medical issues.",
        tasks=[kayne_task],
    )

    bey = User(
        uid="user-001",
        name="Bey",
        phoneNumber="555-1234",
        timezone="America/New_York",
        pets=[simba, kayne],
    )

    scheduler = PetTaskScheduler()
    
    print(bey)
    print(simba)
    print(kayne)



def main() -> None:
    InitializeMockSystem()
    # Additional code to demonstrate functionality can be added here.
    pass

if __name__ == "__main__":
    main()

