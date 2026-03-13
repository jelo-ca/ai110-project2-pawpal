from pawpal_system import Animal, Pet, Task, User, Scheduler 

Ben = User(
    uid="user123",
    name="Ben",
    email="ben@example.com",
    address="123 Main St",
    phoneNumber="555-1234",
    timezone="America/New_York"
)

Simba = Pet(
    uid="pet123",
    name="Simba",
    animal=Animal(uid="animal123", name="Dog"),
    age=3,
    birthDate=date(2020, 5, 15),
    weight=15.5,
)

Kayne = Pet(
    uid="pet124",
    name="Kayne",
    animal=Animal(uid="animal124", name="Cat"),
    age=2,
    birthDate=date(2021, 8, 20),
    weight=10.0,

)

