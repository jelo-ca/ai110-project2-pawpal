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

Another realization I had was the designation between a task app and a "Pet" task app. I was initially designing a task app that could link pets to tasks you assign but from reading a little more, I realized that each task SHOULD be related to a pet. This change caused a change where the pet now hold a list of task rather than the other way around.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The constraints for the scheduler consisted of Time Windows, Task Status, Priority, and Recurrence. I chose these as the app's goal is to organize tasks to help a user be more efficient at executing them. I believe these are the minimum information needed to see, know, and do tasks while also having them as sortable attributes for the UI.

**b. Tradeoffs**

Overlapped tasks are only seen per pet. Cross pet overlap is checked only by their start time. Its not much of a hard fix but it does save effort on checking each pets task interval to ensure that another pet's new task wont conflict. Another solution could be added where a collection of times could be used and a simple start end algorithm could be implemented. This will probably be the next improvement for this feature.

---

## 3. AI Collaboration

**a. How you used AI**

It was extremely useful in generating code for algorithms I had prior knowledge on. Python's sort is the base level of this but to ask it and describe how the algorithm I had in mind works was were it excelled at its job. Asking the agents to refactor huge chunks of code also showed its usefulness in today's engineering workflow.

The prompts I used usually involved the solution itself to the problem. If I didnt have the solution, I would ask how things worked and go back and forth on the directions I could take finding a solution.

**b. Judgment and verification**

I declined times where it created tests using unittest rather than pytest. I adjusted project structure multiple times as well during development and it sometimes had a hard time locating new file locations causing it to create new files. I was also careful with its implementation of class methods as some attributes were built to be strings initially (by AI) but I decided to change them to ENUMs instead for better readability.

---

## 4. Testing and Verification

**a. What you tested**

Task addition, completion, recurring, conflict detection. These are the main interactable features used in the App. The backend, data initialization, could also be tested but those are simple "if put in this, out put this". I focused on the algorithmic methods that could cause funky behavior if one line is out of place.

**b. Confidence**

I'm pretty confident in the ability of the app and all its features. The only thing I didn't test for is for when a reoccuring task is made BUT a different task is set on the time its planned to reoccur. This could be fixed by automatically adjusting it of offsetting it when it happens. But other than that, the main features work as intended and tested.

---

## 5. Reflection

**a. What went well**

The whole system itself. Its a simple and working system made e2e. Its always satisfying to finish a project made from almost scratch.

**b. What you would improve**

Probably the techstack. I think this project has great potential as a useful app in the real world. Upgrading its techstack to be more deployable could potentially launch it as a proper app with users.

**c. Key takeaway**

Planning is the most important step, 2nd to that is adjusting when the plan fails. The initial plan was too simple and more and more features started adding up BUT the initial plan was the foundation of everything that was made. Its better to start that journey with a rough map rather than walking towards a random direction.
