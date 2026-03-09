# Pawpal Spec

## Main Objects

User

- UID
- Name
- Address
- Phone Number
- Pets (fk)
- Tasks (fk)

Pet

- UID
- Name
- Animal (fk)
- Age

Animal

- UID
- Type
- Breed

Task

- UID
- name
- description
- associated_pet (fk)
- type
- duration
- start_date
- end_date
- start_time
- end_time
- edit()
- add()
- delete()

## Note

- User should be able to add and edit tasks
- Tasks schedulinng should not overlap
