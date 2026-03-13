# PawPal+ Project Reflection

## 1. System Design

**i. Core Actions**

- Input owner + pet info
- Add/edit tasks
  - duration
  - priority
  - time availability/ preference
- View daily schedule

**a. Initial design**

My Initial Design involved the minimum objects required to interact with eadch other. I didn't add potential interfaces that would connect each class. I used a relational DB model to understand how the data needs to be setup.

### Initial Classes/Attributes

Holds the tasks and pets classes
User

- UID
- Name
- Address
- Phone Number
- Pets (fk)
- Tasks (fk)

Holds an animal class
Pet

- UID
- Name
- Animal (fk)
- Age

Animal Type and Breed
Animal

- UID
- Type
- Breed

Holds data about tasks including schedule, duration, date, and associated pets
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

**b. Design changes**

A lot of changes occured. Many getters and setters were set by the AI that I knew about yet didn't think of in the initial design. More details about pets and animals were also added which I found useful in the later stages of the system (especially with implementing it to UI elements). Tasks also gained attributes like isRecurring which opened possibilitites for calendar integration.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
